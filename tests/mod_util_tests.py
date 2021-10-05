import unittest

from shamir import mod_util


class TestModUtil(unittest.TestCase):
    def test_modular_inverses(self):
        """
        Test that inverses are available in modular arithmetic.  Implemented
        in Python 3.8 and higher.
        """
        p = 11
        self.assertEqual(pow(1, -1, p), 1)
        self.assertEqual(pow(2, -1, p), 6)
        self.assertEqual(pow(3, -1, p), 4)
        self.assertEqual(pow(4, -1, p), 3)
        self.assertEqual(pow(6, -1, p), 2)

    def test_poly_evaluation(self):
        """
        Test that modular arithmetic and polynomial evaluation works correctly.
        """
        N = 11

        coeffs = [2, 5, 3]  # f(x) = 2 + 5x + 3x^2
        self.assertEqual(mod_util.eval_poly_mod(coeffs, 0, N), 2)
        self.assertEqual(mod_util.eval_poly_mod(coeffs, 11, N), 2)
        self.assertEqual(mod_util.eval_poly_mod(coeffs, 1, N), 10)
        self.assertEqual(mod_util.eval_poly_mod(coeffs, 5, N), 3)
        self.assertEqual(mod_util.eval_poly_mod(coeffs, -10, N), 10)

    def test_canonical_repr(self):
        """
        Test the check of whether an input is a number properly represented in
        some modulus.
        """
        N = 11
        self.assertTrue(mod_util.canonical_repr(0, N))
        self.assertTrue(mod_util.canonical_repr(7, N))
        self.assertTrue(mod_util.canonical_repr(10, N))
        self.assertFalse(mod_util.canonical_repr('7', N))
        self.assertFalse(mod_util.canonical_repr(-1, N))
        self.assertFalse(mod_util.canonical_repr(11, N))

    def test_lagrange_interpolation(self):
        """
        Test that mod-p Lagrange interpolation functions properly.
        """

        # f(x) = 2 + 5x + 3x^2 (mod 11)
        p = 11
        x_s = range(10)
        y_s = [2, 10, 2, 0, 4, 3, 8, 8, 3, 4]

        # test valid interpolation with various input points for f
        for idx_s in [(1, 4, 6), (4, 5, 6), (7, 1, 2), (9, 8, 0)]:
            cur_x_s = [x_s[i] for i in idx_s]
            cur_y_s = [y_s[i] for i in idx_s]
            for x, y in zip(x_s, y_s):
                self.assertEqual(
                    mod_util.lagrange_interpolate(x, cur_x_s, cur_y_s, p), y
                )

        # test bad inputs for interpolation
        for idx_s in [(1, 1, 3)]:
            bad_x_s = [x_s[i] for i in idx_s]
            bad_y_s = [y_s[i] for i in idx_s]
            x, y = 0, 2
            with self.assertRaises(ValueError):
                mod_util.lagrange_interpolate(x, bad_x_s, bad_y_s, p)
