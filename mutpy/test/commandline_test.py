import unittest
from mutpy import commandline


class CommandLineTest(unittest.TestCase):

    def test_build_mutator_with_disable_operator(self):
        parser = commandline.build_parser()
        default_mutator = commandline.build_mutator(parser.parse_args([]))

        mutator = commandline.build_mutator(
            parser.parse_args(['--disable-operator', 'AOR']))
        self.assertEqual(len(default_mutator.operators) - 1,
                         len(mutator.operators))

    def test_build_mutator_with_operator(self):
        parser = commandline.build_parser()
        mutator = commandline.build_mutator(
            parser.parse_args(['--operator', 'AOR']))
        self.assertEqual(1, len(mutator.operators))
