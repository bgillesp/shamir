# class to represent (nested) Shamir shares

from dataclasses import dataclass
from typing import Tuple
import re


class ShareFactory:
    """
    Class to parse Shamir secret pool shares from string format.
    """

    """
    Parsing regular expression described as follows:
    - Look for a sequence of digits and whitespace, followed by a separator
      string, any whitespace character by default
    - This search is greedy, so finds the largest possible prefix
    - If such a sequence is found, parse the sequence (less the separator
      string) to form the prefix for the resulting share
    - All data following, which must include at least one non-whitespace
      character, is parsed by the adapter
    """
    PARSE_REGEX = '(?:([\\s,0-9]*){})?(.*\\S.*)'

    def __init__(self, separator=('\\s', None)):
        # self.adapter = adapter
        if type(separator) is str:
            self.separator_re = separator
            self.separator = separator
        elif type(separator) is tuple:
            self.separator_re, self.separator = separator
        else:
            raise ValueError("invalid separator string specified")
        self.re = re.compile(
            ShareFactory.PARSE_REGEX.format(self.separator_re)
        )

    def parse(self, share_str, adapter):
        # chop off integers until encountering something that is not an integer
        # set a string which represents the divider in case of ambiguity
        # regular expression might make sense to do this parsing
        m = self.re.match(share_str)
        if m is None:
            raise ValueError("unable to parse share string")
        prefix, value = m.groups()
        if prefix is None:
            prefix = ()
        else:
            prefix = tuple(int(s) for s in str(prefix).split())
        value = adapter.to_int(value)
        return Share(value, prefix)

    def format(self, share, adapter):
        parts = tuple(str(n) for n in share.prefix)
        if self.separator is not None:
            parts += (self.separator, )
        val = adapter.from_int(share.value)
        parts += (val, )
        return ' '.join(parts)

    def prefix_string(self, share_str):
        m = self.re.match(share_str)
        if m is None:
            raise ValueError("unable to parse share string")
        return m.group(1)

    def value_string(self, share_str):
        m = self.re.match(share_str)
        if m is None:
            raise ValueError("unable to parse share string")
        return m.group(2)

    @staticmethod
    def common_prefix(shares):
        if len(shares) >= 1:
            prefix = shares[0].prefix
            for sh in shares[1:]:
                prefix = ShareFactory._common_prefix(prefix, sh.prefix)
            return prefix
        else:
            raise ValueError("list of shares is empty")

    @staticmethod
    def _common_prefix_length(p1, p2):
        idx_max = min(len(p1), len(p2))
        for idx in range(idx_max):
            if p1[idx] != p2[idx]:
                return idx
        else:
            return idx_max

    @staticmethod
    def _common_prefix(p1, p2):
        length = ShareFactory._common_prefix_length(p1, p2)
        return p1[:length]


@dataclass
class Share:
    """
    Class representing a secret or a share of a Shamir secret pool.  This is a
    dumb data class, and all values and prefixes are represented as int values.
    """
    value: int
    prefix: Tuple[int, ...] = ()

    def depth(self):
        return len(self.prefix)

    def x(self):
        if len(self.prefix) > 0:
            return self.prefix[-1]
        else:
            return None
