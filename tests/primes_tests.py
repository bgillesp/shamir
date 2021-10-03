import unittest

import shamir.primes as primes
import math


valid_bitlengths = primes.valid_bitlengths()
invalid_bitlengths = [0, max(valid_bitlengths) + 1, -5, 1.5, 'a']

class TestPrimes(unittest.TestCase):

    def test_valid_bitlengths(self):
        """
        Test that the bitlengths specified as valid in this test suite are
        recognized as valid by the primes module.
        """
        mod_valid_bitlengths = primes.valid_bitlengths()
        for bits in valid_bitlengths:
            self.assertTrue(bits in mod_valid_bitlengths)

    def test_prime_lookup(self):
        """
        Test that prime lookup returns valid moduli of approximately the
        correct size, and checks for valid bitlengths.
        """
        # only valid bitlengths
        for bits in valid_bitlengths:
            msg = "bits = %d" % bits
            p = primes.get_prime(bits)
            self.assertEqual(bits, round(math.log2(p)), msg)

        # select invalid bitlengths
        for bits in invalid_bitlengths:
            msg = "bits = %s" % bits
            with self.assertRaises(ValueError, msg=msg):
                primes.get_prime(bits)

    def test_prime_format(self):
        """
        Test that prime format returns a string.
        """
        for bits in valid_bitlengths:
            s = primes.format_prime(bits)
            self.assertEqual(type(s), str)
