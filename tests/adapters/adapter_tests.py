import unittest
from shamir.adapters import Adapter
from shamir.primes import get_prime


class ConcreteAdapter(Adapter):
    """
    Concrete subclass of abstract Adapter class, with empty function calls.
    """

    def to_int(self, str_value):
        pass

    def from_int(self, int_value):
        pass

    @staticmethod
    def get_bitlength(str_value):
        pass


class TestAdapter(unittest.TestCase):
    def test_init(self):
        bitlength = 16
        adapter = ConcreteAdapter(bitlength)

        self.assertEqual(adapter.bitlength, bitlength)
        self.assertEqual(adapter.p, get_prime(bitlength))
