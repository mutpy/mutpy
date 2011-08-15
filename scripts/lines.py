#! /usr/bin/env python

import sys
import tokenize
from _pyio import StringIO

def statistics(src):
    f = StringIO(src)
    result = 0
    classes = 0
    last_token = None
    for tok in tokenize.generate_tokens(f.readline):
        t_type = tok[0]
        if t_type == tokenize.COMMENT:
            result += 1
        elif t_type == tokenize.STRING:
            if last_token is None or last_token[0] in [tokenize.INDENT]:
                result += 1 + tok.end[0] - tok.start[0]
        elif t_type == tokenize.NAME and tok.string == 'class':
            classes += 1
        last_token = tok
    return result, classes

if len(sys.argv) < 2:
    sys.exit(-1)

total_lines = 0
total_uncomented = 0
total_classes = 0
files = 0

for file_name in sys.argv[1:]:
    file = open(file_name, 'r')
    files += 1
    comments, classes = statistics(file.read())
    file.seek(0)
    lines = len(file.readlines())
    uncomented = lines - comments
    print('{}  lines: {}  uncomented: {}  classes: {}'.format(file_name, lines, uncomented, classes))
    total_lines += lines
    total_uncomented += uncomented
    total_classes += classes

print('files: {}  total lines: {}  total uncomented: {}  total_classes: {}'.format(files, total_lines, total_uncomented, total_classes))
