import unittest

from shamir.shamir import Shamir, ShamirSpec
from shamir.share import Share
import itertools
import random


class TestShamir(unittest.TestCase):

    def test_shamir_pool_correctness(self):
        """
        Test that shamir pool operations correctly function together.
        """
        num_tests = 20
        max_k, max_n = 5, 10
        primes = [3, 5, 7, 11, 13, 17, 19]
        for _ in range(num_tests):
            p = primes[random.randrange(len(primes))]
            s = random.randrange(p)
            k = random.randint(2, min(p - 1, max_k))
            n = random.randint(k, min(p - 1, max_n))

            # test pool generation
            shamir = Shamir(p)
            secret = Share(s)
            spec = ShamirSpec(k, n)
            shares = shamir.generate_pool(secret, spec)

            # test pool extension: extend by one additional share

            if n < p - 1:
                sh = shamir.extend_pool(n + 1, shares)
                shares.append(sh)

            # test secret recovery and compatibility of extension share
            enough_shares = itertools.combinations(range(len(shares)), k)
            for tup in enough_shares:
                selected = tuple(shares[i] for i in tup)
                recovered_secret = shamir.recover_secret(selected)
                self.assertEqual(secret, recovered_secret)

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
            secret = Share(s)
            spec = ShamirSpec(k, n)

            shares = shamir.generate_pool(secret, spec)
            for sh in shares:
                self.assertEqual(type(sh), Share, msg)
                self.assertEqual(len(sh.prefix), 1, msg)
            self.assertEqual(len(shares), n, msg)

        # explicit coefficients
        s, k, n, p = 0, 3, 4, 11
        seed = 12345
        shamir = Shamir(p)
        secret = Share(s)
        spec = ShamirSpec(k, n)

        shares1 = shamir.generate_pool(secret, spec, seed=seed)
        shares2 = shamir.generate_pool(secret, spec, seed=seed)
        for sh1, sh2 in zip(shares1, shares2):
            self.assertEqual(sh1, sh2)

    def test_shamir_extend(self):
        s, k, n, p = 0, 2, 4, 11
        shamir, shares = gen_simple_pool(s, k, n, p)

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
                shamir.extend_pool(x, shares)
            except Exception as e:
                raise(e)
                self.fail(msg)


def gen_simple_pool(s, k, n, p):
    shamir = Shamir(p)
    secret = Share(s)
    spec = ShamirSpec(k, n)
    return shamir, shamir.generate_pool(secret, spec)
