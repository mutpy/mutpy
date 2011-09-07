import argparse

from mutpy import controller, views, operators, experiments
import sys

VERSION = 0.2

def main(argv):
    parser = build_parser()
    run_mutpy(parser)


def build_parser():
    DEF_TIMEOUT_FACTOR = 5
    parser = argparse.ArgumentParser(description='Mutation testing tool for Python 3.x source code. ' +
                                     'You can save arguments in file and run mutpy with @FILE.',
                                     fromfile_prefix_chars='@')
    parser.add_argument('--version', '-v', action='version', version='%(prog)s {}'.format(VERSION))
    parser.add_argument('--target', '-t', type=str, nargs='+', help='target module or file to mutate')
    parser.add_argument('--unit-test', '-u', type=str, nargs='+', help='target module, test class, test method or file with unit test')
    parser.add_argument('--report', '-r', type=str, help='generate YAML report', metavar='REPORT_FILE')
    parser.add_argument('--timeout-factor', '-f', type=float, default=DEF_TIMEOUT_FACTOR,
                        help='test for mutants max timeout factor (default {})'.format(DEF_TIMEOUT_FACTOR))
    parser.add_argument('--show-mutants', '-m', action='store_true', help='show mutants')
    parser.add_argument('--quiet', '-q', action='store_true', help='quiet mode')
    parser.add_argument('--debug', action='store_true', help='dubug mode')
    parser.add_argument('--colored-output', '-c', action='store_true', help='try print colored output')
    parser.add_argument('--disable-stdout', '-d', action='store_true', help='try disable stdout during mutation (this option can damage your tests if you interact with sys.stdout)')
    parser.add_argument('--experimental-operators', '-e', action='store_true', help='use experimental operators')
    parser.add_argument('--operator', '-o', type=str, nargs='+', help='use only selected operators (use -l to show all operators)', metavar='OPERATOR')
    parser.add_argument('--list-operators', '-l', action='store_true', help='list available operators')
    return parser


def run_mutpy(parser):
    cfg = parser.parse_args()
    if cfg.list_operators:
        list_operators()
    elif cfg.target and cfg.unit_test:
        mutation_controller = build_controller(cfg)
        mutation_controller.run()
    else:
        parser.print_usage()


def build_controller(cfg):
    views = build_views(cfg)
    mutant_generator = build_mutator(cfg)
    loader = controller.ModulesLoader(cfg.target, cfg.unit_test)
    return controller.MutationController(loader, views, mutant_generator, cfg.timeout_factor, cfg.disable_stdout, cfg.debug)


def build_mutator(cfg):
    operators_set = set()

    if cfg.experimental_operators:
        operators_set.update(experiments.all_operators)

    if cfg.operator:
        name_to_operator = build_name_to_operator_map()
        for operator in cfg.operator:
            try:
                operators_set.add(name_to_operator[operator])
            except KeyError:
                print('Unsupported operator {}! Use -l to show all operators.'.format(operator))
                sys.exit(-1)
    else:
        operators_set.update(operators.all_operators)

    return controller.Mutator(operators_set)


def build_name_to_operator_map():
    result = {}
    for operator in operators.all_operators + experiments.all_operators:
        result[operator.name()] = operator
        result[operator.long_name()] = operator
    return result


def build_views(cfg):
    views_list = []

    if cfg.quiet:
        views_list.append(views.QuietTextView(cfg.colored_output))
    else:
        views_list.append(views.TextView(cfg.colored_output, cfg.show_mutants))

    if cfg.report:
        views_list.append(views.YAMLRaportView(cfg.report))

    return views_list


def list_operators():
    print('Standard mutation operators:')
    for operator in operators.all_operators:
        print(' - {:3} - {}'.format(operator.name(), operator.long_name()))
    print('Experimental mutation operators:')
    for operator in experiments.all_operators:
        print(' - {:3} - {}'.format(operator.name(), operator.long_name()))
