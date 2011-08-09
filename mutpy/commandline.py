import argparse

from mutpy import controller, views, operators, experiments

VERSION = 0.1

def main(argv):
    parser = build_parser()
    cfg = parser.parse_args()
    mutation_controller = build_controller(cfg)
    mutation_controller.run()

def build_parser():
    DEF_TIMEOUT_FACTOR = 5
    parser = argparse.ArgumentParser(description='Mutation testing tool for Python 3.x source code. ' +
                                     'You can save arguments in file and run mutpy with @FILE.',
                                     fromfile_prefix_chars='@')
    parser.add_argument('--version', '-v', action='version', version='%(prog)s {}'.format(VERSION))
    parser.add_argument('--targets', '-t', type=str, nargs='+', help='targets module to mutate', required=True)
    parser.add_argument('--unit-test', '-u', type=str, nargs='+', help='module with unit test', required=True)
    parser.add_argument('--report', '-r', type=str, help='generate YAML report', metavar='RAPORT_FILE')
    parser.add_argument('--timeout-factor', '-f', type=float, default=DEF_TIMEOUT_FACTOR,
                        help='test for mutants max timeout factor (default {})'.format(DEF_TIMEOUT_FACTOR))
    parser.add_argument('--show-mutants', '-m', action='store_true', help='show mutants')
    parser.add_argument('--quiet', '-q', action='store_true', help='quiet mode')
    parser.add_argument('--debug', action='store_true', help='dubug mode')
    parser.add_argument('--colored-output', '-c', action='store_true', help='try print colored output')
    parser.add_argument('--disable-stdout', '-d', action='store_true', help='try disable stdout during mutation (this option can damage your tests if you interact with sys.stdout)')
    parser.add_argument('--experimental-operators', '-e', action='store_true', help='use only experimental operators')
    return parser

def build_controller(cfg):
    views = build_views(cfg)
    mutant_generator = build_mutator(cfg)
    loader = controller.ModulesLoader(cfg.targets, cfg.unit_test)
    return controller.MutationController(loader, views, mutant_generator, cfg.timeout_factor, cfg.disable_stdout, cfg.debug)

def build_mutator(cfg):
    if cfg.experimental_operators:
        operators_set = experiments.all_operators
    else:
        operators_set = operators.all_operators

    return controller.Mutator(operators_set)

def build_views(cfg):
    views_list = []

    if cfg.quiet:
        views_list.append(views.QuietTextView(cfg.colored_output))
    else:
        views_list.append(views.TextView(cfg.colored_output, cfg.show_mutants))

    if cfg.report is not None:
        views_list.append(views.YAMLRaportView(cfg.report))

    return views_list
