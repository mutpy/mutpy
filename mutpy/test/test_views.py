import sys
import unittest
from contextlib import contextmanager
from io import StringIO

from mutpy import utils
from mutpy.views import QuietTextView, TextView

COLOR_RED = 'red'


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class QuietTextViewTest(unittest.TestCase):
    @staticmethod
    def get_quiet_text_view(colored_output=False):
        return QuietTextView(colored_output=colored_output)

    def test_decorate_with_color(self):
        # given
        text_view = self.get_quiet_text_view(colored_output=True)
        text = 'mutpy'
        expected_colored_text = '\x1b[31mmutpy\x1b[0m'
        # when
        colored_text = text_view.decorate(text, color=COLOR_RED)
        # then
        self.assertEqual(expected_colored_text, colored_text)


class TextViewTest(unittest.TestCase):
    SEPARATOR = '--------------------------------------------------------------------------------'
    EOL = "\n"

    @staticmethod
    def get_text_view(colored_output=False, show_mutants=False):
        return TextView(colored_output=colored_output, show_mutants=show_mutants)

    def test_print_code(self):
        # given
        text_view = self.get_text_view(show_mutants=True)
        original = utils.create_ast('x = x + 1')
        mutant = utils.create_ast('x = x - 1')
        # when
        with captured_output() as (out, err):
            text_view.print_code(mutant, original)
        # then
        output = out.getvalue().strip()
        self.assertEqual(
            self.SEPARATOR + self.EOL + '- 1: x = x + 1' + self.EOL + '+ 1: x = x - 1' + self.EOL + self.SEPARATOR,
            output
        )
