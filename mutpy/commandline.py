import argparse

from mutpy import controller, view

VERSION = 0.1

def main(argv):
    parser = build_parser()
    args = parser.parse_args()
    views = create_views(args)
    mutation_controller = controller.MutationController(args, views)
    mutation_controller.run()

def create_views(args):
    views = []
    
    if args.quiet:
        views.append(view.QuietTextMutationView(args))
    else:
        views.append(view.TextMutationView(args))
    
    if args.raport is not None:
        views.append(view.YAMLRaportMutationView(args.raport))
    
    return views
        
def build_parser():
    DEF_TIMEOUT_FACTOR = 5
    parser = argparse.ArgumentParser(description='Mutation testing tool for Python 3.x source code.')
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
