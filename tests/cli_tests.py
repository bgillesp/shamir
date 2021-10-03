import unittest
# import os

from shamir import version
from shamir.cli import cli
from tests.bip39_vectors import vectors, random_vector

from click.testing import CliRunner

# import shamir.cli as cli
# see: https://stackoverflow.com/questions/18668947/how-do-i-set-sys-argv-so-i-can-unit-test-it


class TestCli(unittest.TestCase):

    def test_cli_entrypoint(self):
        """
        Test that CLI entrypoint functions correctly.
        """
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(
            result.output, ''.join(['shamir, version ', version, '\n']))

    def test_generate(self):
        """
        Test CLI to generate
        """
        runner = CliRunner()
        # for v in vectors + [random_vector(seed=i) for i in range(3)]:
        #     threshold = len(v['coefficients']) + 1
            # num_
            # args = ['generate', v['coefficei
            # result = runner

    def test_extend(self):
        pass

    def test_combine(self):
        pass


