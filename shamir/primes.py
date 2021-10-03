prime_offsets_filename = 'shamir/data/prime-offsets.dat'

# Description of largest primes smaller than some powers of 2.
# Offets from the Online Encyclopedia of Integer Sequences (OEIS)
# http://oeis.org/A013603/b013603.txt
# Values range from 1 up to 4096

# Corresponding primes given by: p = 2**idx - value
with open(prime_offsets_filename, 'r') as f:
    prime_offsets = [None] + [int(n) for n in f]


def _check_bitlength(bitlength):
    if type(bitlength) is not int or bitlength < 1\
            or bitlength >= len(prime_offsets):
        raise ValueError("invalid bitlength specified (%s)" % bitlength)


def valid_bitlengths():
    return range(1, len(prime_offsets))


def get_prime(bitlength):
    """
    Return a prime number suitable to represent (almost) all numbers up to a
    given bitlength.
    """
    _check_bitlength(bitlength)
    return 2**bitlength - prime_offsets[bitlength]


def format_prime(bitlength):
    """
    Return a concise string representation of the prime associated with a given
    bitlength.
    """
    _check_bitlength(bitlength)
    return "2^%d - %d" % (bitlength, prime_offsets[bitlength])
