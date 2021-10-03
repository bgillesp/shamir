import unittest

from shamir.mod_util import eval_poly_mod, canonical_repr


class TestModUtil(unittest.TestCase):

    def test_poly_evaluation(self):
        """
        Test that modular arithmetic and polynomial evaluation works correctly.
        """
        N = 11

        coeffs = [2, 5, 3]  # f(x) = 2 + 5x + 3x^2
        self.assertEqual(eval_poly_mod(coeffs, 0, N), 2)
        self.assertEqual(eval_poly_mod(coeffs, 11, N), 2)
        self.assertEqual(eval_poly_mod(coeffs, 1, N), 10)
        self.assertEqual(eval_poly_mod(coeffs, 5, N), 3)
        self.assertEqual(eval_poly_mod(coeffs, -10, N), 10)

    def test_canonical_repr(self):
        """
        Test the check of whether an input is a number properly represented in
        some modulus.
        """
        N = 11
        self.assertTrue(canonical_repr(7, N))
        self.assertTrue(canonical_repr(0, N))
        self.assertTrue(canonical_repr(10, N))
        self.assertFalse(canonical_repr('7', N))
        self.assertFalse(canonical_repr(-1, N))
        self.assertFalse(canonical_repr(11, N))
