import unittest


class TestSimpleMath(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(2 + 2, 4)


if __name__ == "__main__":
    unittest.main()
