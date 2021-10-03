"""
The following Python implementation of Shamir's Secret Sharing is
adapted from code presented on Wikipedia's article of the same name:

https://en.wikipedia.org/w/index.php?title=Shamir%27s_Secret_Sharing
&oldid=1032647996

The code from that source is made available in the Public Domain under
the terms of CC0 and OWFa:

https://creativecommons.org/publicdomain/zero/1.0/
http://www.openwebfoundation.org/legal/the-owf-1-0-agreements/owfa-1-0

This adaptation is licensed according to the file `LICENSE` in the base
directory of the repository.
"""

import secrets


# TODO document that all computations for this class are done over Z/pZ, and
# that input parameters are interpreted accordingly


class Shamir:
    def __init__(self, prime):
        """
        Construct a Shamir object for secret sharing modulo the given prime
        modulus.
        """
        self.p = prime

    def _eval_at(self, poly_coeffs, x):
        """
        Evaluates polynomial (coefficient tuple) at x, used to generate a
        shamir pool in make_random_shares below.
        """
        accum = 0
        for coeff in reversed(poly_coeffs):
            accum *= x
            accum += coeff
            accum %= self.p
        return accum

    def _lagrange_interpolate(self, x, x_s, y_s):
        """
        Find the y-value for the given x, given n (x, y) points;
        k points will define a polynomial of up to kth order.
        """
        k = len(x_s)
        if k != len(set(x_s)):
            raise ValueError("points must be distinct")

        accum = 0
        for i in range(k):
            others = list(x_s)
            cur = others.pop(i)
            term = y_s[i]
            for o in others:
                term *= x - o
                term *= pow(cur - o, -1, self.p)
                term %= self.p
            accum += term
        accum %= self.p
        return accum

    def generate_pool(self, secret, threshold, num_shares, coeffs=None):
        """
        Generates random shamir secret shares for a given secret, and specified
        number of bits.  Returns the points of the shares.

        If specified, `coeffs` is an iterable containing coefficients for x,
        x^2, x^3, ... in the underlying polynomial, in that order.  These
        coefficients should be generated randomly in the interval [0, prime-1]
        using a secure source of randomness, as their randomness is the
        theoretical assurance that the resulting Shamir pool is secure.

        If `coeffs` is unspecified, then random coefficients are generated
        using the `secrets` standard library module.
        """
        if type(threshold) is not threshold < 1:
            raise ValueError("threshold must be a positive integer")

        if type(num_shares) is not int or num_shares < 1:
            raise ValueError("num_shares must be a positive integer")

        if num_shares < threshold:
            raise ValueError(
                "secret not recoverable from specified number of shares")

        if num_shares >= self.p:
            raise ValueError(
                "specified number of shares are too large for prime modulus")

        if type(secret) is not int:
            raise ValueError("secret must be an integer")

        if coeffs is None:
            coeffs = [secrets.randbelow(self.p) for _ in range(threshold - 1)]
        else:
            coeffs = [c % self.p for c in coeffs]

        # coeffs for random polynomial in (ZZ/pZZ)[x] of degree threshold-1
        coeffs = [secret % self.p] + coeffs
        return [(i, self._eval_at(coeffs, i))
                for i in range(1, num_shares + 1)]

    def extend_pool(self, x, shares):
        """
        Extend the secret share pool by generating a share with the given
        x-value.
        """

        if type(x) is not int:
            raise ValueError("x-value must be an int")

        if x % self.p == 0:
            raise ValueError(
                "x-value of 0 is reserved for the original secret")

        if len(shares) == 0:
            raise ValueError("must provide at least one share")

        x_s, y_s = zip(*shares)
        return self._lagrange_interpolate(x, x_s, y_s)

    def recover_secret(self, shares):
        """
        Recover the secret from share points.
        """
        x_s, y_s = zip(*shares)
        return self._lagrange_interpolate(0, x_s, y_s)
