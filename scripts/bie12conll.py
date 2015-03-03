#!/usr/bin/python -u
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import sys
import optfunc


def log(s):
    sys.stderr.write('{0}\n'.format(s))


def transform(sConst, c, dontDoBIE1ToBI=False, dontDoNbarToNP=False, dontDoNplusToNbar=False):
    s = sConst
    #log(s)
    if s != 'O':
        if s[1] != '-':
            log('Malformed tag: {0}\nLine: {1}'.format(s, c))
            sys.exit(1)

        if not dontDoNplusToNbar:
            s = s.strip('+')

        if not dontDoNbarToNP:
            a = s.split('_')
            if len(a) != 2:
                log('Malformed tag: {0}\nLine: {1}'.format(s, c))
                sys.exit(1)
            s = '{0}P'.format(a[0])
        if not dontDoBIE1ToBI:
            if s[0] == '1':
                s = 'B{0}'.format(s[1:])
            if s[0] == 'E':
                s = 'I{0}'.format(s[1:])
    return s


def main(dontDoBIE1ToBI=False, dontDoNbarToNP=False, dontDoNplusToNbar=False, fields='-2,-1'):
    fieldList = map(int, fields.split(','))
    lengthSet = set()
    line = sys.stdin.readline()
    c = 0
    while line:
        c += 1
        a = line.strip().split()
        if len(a) == 0:
            print
        else:
            assert len(a) >= 2
            lengthSet.add(len(a))
            if len(lengthSet) > 1:
                log('Column number differs from those of previous lines:')
                log(line)
                sys.exit(1)
            for ind in fieldList:
                a[ind] = transform(a[ind], c, dontDoBIE1ToBI, dontDoNbarToNP, dontDoNplusToNbar)
            print '\t'.join(a)
        line = sys.stdin.readline()

if __name__ == '__main__':
    optfunc.run(main)

#    gsub('1-', 'B-', $3)
#    gsub('1-', 'B-', $4)
#    gsub('E-', 'I-', $3)
#    gsub('E-', 'I-', $4)
