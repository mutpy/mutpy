import argparse

def build_parser():
	DEF_TIMEOUT_FACTOR = 5
	parser = argparse.ArgumentParser(description='This is test for parsing command line ',fromfile_prefix_chars='@')
	parser.add_argument('--type-check', action='store_true',help='tries to keep track of types and prevents some mutants incompetent from TypeError')
	return parser
	
parser = build_parser()
cfg = parser.parse_args()
print(cfg.__dict__)