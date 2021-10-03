import unittest

from shamir.shamir import Shamir
import itertools
import random


class TestShamir(unittest.TestCase):
    def test_modular_arithmetic(self):
        """
        Test that modular arithmetic and polynomial evaluation works correctly.
        """
        p = 11
        shamir = Shamir(p)

        coeffs = [2, 5, 3]  # f(x) = 2 + 5x + 3x^2
        self.assertEqual(shamir._eval_at(coeffs, 0), 2)
        self.assertEqual(shamir._eval_at(coeffs, 11), 2)
        self.assertEqual(shamir._eval_at(coeffs, 1), 10)
        self.assertEqual(shamir._eval_at(coeffs, 5), 3)
        self.assertEqual(shamir._eval_at(coeffs, -10), 10)

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

    def test_lagrange_interpolation(self):
        """
        Test that mod-p Lagrange interpolation functions properly.
        """

        # f(x) = 2 + 5x + 3x^2 (mod 11)
        p = 11
        shamir = Shamir(p)
        x_s = range(10)
        y_s = [2, 10, 2, 0, 4, 3, 8, 8, 3, 4]

        # test valid interpolation with various input points for f
        for idx_s in [(1, 4, 6), (4, 5, 6), (7, 1, 2), (9, 8, 0)]:
            cur_x_s = [x_s[i] for i in idx_s]
            cur_y_s = [y_s[i] for i in idx_s]
            for x, y in zip(x_s, y_s):
                self.assertEqual(
                    shamir._lagrange_interpolate(x, cur_x_s, cur_y_s), y
                )

        # test bad inputs for interpolation
        for idx_s in [(1, 1, 3)]:
            bad_x_s = [x_s[i] for i in idx_s]
            bad_y_s = [y_s[i] for i in idx_s]
            x, y = 0, 2
            with self.assertRaises(ValueError):
                shamir._lagrange_interpolate(x, bad_x_s, bad_y_s)

    def test_shamir_pool_correctness(self):
        """
        Test that shamir pool operations correctly function together.
        """
        num_tests = 50
        max_k, max_n = 6, 12
        primes = [3, 5, 7, 11, 13, 17, 19]
        for _ in range(num_tests):
            p = primes[random.randint(0, len(primes) - 1)]
            n = random.randint(1, min(p - 2, max_n))
            k = random.randint(1, min(n, max_k))
            s = random.randint(0, p - 1)
            shamir = Shamir(p)

            # test pool generation
            shares = shamir.generate_pool(s, k, n)

            # test pool extension: extend by one additional share
            x = n + 1
            y = shamir.extend_pool(x, [shares[i] for i in range(k)])
            shares.append((x, y))

            # test secret recovery and compatibility of extension share
            for tup in itertools.combinations(range(n + 1), k):
                selected = [shares[i] for i in tup]
                self.assertEqual(shamir.recover_secret(selected), s)

    def test_shamir_generate(self):
        bad_inputs = [          # (s, k, n, p)
            (0, 0, 1, 11),      # k too small
            (0, -1, 1, 11),     # k negative
            (0, 1.5, 1, 11),    # k a float
            (0, 0.5, 1, 11),    # k a float and too small
            (0, 1, 0, 11),      # n too small
            (0, 1, -1, 11),     # n negative
            (0, 1, 1.5, 11),    # n a float
            (0, 1, 0.5, 11),    # n a float and too small
            (0, 3, 2, 11),      # k larger than n
            (0, 101, 50, 11),   # k larger than n
            (2.5, 1, 1, 11),    # s a float
            (-0.5, 1, 1, 11),   # s negative and a float
            (0, 3, 5, 3),       # p too small for number of shares
            (0, 3, 5, 5),       # p too small for number of shares
        ]
        for s, k, n, p in bad_inputs:
            msg = "(s, k, n, p) = %s" % ((s, k, n, p), )
            with self.assertRaises(ValueError, msg=msg):
                shamir = Shamir(p)
                shamir.generate_pool(s, k, n)

        good_inputs = [
            (0, 2, 4, 11),
            (5, 3, 5, 13),
            (1, 1, 1, 101),
        ]
        for s, k, n, p in good_inputs:
            msg = "(s, k, n, p) = %s" % ((s, k, n, p), )
            shamir = Shamir(p)
            shares = shamir.generate_pool(s, k, n)
            for sh in shares:
                self.assertEqual(type(sh), tuple, msg)
                self.assertEqual(len(sh), 2, msg)
            self.assertEqual(len(shares), n, msg)

        # explicit coefficients
        s, k, n, p = 0, 3, 4, 11
        coeffs = [123, 1212123]
        shamir = Shamir(p)
        shares1 = shamir.generate_pool(s, k, n, coeffs=coeffs)
        shares2 = shamir.generate_pool(s, k, n, coeffs=coeffs)
        for (x1, y1), (x2, y2) in zip(shares1, shares2):
            self.assertEqual(x1, x2)
            self.assertEqual(y1, y2)

    def test_shamir_extend(self):
        s, k, n, p = 0, 2, 4, 11
        shamir = Shamir(p)
        shares = shamir.generate_pool(s, k, n)

        bad_x_values = [
            1.5,    # x a float
            -1.0,   # x a negative float
            0,      # x is zero (reserved for secret)
            p,      # x is zero mod p
        ]
        for x in bad_x_values:
            msg = "x = %s" % x
            with self.assertRaises(ValueError, msg=msg):
                shamir.extend_pool(x, shares)

        msg = "no shares"
        with self.assertRaises(ValueError, msg=msg):
            shamir.extend_pool(1, [])

        good_x_values = range(1, p)
        for x in good_x_values:
            msg = "x = %s" % x
            try:
                y = shamir.extend_pool(x, shares)
            except Exception:
                self.fail(msg)
            # self.assertTrue(shamir._proper(y), msg)
