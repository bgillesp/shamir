def canonical_repr(num, modulus):
    """
    Return whether ``num`` is an int in the range [0, modulus).
    """
    return (type(num) is int) and (num >= 0) and (num < modulus)


def eval_poly_mod(poly_coeffs, x, modulus):
    """
    Evaluates a polynomial at a point x, modulo an integer.  The polynomial is
    expressed as a tuple of coefficients, given in increasing order of
    exponent.  If a_i is the i-th element of ``poly_coeffs``, then the
    associated polynomial is: a_0 x^0 + a_1 x^1 + ... + a_k x^k
    """
    accum = 0
    for coeff in reversed(poly_coeffs):
        accum *= x
        accum += coeff
        accum %= modulus
    return accum
