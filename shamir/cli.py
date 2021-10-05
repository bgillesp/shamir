from shamir import Shamir, get_prime, format_prime, version
from shamir.shamir import ShamirSpec
from shamir.share import ShareFactory, Share
from shamir.adapters import BIP39Adapter
from mnemonic import Mnemonic

import click
import logging
import os
import sys


@click.group(
    name='shamir',
    context_settings={'help_option_names': ['-h', '--help']}
)
@click.version_option(version=version)
def cli():
    """
    Generate or extend a Shamir secret sharing pool, or reconstitute a secret
    from shares.
    """
    pass


@cli.command()
@click.argument('threshold', type=int)
@click.argument('num_shares', type=int)
@click.option('-s', '--secret',
              help='Secret seed phrase to represent as shares, expressed as a'
              ' single string with words separated by spaces.')
@click.option('-l', '--language', 'lang', default='english',
              help='Language list to use for BIP-39 mnemonic phrases.')
@click.option('-r', '--rand', 'rand_indices', type=int,
              help='Shares are created with random indices between 1 and the'
              ' specified value.')
@click.option('-p', '--pretty', is_flag=True,
              help='Print output in pretty human-readable format.')
@click.option('--seed', type=int,
              help='Option to facilitate testing.  Use a pseudorandom number'
              ' generator with the specified seed instead of a secure system'
              ' random number generator.  DO NOT USE THIS OPTION TO GENERATE A'
              ' PRODUCTION POOL.  The use of a deterministic random number'
              ' generator may reduce the security of the output.')
@click.option('--list-parameters', 'list_params', is_flag=True,
              help='Output a list of internal parameters which would be used'
              ' for the computation, then exit.')
def generate(threshold, num_shares, secret, lang,
             rand_indices, pretty, seed, list_params):
    """
    Generate shares of a Shamir secret sharing pool for a specified secret.
    Generates a pool consisting of NUM_SHARES total shares, any THRESHOLD of
    which may be used to reconstruct the original secret.  Secret is read from
    standard input or specified as a string with the --secret option.
    """
    if threshold <= 0:
        exit_error("threshold must be a positive integer")

    if num_shares < threshold:
        exit_error("num_shares must be at least as large as threshold")

    if secret is None:
        if os.isatty(sys.stdin.fileno()):
            exit_error("no secret seed phrase specified")
        secret = sys.stdin.readline().rstrip()

    try:
        sh_fact = ShareFactory()
        mnemonic_phrase = sh_fact.value_string(secret)
        bitlength = BIP39Adapter.get_bitlength(mnemonic_phrase)
        adapter = BIP39Adapter(bitlength, lang)

        secret = sh_fact.parse(secret, adapter)
        spec = ShamirSpec(threshold, num_shares)
        prime, prime_str = get_prime(bitlength), format_prime(bitlength)

        shamir = Shamir(prime)
        shares = shamir.generate(
            secret, spec, rand_indices=rand_indices, seed=seed)

        if list_params:
            exit_list_params({
                "bitlength": bitlength,
                "prime_modulus": prime_str,
            })
    except Exception as e:
        exit_error(str(e))

    if pretty:
        for share in shares:
            prefix_str = '.'.join(str(n) for n in share.prefix)
            print(f"Share {prefix_str}")
            print(adapter.from_int(share.value, pretty=True))
    else:
        for share in shares:
            print(sh_fact.format(share, adapter))


@cli.command()
@click.argument('new_share_number', type=str)
@click.option('-s', '--share', 'share_strs', multiple=True, type=str,
              help='Specify one of the shares to use to specify the pool.')
@click.option('-l', '--language', 'lang', default='english',
              help='Language list to use for BIP-39 mnemonic phrases.')
@click.option('-p', '--pretty', is_flag=True,
              help='Print output in pretty human-readable format.')
@click.option('--list-parameters', 'list_params', is_flag=True,
              help='Output a list of internal parameters which would be used'
              ' for the computation, then exit.')
def extend(new_share_number, share_strs, lang, pretty, list_params):
    """
    Extend an existing Shamir pool for BIP-39 mnemonic seed phrases.  Each
    share should be provided as a string in the following format:

      'x word_1 word_2 ... word_n'

    Here, 'x' represents the share number, and 'word_1 word_2 ... word_n' is
    the BIP-39 mnemonic phrase of the share.
    """
    if not os.isatty(sys.stdin.fileno()):
        share_strs += tuple(line.rstrip() for line in sys.stdin.readlines())

    if share_strs == ():
        exit_error("no shamir pool shares specified")

    try:
        sh_fact = ShareFactory()
        a_share_mnem = sh_fact.value_string(share_strs[0])
        bitlength = BIP39Adapter.get_bitlength(a_share_mnem)
        adapter = BIP39Adapter(bitlength, lang)

        new_share_number = tuple(int(n) for n in new_share_number.split())

        shares = tuple(sh_fact.parse(sh, adapter) for sh in share_strs)

        # test for empty prefixes
        for sh in shares:
            if len(sh.prefix) == 0:
                raise ValueError("specified share has empty prefix")

        prime, prime_str = get_prime(bitlength), format_prime(bitlength)
        shamir = Shamir(prime)
        new_share = shamir.extend(new_share_number, shares)

        if list_params:
            exit_list_params({
                "bitlength": bitlength,
                "prime_modulus": prime_str,
            })
    except Exception as e:
        exit_error(str(e))

    if pretty:
        prefix_str = '.'.join(str(n) for n in new_share.prefix)
        print("Share %s" % prefix_str)
        print(adapter.from_int(new_share.value, pretty=True))
    else:
        print(sh_fact.format(new_share, adapter))


@cli.command()
@click.option('-s', '--share', 'share_strs', multiple=True, type=str,
              help='Specify one of the shares to use to reconstruct the secret'
              ' mnemonic.')
@click.option('-f', '--filename', 'file', type=click.File(),
              help='File to read for shares used to reconstruct the secret'
              ' mnemonic.')
@click.option('-l', '--language', 'lang', default='english',
              help='Language list to use for BIP-39 mnemonic phrases.')
@click.option('-p', '--pretty', is_flag=True,
              help='Print output in pretty human-readable format.')
@click.option('--list-parameters', 'list_params', is_flag=True,
              help='Output a list of internal parameters which would be used'
              ' for the computation, then exit.')
def combine(share_strs, file, lang, pretty, list_params):
    """
    Combine shares of a Shamir pool for BIP-39 mnemonic seed phrases to recover
    the original secret phrase.  Each share should be provided as a string in
    the following format:

      'x word_1 word_2 ... word_n'

    Here, 'x' represents the share number, and 'word_1 word_2 ... word_n' is
    the BIP-39 mnemonic phrase of the share.
    """
    if not os.isatty(sys.stdin.fileno()):
        share_strs += tuple(line.rstrip() for line in sys.stdin.readlines())

    if share_strs == ():
        exit_error("no shamir pool shares specified")

    try:
        sh_fact = ShareFactory()
        a_share_mnem = sh_fact.value_string(share_strs[0])
        bitlength = BIP39Adapter.get_bitlength(a_share_mnem)
        adapter = BIP39Adapter(bitlength, lang)

        prime, prime_str = get_prime(bitlength), format_prime(bitlength)
        shamir = Shamir(prime)

        shares = tuple(sh_fact.parse(sh, adapter) for sh in share_strs)
        secret = shamir.combine(shares)

        if list_params:
            exit_list_params({
                "bitlength": bitlength,
                "prime_modulus": prime_str,
            })
    except Exception as e:
        exit_error(str(e))

    if pretty:
        if len(secret.prefix) > 0:
            prefix_str = '.'.join(str(n) for n in secret.prefix)
            print(f"Combined Share {prefix_str}")
        else:
            print("Root Share")
        print(adapter.from_int(secret.value, pretty=True))
    else:
        print(sh_fact.format(secret, adapter))


def exit_error(error_str):
    print(_error_msg(error_str))
    exit(1)


def exit_list_params(param_dict):
    print("parameters:")
    for key, value in param_dict.items():
        print(f"  {key}={value}")
    exit(0)


def _error_msg(error_str):
    return ''.join(["error: ", error_str])


if __name__ == "__main__":
    cli()
    exit(0)
