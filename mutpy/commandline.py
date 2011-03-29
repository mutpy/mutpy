import argparse
from mutpy import mutation_controller

VERSION = 0.1

def main(argv):
	parser = build_parser()
	args = parser.parse_args()
	controller = mutation_controller.MutationController(args.target, args.test, None)
	controller.run()

def build_parser():
	parser = argparse.ArgumentParser(description='Mutation testing tool for Python 3.x source code.')
	parser.add_argument('--version', '-v', action='version', version='%(prog)s {}'.format(VERSION))
	parser.add_argument('target', help='target module to mutate')
	parser.add_argument('test', nargs='+', help='module with unit test')
	return parser
