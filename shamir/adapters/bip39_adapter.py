from mnemonic import Mnemonic
from shamir.adapters import Adapter
from shamir.mod_util import canonical_repr

from itertools import zip_longest
from math import ceil


class BIP39Adapter(Adapter):
    def __init__(self, bitlength, language="english"):
        if bitlength not in [128, 160, 192, 224, 256]:
            raise ValueError(
                "invalid bitlength for BIP39 mnemonics (%d)" % bitlength)
        super(BIP39Adapter, self).__init__(bitlength)
        self.bip39 = Mnemonic(language)

    def to_int(self, str_value):
        mnemo = self.bip39.expand(str_value)
        if not self.bip39.check(mnemo):
            raise ValueError("invalid BIP39 mnemonic")
        bitlength = 32 * (len(str.split(mnemo)) // 3)
        if bitlength != self.bitlength:
            raise ValueError(
                "mnemonic has incorrect bitlength (%d)" % bitlength)
        return int.from_bytes(self.bip39.to_entropy(mnemo), byteorder='big')

    def from_int(self, int_value, pretty=False):
        if not canonical_repr(int_value, self.p):
            raise ValueError(
                "integer value not properly represented by bitlength")
        mnemonic = self.bip39.to_mnemonic(
            int_value.to_bytes(self.bitlength // 8, byteorder='big')
        )
        if not pretty:
            return mnemonic
        else:
            return BIP39Adapter.format_mnemonic(mnemonic)

    @staticmethod
    def get_bitlength(str_value):
        """
        Return the bitlength associated to a mnemonic seed phrase.
        """
        return 32 * (len(str.split(str_value)) // 3)

    @staticmethod
    def format_mnemonic(str_value, pad_width=10, n_columns=2, numbers=True):
        words = str.split(str_value)
        c_len = ceil(len(words) / n_columns)
        columns = list()
        for start_idx in range(0, len(words), c_len):
            # parameters
            number_max_size = len(str(min(start_idx + c_len, len(words))))
            format_st = "%%%dd. " % number_max_size
            # generate and format column
            col = words[start_idx:start_idx + c_len]
            col = [format_st % (start_idx + j + 1) + w.ljust(pad_width)
                   for j, w in enumerate(col)]
            columns.append(col)
        rows = zip_longest(*columns, fillvalue='')
        return '\n'.join([''.join(row) for row in rows])
