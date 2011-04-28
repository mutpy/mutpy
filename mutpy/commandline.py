import argparse
from mutpy import controller, view

VERSION = 0.1

def main(argv):
    parser = build_parser()
    args = parser.parse_args()
    mutation_controller = controller.MutationController(args, view.TextMutationView())
    mutation_controller.run()

def build_parser():
    DEF_TIMEOUT_FACTOR = 5
    parser = argparse.ArgumentParser(description='Mutation testing tool for Python 3.x source code.')
    parser.add_argument('--version', '-v', action='version', version='%(prog)s {}'.format(VERSION))
    parser.add_argument('target', help='target module to mutate')
    parser.add_argument('test', nargs='+', help='module with unit test')
    parser.add_argument('--timeout-factor', '-t', type=float, default=DEF_TIMEOUT_FACTOR, help='test for mutants max timeout factor (default {})'.format(DEF_TIMEOUT_FACTOR))
    parser.add_argument('--show-mutants', '-m', action='store_true', help='show mutants')
    parser.add_argument('--debug', '-d', action='store_true', help='debug mode (print more info)')
    return parser
