import argparse

from mutpy import controller, view, operator

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
    parser.add_argument('target', help='target module to mutate')
    parser.add_argument('test', nargs='+', help='module with unit test')
    parser.add_argument('--raport', '-r', type=str, help='generate YAML raport', metavar='RAPORT_FILE')
    parser.add_argument('--timeout-factor', '-t', type=float, default=DEF_TIMEOUT_FACTOR,
                        help='test for mutants max timeout factor (default {})'.format(DEF_TIMEOUT_FACTOR))
    parser.add_argument('--show-mutants', '-m', action='store_true', help='show mutants')
    parser.add_argument('--quiet', '-q', action='store_true', help='quiet mode')
    parser.add_argument('--colored-output', '-c', action='store_true', help='try print colored output')
    return parser

def build_controller(cfg):
    views = build_views(cfg)
    mutant_generator = build_mutator(cfg)
    loader = controller.ModulesLoader(cfg.target, cfg.test)
    return controller.MutationController(loader, views, mutant_generator, cfg.timeout_factor)

def build_mutator(cfg):
    operators = {operator.ArithmeticOperatorReplacement,
                     operator.ConstantReplacement,
                     operator.StatementDeletion,
                     operator.ConditionNegation,
                     operator.SliceIndexReplace,
                     operator.BinaryOperatorReplacement,
                     operator.LogicaOperatorReplacement,
                     operator.ConditionalOperatorReplacement,
                     operator.ExceptionHandleDeletion,
                     operator.MembershipTestReplacement,
                     operator.OneIterationLoop,
                     operator.ZeroIterationLoop,
                     operator.ReverseIterationLoop,
                     operator.UnaryOperatorReplacement,
                     operator.SelfWordDeletion}

    return controller.Mutator(operators)
    
def build_views(cfg):
    views = []
    
    if cfg.quiet:
        views.append(view.QuietTextView(cfg))
    else:
        views.append(view.TextView(cfg))
    
    if cfg.raport is not None:
        views.append(view.YAMLRaportView(cfg.raport))
    
    return views
