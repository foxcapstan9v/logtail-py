import unittest
from logtail import Rule, match


class MatchTests(unittest.TestCase):
    def test_hits(self):
        rules = [Rule.build("oom", r"OutOfMemory")]
        self.assertEqual(len(match(rules, "x OutOfMemory y")), 1)

    def test_miss(self):
        rules = [Rule.build("oom", r"OutOfMemory")]
        self.assertEqual(match(rules, "all good"), [])


if __name__ == "__main__":
    unittest.main()
