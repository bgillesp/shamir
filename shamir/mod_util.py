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


def lagrange_interpolate(x, x_s, y_s, modulus):
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
            term *= pow(cur - o, -1, modulus)
            term %= modulus
        accum += term
    accum %= modulus
    return accum
