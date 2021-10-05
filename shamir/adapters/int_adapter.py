from shamir.adapters import Adapter
from shamir.mod_util import canonical_repr


class IntAdapter(Adapter):
    def __init__(self, bitlength):
        super(IntAdapter, self).__init__(bitlength)

    def to_int(self, value):
        self._validate(int(value))
        return int(value)

    def from_int(self, value, pretty=False):
        self._validate(value)
        if not pretty:
            return str(value)
        else:
            return str(value)

    def _validate(self, value):
        if not canonical_repr(value, self.p):
            raise ValueError("integer value (%d) not properly"
                             " represented by bitlength" % value)

    @classmethod
    def get_bitlength(value):
        """
        Return the bitlength associated to a mnemonic seed phrase.
        """
        return int.bit_length(value)
