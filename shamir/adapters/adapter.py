from abc import ABC, abstractmethod

from shamir.primes import get_prime

# adapter converts data format into number of appropriate bitlength
# adapter class then should handle checking validity of conversion, i.e. that
# produced number is in the proper range


class Adapter(ABC):
    """
    Abstract base class for adapters which convert a string of some format into
    an integer of a fixed maximum bitlength, and back again.
    """

    def __init__(self, bitlength):
        # TODO rewrite to work better with bitlength and prime specification
        # TODO how do we separate shamir secret sharing, which works over any
        #      finite field, from adapters, which are designed to work with a
        #      specific bitlength?
        # TODO utility class to aggregate operations over modular arithmetic.
        # TODO this class should work only with bitlengths, and not primes
        # TODO could be useful to create small standalone libraries for working
        #      with various finite fields; not today
        self.bitlength = bitlength
        self.p = get_prime(bitlength)

    @abstractmethod
    def to_int(self, str_value):
        pass

    @abstractmethod
    def from_int(self, int_value, pretty=False):
        pass

    @staticmethod
    @abstractmethod
    def get_bitlength(str_value):
        pass
