#! /usr/bin/env python3.2

import yaml
from collections import defaultdict
import sys

COL_SEP = ' & '
END_ROW = r' \\ '
HLINE = r'\hline'

def pp(x):
    return '{:.1f}\%'.format(x)

def pf(x):
    return '{:.2f}'.format(x)

def get_row(items):
    return COL_SEP.join(map(str, items)) + END_ROW

def score(killed, timout, _all):
    return ((100 * (killed + timeout)) / _all) if _all else 0

class Table():

    def __init__(self):
        self.rows = []

    def append_row(self, items, hline_before=False, hline_after=True):
        if hline_before:
            self.rows.append(HLINE)
        row = self.get_row(items)
        row += END_ROW
        if hline_after:
            row += HLINE
        self.rows.append(row)

    def print_table(self):
        line_len = 50
        print('-' * line_len)
        print()
        print('\n'.join(self.rows))
        print()
        print('-' * line_len)

    def sort_rows(self):
        self.rows.sort()

    @staticmethod
    def get_row(items):
        return COL_SEP.join(map(str, items))

operators_dict = defaultdict(lambda:defaultdict(int))

filename = sys.argv[1]
file = open(filename , 'r')
result = yaml.load(file)

mutation_count = 0

for mutation in result['mutations']:
    operators_dict[mutation['operator']][mutation['status']] += 1
    mutation_count += 1

all_killed = 0
all_survived = 0
all_incompetent = 0
all_timeout = 0

stats_table = Table()
first_table = Table()
second_table = Table()

for operator in operators_dict:
    operator_stats = operators_dict[operator]
    survived = operator_stats['survived']
    killed = operator_stats['killed']
    incompetent = operator_stats['incompetent']
    timeout = operator_stats['timeout']
    _all = survived + killed + incompetent + timeout
    real_all = _all - incompetent
    all_killed += killed
    all_survived += survived
    all_incompetent += incompetent
    all_timeout += timeout
    first_table.append_row([operator, _all, incompetent, real_all])
    first_score = score(killed, timeout, _all)
    second_score = score(killed, timeout, real_all)
    second_table.append_row([operator, killed, timeout, survived, pp(first_score), pp(second_score)])

first_table.sort_rows()
first_table.append_row(['Suma', mutation_count, all_incompetent, mutation_count - all_incompetent], hline_before=True, hline_after=False)
first_table.print_table()

second_table.sort_rows()
first_score = score(all_killed, all_timeout, mutation_count)
second_score = score(all_killed, all_timeout, mutation_count - all_incompetent)
second_table.append_row(['Suma', all_killed, all_timeout, all_survived, pp(first_score), pp(second_score)], hline_before=True, hline_after=False)
second_table.print_table()

stats_table.append_row([pf(result['time']), mutation_count, all_survived, all_incompetent, all_killed, all_timeout, pp(second_score)])
stats_table.print_table()
