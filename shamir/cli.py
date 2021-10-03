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
@click.option('-v', '--verbose', is_flag=True,
              help='Print verbose output.')
@click.option('--seed', type=int,
              help='Option to facilitate testing.  Use a pseudorandom number'
              ' generator with the specified seed instead of a secure system'
              ' random number generator.  DO NOT USE THIS OPTION TO GENERATE A'
              ' PRODUCTION POOL.  The use of a deterministic random number'
              ' generator may reduce the security of the output.')
def generate(threshold, num_shares, secret, lang,
             rand_indices, pretty, verbose, seed):
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
        shares = shamir.generate_pool(
            secret, spec, rand_indices=rand_indices, seed=seed)
    except Exception as e:
        raise(e)
        exit_error(str(e))

    if pretty:
        print("====== Begin Shamir Secret Pool ======")
        if verbose:
            print("threshold = %d shares" % threshold)
            print("prime_modulus = %s" % prime_str)
        if len(secret.prefix) > 0:
            print()
            print("----- Prefix -----")
            print(' '.join(str(p) for p in secret.prefix))
        print()
        print("------ Secret ------")
        print(adapter.from_int(secret.value, pretty=True))
        print()
        for share in shares:
            print("------ Share %d ------" % share.x())
            logging.info("x = %d" % share.x())
            print(adapter.from_int(share.value, pretty=True))
            print()
        print("====== End Shamir Secret Pool ======")
    else:
        if verbose:
            print("k = %d, p = %s" % (threshold, prime_str))
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
@click.option('-v', '--verbose', is_flag=True,
              help='Print verbose output.')
def extend(new_share_number, share_strs, lang, pretty, verbose):
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

        new_share = shamir.extend_pool(new_share_number, shares)
        prefix_str = ' '.join(str(n) for n in new_share.prefix)
    except Exception as e:
        exit_error(str(e))

    if pretty:
        print("====== Begin Extend Shamir Secret Pool ======")
        if verbose:
            print("prime_modulus = %s" % prime_str)
        print()
        print("New Share (%s)" % prefix_str)
        print(adapter.from_int(new_share.value, pretty=True))
        print()
        print("====== End Extend Shamir Secret Pool ======")
    else:
        if verbose:
            print("p = %s" % prime_str)
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
@click.option('-v', '--verbose', is_flag=True,
              help='Print verbose output.')
def combine(share_strs, file, lang, pretty, verbose):
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
        secret = shamir.recover_secret(shares)

        # if secret is None:
        #     raise Exception("error merging secret shares")
    except Exception as e:
        exit_error(str(e))

    if pretty:
        print("====== Begin Recovered Shamir Secret ======")
        if verbose:
            print("prime_modulus = %s" % prime_str)
        print()
        print("Combined Mnemonic")
        if secret.prefix != ():
            prefix_str = ' '.join(str(n) for n in secret.prefix)
            print("Prefix %s" % prefix_str)
        print(adapter.from_int(secret.value, pretty=True))
        print()
        print("====== End Recovered Shamir Secret ======")
    else:
        if verbose:
            print("p = %s" % (prime_str))
        print(sh_fact.format(secret, adapter))


def exit_error(error_str):
    print(_error_msg(error_str))
    exit(1)


def _error_msg(error_str):
    return ''.join(["error: ", error_str])


if __name__ == "__main__":
    cli()
    exit(0)
