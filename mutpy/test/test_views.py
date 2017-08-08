import unittest

from mutpy.views import QuietTextView

COLOR_RED = 'red'


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
