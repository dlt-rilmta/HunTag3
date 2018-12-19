#!/usr/bin/python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import sys


def process_header(stream, source_fields, target_fields):
    fields = []
    if source_fields:
        fields = next(stream).strip().split('\t')                           # Read header to fields
        if not source_fields.issubset(set(fields)):
            raise NameError('Input does not have the required field names ({0}). The following field names found: {1}'.
                            format(sorted(source_fields), fields))
    fields.extend(target_fields)                                    # Add target fields
    field_names = {name: i for i, name in enumerate(fields)}        # Decode field names
    field_names.update({i: name for i, name in enumerate(fields)})  # Both ways...
    header = '{0}\n'.format('\t'.join(fields))
    return header, field_names


# Only This method is public...
def process(stream, internal_app):
    header, field_names = process_header(stream, internal_app.source_fields, internal_app.target_fields)
    yield header

    # Like binding names to indices...
    field_values = internal_app.prepare_fields(field_names)

    print('featurizing sentences...', end='', file=sys.stderr, flush=True)
    sen_count = 0
    for sen_count, (sen, comment) in enumerate(sentence_iterator(stream)):
        sen_count += 1
        if comment:
            yield '{0}\n'.format(comment)

        yield from ('{0}\n'.format('\t'.join(tok)) for tok in internal_app.process_sentence(sen, field_values))
        yield '\n'

        if sen_count % 1000 == 0:
            print('{0}...'.format(sen_count), end='', file=sys.stderr, flush=True)
    print('{0}...done'.format(sen_count), file=sys.stderr, flush=True)


def sentence_iterator(input_stream):
    curr_sen = []
    curr_comment = None
    for line in input_stream:
        line = line.strip()
        # Blank line handling
        if len(line) == 0:
            if curr_sen:  # End of sentence
                yield curr_sen, curr_comment
                curr_sen = []
                curr_comment = None
            else:  # WARNING: Multiple blank line
                print('WARNING: wrong formatted sentences, only one blank line allowed!', file=sys.stderr, flush=True)
        else:
            curr_sen.append(line.split('\t'))
    if curr_sen:
        print('WARNING: No blank line before EOF!', file=sys.stderr, flush=True)
        yield curr_sen, curr_comment
