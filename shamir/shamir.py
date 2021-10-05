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

from shamir.mod_util import eval_poly_mod, lagrange_interpolate
from shamir.share import Share, ShareFactory
from dataclasses import dataclass
from typing import Tuple, Union

import secrets
import random


# TODO document that all computations for this class are done over Z/pZ, and
# that input parameters are interpreted accordingly


class Shamir:
    def __init__(self, prime):
        """
        Construct a Shamir object for secret sharing modulo the given prime
        modulus.
        """
        self.p = prime

    def generate_pool(self, secret, spec, rand_indices=None, seed=None):
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
        if type(secret) is not Share:
            raise ValueError("secret must be of type Share")

        spec.validate()

        if seed is None:
            r = secrets.SystemRandom()

            def rng(idx=0):
                return r
        else:
            r = random.Random(seed)
            rands = list()

            # several parallel deterministic random threads
            def rng(idx=0):
                if len(rands) <= idx:
                    rands.extend([
                        random.Random(r.random())
                        for _ in range(len(rands), idx + 1)
                    ])
                return rands[idx]

        return self._rec_generate_pool(secret, spec, rand_indices, rng)

    def _rec_generate_pool(self, secret, spec, rand_indices, rng):
        # 1. generate coefficients
        num_shares = spec.num_shares()
        threshold = spec.threshold

        if num_shares >= self.p:
            raise ValueError(
                "specified number of shares is too large for prime modulus")

        coeff_rng = rng(0)
        coeffs = [secret.value % self.p]
        coeffs.extend(
            [coeff_rng.randrange(self.p) for _ in range(threshold - 1)])

        # 2. generate indices
        if rand_indices is None:
            indices = range(1, num_shares + 1)
        else:
            index_rng = rng(1)
            indices = index_rng.sample(
                range(1, rand_indices + 1), k=num_shares)

        # 3. generate shares
        share_pts = [
            (x, eval_poly_mod(coeffs, x, self.p)) for x in indices
        ]

        # 4. recursive generate on sub_specs
        shares = list()
        if type(spec.shares) is int:
            shares.extend([
                Share(y, secret.prefix + (x, )) for x, y in share_pts
            ])
        else:
            for sh in spec.shares:
                idx = 0
                if type(sh) is int:
                    shares.extend([
                        Share(y, secret.prefix + (x, ))
                        for x, y in share_pts[idx:idx + sh]
                    ])
                else:
                    sub_shares = [
                        Share(y, secret.prefix + (x, ))
                        for x, y in share_pts[idx:idx + sh[0]]
                    ]
                    for s_sh in sub_shares:
                        shares.extend(
                            self._rec_generate_pool(
                                s_sh, sh[1], rand_indices, rng)
                        )

        # 5. return list of all generated shares
        return shares

    def extend_pool(self, val, shares):
        """
        Extend the secret share pool by generating a share with the given
        x-value or prefix.
        """

        if type(val) is int:
            prefix = ()
            x = val
        elif type(val) is tuple and all(type(n) is int for n in val):
            if val == ():
                return
                raise ValueError("cannot extend pool with empty value")
            prefix = val[:-1]
            x = val[-1]
        else:
            raise ValueError("extending value must be an int or tuple of ints")

        if x % self.p == 0 or any(n % self.p == 0 for n in prefix):
            raise ValueError("x-value of 0 is reserved")

        if len(shares) == 0:
            raise ValueError("must specify at least one share")

        active_shares = dict()
        for sh in shares:
            p = sh.prefix
            if len(p) > len(prefix) and p[:len(prefix)] == prefix:
                head = p[:len(prefix) + 1]
                if head not in active_shares:
                    active_shares[head] = list()
                active_shares[head].append(sh)

        peers = list()
        for p in active_shares:
            peers.append(self._combine_shares(active_shares[p]))
        if len(peers) == 0:
            raise ValueError("specified prefix has no peers")

        new_value = lagrange_interpolate(
            x,
            tuple(sh.x() for sh in peers),
            tuple(sh.value for sh in peers),
            self.p
        )

        return Share(new_value, prefix + (x, ))

    def recover_secret(self, shares):
        """
        Recover the secret from share points.
        """
        secret = self._combine_shares(shares)
        return secret

    def _combine_shares(self, shares):
        """
        Combine the given shares up to their common prefix.  Assumes that all
        specified shares come from the same properly constructed pool.
        """

        common_prefix = ShareFactory.common_prefix(shares)
        for sh in shares:
            if sh.prefix == common_prefix:
                return sh
        len_common_prefix = len(common_prefix)
        result = None

        # generate all prefixes and subprefixes
        share_pool = dict()
        for sh in shares:
            for i in range(len_common_prefix, len(sh.prefix)):
                pr = sh.prefix[:i]
                if pr not in share_pool:
                    share_pool[pr] = list()
            share_pool[sh.prefix[:-1]].append(sh)

        # merge shares given with each common prefix
        all_prefixes = list(share_pool.keys())
        all_prefixes.sort(key=(lambda pr: len(pr)), reverse=True)
        for pr in all_prefixes:
            xs = tuple(sh.x() for sh in share_pool[pr])
            ys = tuple(sh.value for sh in share_pool[pr])
            merged_val = lagrange_interpolate(0, xs, ys, self.p)
            merged = Share(merged_val, pr)

            if pr == common_prefix:
                result = merged
                break
            else:
                new_pr = pr[:-1]
                share_pool[new_pr].append(merged)

        return result

    def gen(self, secret, coeffs, indices):
        # coeffs for random polynomial in (ZZ/pZZ)[x] of degree threshold-1
        coeffs = [secret % self.p] + coeffs
        return [(i, eval_poly_mod(coeffs, i, self.p)) for i in indices]

    # def eval(self, x, points):
    #     x_s, y_s = zip(*points)
    #     return lagrange_interpolate(x, x_s, y_s, self.p)

    # combine shares up to given prefix, checks that all shares have prefix
    # combine shares up to common prefix
    # for extend CLI, extend at level of common prefix


@dataclass
class ShamirSpec:
    """
    Data class representing a nested Shamir secret pool specification.  Each
    object represents one level of indirection.  The ``threshold`` field gives
    the number of shares required to reconstruct the secret.  The ``shares``
    field specifies the shares to produce, using the following format:

      - If ``shares`` is an int, then produce that number of standard shares.
      - If ``shares`` is a tuple, then each element of the tuple should be:
        - An int to represent a number of standard shares.
        - A tuple consisting of an int and a ShamirSpec object, where the
          ShamirSpec specifies a subspecification to split a share into, and
          the int represents the number of shares to split in this way.
    """
    threshold: int
    shares: Union[
        int,
        Tuple[
            Union[int, Tuple[int, 'ShamirSpec']],
            ...
        ]
    ]

    def num_shares(self):
        """
        Returns the number of shares specified by this ShamirSpec object at its
        top level.
        """
        if type(self.shares) is int:
            return self.shares
        else:
            accum = 0
            for sh in self.shares:
                if type(sh) is int:
                    accum += sh
                else:
                    accum += sh[0]

    def total_shares(self):
        """
        Returns the total number of shares specified by this ShamirSpec object.
        """
        if type(self.shares) is int:
            return self.shares
        else:
            accum = 0
            for sh in self.shares:
                if type(sh) is int:
                    accum += sh
                else:
                    accum += sh[0] * sh[1].total_shares()
            return accum

    def num_coeffs(self):
        """
        Returns the number of coefficients needed to specify the Shamir
        polynomials associated with this specification.
        """
        accum = self.threshold - 1
        if type(self.shares) is int:
            pass
        else:
            for sh in self.shares:
                if type(sh) is int:
                    pass
                else:
                    accum += sh[0] * sh[1].num_coeffs()
        return accum

    def validate(self):
        """
        Check recursively that ``shares`` has size at least ``threshold``, i.e.
        that a secret may be reproduced from a pool generated with this
        ShamirSpec object.
        """
        # check that top level threshold is positive
        if self.threshold < 1:
            raise ValueError("threshold is nonpositive")

        # check that all share multiplicities are positive
        if type(self.shares) is int:
            if self.shares < 1:
                raise ValueError("nonpositive share multiplicity")
        else:
            for sh in self.shares:
                if type(sh) is int:
                    if sh < 1:
                        raise ValueError("nonpositive share multiplicity")
                else:
                    if sh[0] < 1:
                        raise ValueError(
                            "nonpositive sub-specification multiplicity")

        # check that top level number of shares is not smaller than threshold
        if self.num_shares() < self.threshold:
            raise ValueError("secret not recoverable from specified shares")

        # validate all sub-specifications
        if type(self.shares) is not int:
            for sh in self.shares:
                if type(sh) is not int:
                    sh[1].validate()
