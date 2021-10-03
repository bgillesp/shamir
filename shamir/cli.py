from shamir import Shamir, get_prime, format_prime, version
from shamir.share import ShareFactory, Share
from shamir.adapters import BIP39Adapter
from shamir.adapters.registry import get_adapter
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
              help='Secret to represent as shares, expressed as a'
              ' single string with words separated by spaces.')
@click.option('-t', '--type', default='int',
              help='Specify the data format of the secret.')
@click.option('-b', '--bitlength',
              help='Specify the bitlength of the secret and resulting shares.')
@click.option('-c', '--coefficients', 'coeffs', type=str,
              help='List of explicit coefficients for the Shamir polynomial'
              ' S + c_1 x^1 + ... + c_k x^k, where k is one less than'
              ' THRESHOLD, expressed as a string \'c_1 c_2 ... c_k\' of'
              ' integers separated by spaces.')
@click.option('-l', '--language', 'lang', default='english',
              help='Language list to use for BIP-39 mnemonic phrases.')
@click.option('-p', '--pretty', is_flag=True,
              help='Print output in pretty human-readable format.')
@click.option('-v', '--verbose', is_flag=True,
              help='Print verbose output.')
def generate(threshold, num_shares, secret, type, bitlength,
             coeffs, lang, pretty, verbose):
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

    if coeffs:
        try:
            coeffs = [int(c) for c in coeffs.split()]
        except ValueError:
            exit_error('unable to parse coefficients string')
        if len(coeffs) != threshold - 1:
            exit_error("incorrect number of coefficients "
                       "(expected: %d)" % (threshold - 1))

    try:
        sh_fact = ShareFactory()
        # TODO guess bitlength from input, possibly guess data type
        # mnemonic_phrase = sh_fact.value_string(secret)
        # bitlength = BIP39Adapter.get_bitlength(mnemonic_phrase)
        bitlength = int(bitlength)
        adapter = get_adapter(type, bitlength)

        secret = sh_fact.parse(secret, adapter)
        prime, prime_str = get_prime(bitlength), format_prime(bitlength)

        # TODO modify output to handle nontrivial prefix on input
        # TODO parse output value for verbose output using adapter class

        # bip39 = Mnemonic(lang)
        # secret, mnemonic, bitlength = parse_mnemonic(mnemonic, bip39)
        # prime, prime_str = get_prime(bitlength), format_prime(bitlength)

        shamir = Shamir(prime)
        shares = shamir.generate_pool(
            secret.value, threshold, num_shares, coeffs=coeffs)
        shares = [Share(sh[1], secret.prefix + (sh[0], )) for sh in shares]
        # share_mnemonics = [adapter.from_int(y) for _, y in shares]
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
@click.argument('new_share_number', type=int)
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
        bip39 = Mnemonic(lang)
        shares, share_mnemonics, bitlength = parse_shares(share_strs, bip39)
        threshold = len(share_strs)
        prime = get_prime(bitlength)
        prime_str = format_prime(bitlength)

        shamir = Shamir(prime)
        new_share = shamir.extend_pool(new_share_number, shares)
        new_share_mnemo = bip39.to_mnemonic(
            new_share.to_bytes(bitlength // 8, byteorder='big'))
    except Exception as e:
        exit_error(str(e))

    if pretty:
        print("====== Begin Extend Shamir Secret Pool ======")
        if verbose:
            print("threshold = %d shares" % threshold)
            print("prime_modulus = %s" % prime_str)
        print()
        for share, share_mnemo in zip(shares, share_mnemonics):
            print("------ Share %d ------" % share[0])
            if verbose:
                print("x = %d" % share[0])
            print(format_mnemonic(share_mnemo))
            print()
        print("------ New Share %d ------" % new_share_number)
        print(format_mnemonic(new_share_mnemo))
        print()
        print("====== End Extend Shamir Secret Pool ======")
    else:
        if verbose:
            print("k = %d, p = %s" % (len(shares), prime_str))
        print("%d %s" % (new_share_number, new_share_mnemo))


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
        bip39 = Mnemonic(lang)
        shares, share_mnemonics, bitlength = parse_shares(share_strs, bip39)
        threshold = len(share_strs)
        prime = get_prime(bitlength)
        prime_str = format_prime(bitlength)

        shamir = Shamir(prime)
        secret = shamir.recover_secret(shares)
        secret_mnemo = bip39.to_mnemonic(
            secret.to_bytes(bitlength // 8, byteorder='big'))
    except Exception as e:
        exit_error(str(e))

    if pretty:
        print("====== Begin Recovered Shamir Secret ======")
        logging.info("threshold = %d shares" % threshold)
        logging.info("prime_modulus = %s" % prime_str)
        print()
        for share, share_mnemo in zip(shares, share_mnemonics):
            print("------ Share %d ------" % share[0])
            logging.info("x = %d" % share[0])
            print(format_mnemonic(share_mnemo))
            print()
        print("------ Secret ------")
        print(format_mnemonic(secret_mnemo))
        print()
        print("====== End Recovered Shamir Secret ======")
    else:
        logging.info("k = %d, p = %s" % (len(shares), prime_str))
        print("%s" % secret_mnemo)


def parse_mnemonic(mnemo, bip39):
    mnemo = bip39.expand(mnemo)
    if not bip39.check(mnemo):
        raise ValueError("invalid BIP39 mnemonic specified")
    int_repr = int.from_bytes(bip39.to_entropy(mnemo), byteorder='big')
    bitlength = 32 * (len(str.split(mnemo)) // 3)
    return int_repr, mnemo, bitlength


def parse_shares(share_strs, bip39):
    shares = list()
    mnemos = list()
    bitlength = -1

    for sh_str in share_strs:
        x, mnemo = sh_str.split(maxsplit=1)
        x = int(x)
        int_repr, mnemo, bl = parse_mnemonic(mnemo, bip39)
        if bitlength == -1:
            bitlength = bl
        elif bl != bitlength:
            raise ValueError(
                "shares have different lengths (share %d)" % x)
        shares.append((x, int_repr))
        mnemos.append(mnemo)

    return shares, mnemos, bitlength


def exit_error(error_str):
    print(_error_msg(error_str))
    exit(1)


def _error_msg(error_str):
    return ''.join(["error: ", error_str])


if __name__ == "__main__":
    cli()
    exit(0)
