import unittest
from mutpy import controller


class MutationScoreTest(unittest.TestCase):

    def test_score(self):
        score = controller.MutationScore(all_mutants=11, killed_mutants=5, incompetent_mutants=1)
        self.assertEqual(score.count(), 50)
        score.inc_killed()
        self.assertEqual(score.count(), 60)

    def test_zero_score(self):
        score = controller.MutationScore(all_mutants=0)
        self.assertEqual(score.count(), 0)

