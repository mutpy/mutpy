import argparse
from mutpy import mutator

VERSION = 0.1

def main(argv):
	parser = build_parser()
	args = parser.parse_args()
	main_mutator = mutator.Mutator(args.target, args.test)
	main_mutator.run()

def build_parser():
	parser = argparse.ArgumentParser(description='Mutation testing tool for Python 3.x source code.')
	parser.add_argument('--version', '-v', action='version', version='%(prog)s {}'.format(VERSION))
	parser.add_argument('target', help='target module file to mutate')
	parser.add_argument('test', nargs='+', help='unit test file')
	return parser
