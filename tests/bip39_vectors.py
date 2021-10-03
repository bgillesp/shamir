from mnemonic import Mnemonic
from shamir import Shamir, get_prime
import random


_seed_phrase_sizes = [16, 20, 24, 28, 32]
_seed_phrase_langs = Mnemonic.list_languages()


def random_vector(seed=None, random_lang=False):
    if seed is not None:
        random.seed(seed)
    size = random.choice([16, 20, 24, 28, 32])
    prime = get_prime(8 * size)
    shamir = Shamir(prime)

    secret = random.getrandbits(8 * size)
    if random_lang:
        lang = random.choice(_seed_phrase_langs)
    else:
        lang = "english"

    bip39 = Mnemonic(lang)
    mnemonic = bip39.to_mnemonic(secret.to_bytes(size, byteorder='big'))
    threshold = random.randint(1, 3) + random.randint(1, 3)
    num_shares = threshold + random.randint(1, 3)
    coeffs = [random.randint(0, prime - 1) for i in range(threshold - 1)]

    shares = shamir.generate_pool(
        secret, threshold, num_shares, coeffs=coeffs)
    extra_share = shamir.extend_pool(
        random.randint(10, 1000), shares)
    share_mnemonics = list()
    for _, y in shares:
        mnemo = bip39.to_mnemonic(
            y.to_bytes(size, byteorder='big'))
        share_mnemonics.append(mnemo)
    # extra_share_mnemonic = bip39.to_mnemonic(
    #     extra_share[1], byteorder='big')

    vector = dict()
    vector['secret'] = mnemonic
    vector['coefficients'] = coeffs
    vector['shares'] = {sh[0]: m for sh, m in zip(shares, share_mnemonics)}
    # vector['extra_shares'] = {extra_share[0]: extra


vectors = [
    {
        'secret':
            'abandon  abandon  abandon  abandon  abandon  abandon  '
            'abandon  abandon  abandon  abandon  abandon  about    ',
        'coefficients': [0],
        'shares': {
            1:
            'abandon  abandon  abandon  abandon  abandon  abandon  '
            'abandon  abandon  abandon  abandon  abandon  about    ',
            2:
            'abandon  abandon  abandon  abandon  abandon  abandon  '
            'abandon  abandon  abandon  abandon  abandon  about    ',
            3:
            'abandon  abandon  abandon  abandon  abandon  abandon  '
            'abandon  abandon  abandon  abandon  abandon  about    ',
        },
        'extra_shares': {
            4:
            'abandon  abandon  abandon  abandon  abandon  abandon  '
            'abandon  abandon  abandon  abandon  abandon  about    ',
        },
    },
    {
        'secret':
            'abandon  abandon  abandon  abandon  abandon  abandon  '
            'abandon  abandon  abandon  abandon  abandon  about    ',
        'coefficients': [
            21201381435957109336073469886064098126,
            58482264874044281995270875978615217265,
        ],
        'shares': {
            1:
            'media    glow     cause    tooth    tonight  flip    '
            'art      female   hawk     spin     clown    slush   ',
            2:
            'bundle   unable   ask      lesson   slow     stick   '
            'invest   cause    cable    uniform  motor    erode   ',
            3:
            'apart    hard     bone     dance    sauce    dumb    '
            'broccoli invest   tongue   island   title    mushroom',
            4:
            'evolve   surprise embrace  annual   salmon   photo   '
            'about    enable   rescue   home     casual   object  ',
            5:
            'tuition  divorce  online   walnut   similar  visual  '
            'canyon   ozone    oblige   speed    famous   grape   ',
        },
        'extra_shares': {
            10000:
            'food     rebel    weekend  oval     gadget   small   '
            'rally    reveal   kite     announce left     legend  ',
        },
    }
]
