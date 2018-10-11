#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import sys
from sklearn.externals import joblib
from scipy.sparse import csr_matrix

from huntag.tools import featurize_sentence, use_featurized_sentence, BookKeeper, bind_features_to_indices


class Tagger:
    def __init__(self, features, trans_model, options):
        self.features = features
        self.tag_field_name = options['tag_field']
        self.tag_field = options['field_names'][options['tag_field']]
        self.field_names = options['field_names']
        self.target_fields = [options['tag_field']]
        self._data_sizes = options['data_sizes']
        self._trans_probs = trans_model
        self.use_header = options['use_header']

        # Set functions according to task...
        if options.get('inp_featurized', False):
            self._featurize_sentence_fun = use_featurized_sentence
            self._format_output = self._add_tagging_featurized
            self._tag_fun = self.tag_by_feat_number
        else:
            self._featurize_sentence_fun = featurize_sentence
            if options.get('task') == 'tag-featurize':  # print features
                self._format_output = self._feat_counter.no_to_name
                self._tag_fun = self._print_features
            else:  # tag sentences
                self._format_output = self._add_tagging_normal
                self._tag_fun = self.tag_by_feat_number

        print('loading observation model...', end='', file=sys.stderr, flush=True)
        self._model = joblib.load('{0}'.format(options['model_filename']))
        self._feat_counter = BookKeeper(options['featcounter_filename'])
        self._label_counter = BookKeeper(options['labelcounter_filename'])
        print('done', file=sys.stderr, flush=True)

    def _get_tag_probs_by_pos(self, feat_numbers):
        rows, cols, data = [], [], []
        for rownum, featNumberSet in enumerate(feat_numbers):
            for featNum in featNumberSet:
                rows.append(rownum)
                cols.append(featNum)
                data.append(1)
        contexts = csr_matrix((data, (rows, cols)), shape=(len(feat_numbers), self._feat_counter.num_of_names()),
                              dtype=self._data_sizes['data_np'])
        tagprobs_by_pos = [{self._label_counter.no_to_name[i]: prob for i, prob in enumerate(prob_dist)}
                           for prob_dist in self._model.predict_proba(contexts)]
        return tagprobs_by_pos

    @staticmethod
    def _add_tagging_featurized(_, best_tagging, __):
        return [[label] for label in best_tagging]

    @staticmethod
    def _add_tagging_normal(sent, best_tagging, tag_index):
        for tok, label in zip(sent, best_tagging):
            tok.insert(tag_index, label)
        return sent

    def tag_by_feat_number(self, sen, feat_numbers, add_tagging, tag_index):
        best_tagging = self._trans_probs.tag_sent(self._get_tag_probs_by_pos(feat_numbers))
        return add_tagging(sen, best_tagging, tag_index)  # Add tagging to sentence

    @staticmethod
    def _print_features(_, __, feat_numbers, featno_to_name, ___):
        return [[featno_to_name[featNum].replace(':', 'colon') for featNum in featNumberSet]
                for featNumberSet in feat_numbers]

    def prepare_fields(self, field_names):
        return bind_features_to_indices(self.features, field_names)

    def process_sentence(self, sen, features_bound_to_column_ids):
        sen_feats = self._featurize_sentence_fun(sen, features_bound_to_column_ids)
        get_no_tag = self._feat_counter.get_no_tag
        # Get Sentence Features translated to numbers and contexts in two steps
        feat_numbers = [{get_no_tag(feat) for feat in feats if get_no_tag(feat) is not None} for feats in sen_feats]
        yield self._tag_fun(sen, feat_numbers, self._format_output, self.tag_field)

    def print_weights(self, n=100, output_stream=sys.stdout):
        coefs = self._model.coef_
        labelno_to_name = self._label_counter.no_to_name
        featno_to_name = self._feat_counter.no_to_name
        sorted_feats = sorted(featno_to_name.items())
        for i, label in sorted(labelno_to_name.items()):
            columns = ['{0}:{1}'.format(w, feat) for w, (no, feat) in sorted(zip(coefs[i, :], sorted_feats),
                                                                             reverse=True)]
            print('{0}\t{1}'.format(label, '\t'.join(columns[:n])), file=output_stream)  # Best
            # Worst -> Negative correlation
            print('{0}\t{1}'.format(label, '\t'.join(sorted(columns[-n:], reverse=True))), file=output_stream)
