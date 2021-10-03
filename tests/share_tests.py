import unittest

from shamir.share import ShareFactory, Share
from shamir.adapters import IntAdapter
# import itertools
# import random


class TestShare(unittest.TestCase):
    def test_common_prefix(self):
        """
        Test construction of longest common prefix of shares.
        """
        shares = [
            Share(0, ()),
            Share(1, (1,)),
            Share(2, (1, 2)),
            Share(3, (1, 3)),
            Share(4, (2, 1)),
            Share(5, (1, 2, 3)),
            Share(6, (1, 2, 4)),
            Share(7, (1, 2, 3, 4)),
        ]
        cases = [
            ([0], ()),
            ([0, 1], ()),
            ([1, 2], (1,)),
            ([2, 3], (1,)),
            ([1, 4], ()),
            ([2, 5, 6], (1, 2)),
            ([6, 7], (1, 2)),
            ([3, 5], (1,)),
        ]
        for share_indices, prefix in cases:
            share_list = [shares[i] for i in share_indices]
            self.assertEqual(ShareFactory.common_prefix(share_list), prefix)

    def test_parser(self):
        """
        Test the parser regular expression for share strings.
        """

        # Test parsing with integer adapter and default separator string
        bitlength = 8
        adapter = IntAdapter(bitlength)
        sh_fact = ShareFactory()

        cases = [
            # empty prefix
            ('0', Share(0, ())),
            ('  0', Share(0, ())),
            ('0  ', Share(0, ())),
            # nonempty prefix
            ('1 0', Share(0, (1, ))),
            ('\t1   0 \t', Share(0, (1, ))),
            (' 1\t0\n', Share(0, (1, ))),
            # longer prefix
            ('5 4 3 2 1 0', Share(0, (5, 4, 3, 2, 1))),
            # large integers allowed in prefix
            ('99999 10', Share(10, (99999, ))),
        ]
        for share_str, share in cases:
            msg = 'share_str = "%s"' % share_str
            self.assertEqual(sh_fact.parse(share_str, adapter), share, msg)

        error_cases = [
            # string of only whitespace
            '',
            '  ',
            '\n',
            # invalid prefix
            'a 0',
            ':::120398dfajls 0',
            # value after prefix rejected by adapter
            '1 256'
        ]
        for share_str in error_cases:
            msg = 'share_str = "%s"' % share_str
            with self.assertRaises(ValueError, msg=msg):
                sh_fact.parse(share_str, adapter)

    def test_parser_custom_separator(self):
        # Test parsing with integer adapter and specified separator string
        bitlength = 8
        adapter = IntAdapter(bitlength)
        sep = 'foo'
        sh_fact = ShareFactory(separator=sep)

        cases = [
            # empty prefix
            ('0', Share(0, ())),
            ('  0', Share(0, ())),
            ('0  ', Share(0, ())),
            # nonempty prefix
            ('1 foo 0', Share(0, (1, ))),
            ('1 foo0', Share(0, (1, ))),
            ('1foo 0', Share(0, (1, ))),
            ('1foo0', Share(0, (1, ))),
            ('1\tfoo\t0', Share(0, (1, ))),
            ('1 foo 0', Share(0, (1, ))),
        ]
        for share_str, share in cases:
            msg = 'share_str = "%s", separator = "%s"' % (share_str, sep)
            self.assertEqual(sh_fact.parse(share_str, adapter), share, msg)

        error_cases = [
            # string of only whitespace
            '',
            '  ',
            '\n',
            # invalid prefix
            'a foo 0',
            ':::120398dfajls foo 0',
            # missing separator
            '1 0',
            '5 4 3 2 1 0',
            '1 bar 0',
            '1fo0',
        ]
        for share_str in error_cases:
            msg = 'share_str = "%s", separator = "%s"' % (share_str, sep)
            with self.assertRaises(ValueError, msg=msg):
                sh_fact.parse(share_str, adapter)
