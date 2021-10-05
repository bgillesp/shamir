# Shamir Secret Sharing for BIP 39 Mnemonic Phrases

## Background: BIP 39 Mnemonic Phrases

Ledger (and others) make use of the BIP 39 standard for representing a cryptographic wallet as a 24-word seed phrase.  For Ledger's usage, this standard represents a 256 bit binary word as a list of 24 English words by doing the following:

1. Let W denote the binary word of 256 bits to be represented
2. Apply the SHA256 hashing algorithm to W to get a hash word H
3. Let H' denote the first 8 bits of H
4. Append H' to the end of W to get the extended binary word W' = WH' of length 264 bits
5. Divide W' into 24 substrings S_i, i = 1, ..., 24, each of length 11 bits
6. Convert each 11-bit substring S_i into an English word by taking the corresponding entry in the standard English wordlist for BIP 39.  The wordlist begins with "abandon, ability, able, about, ..." and has 2^11 = 2048 entries.  Note that the conversion uses 0-based indexing.

In particular, such a seed phrase may be converted back to an original 256 bit binary word by converting each English word to the 11-bit binary word associated with its index in the standard English wordlist, and truncating the last 8 bits.

# Background: Shamir Secret Sharing

We apply Shamir's secret sharing to convert a 24-word seed phrase into a collection of several 24-word seed phrases which may be appropriately combined to reproduce the original seed phrase.  The approach makes use of univariate polynomial interpolation:

1. We produce a shared secret such that any k parts ("shares") may be used to derive the secret.
2. Let p be a large prime number close to 2^256; we will use p = 2^256 - 189, which appears to be the largest prime smaller than 2^256 according to a random list on the internet.  This value of p passes numerous rounds of the Miller-Rabin primality test, and therefore is highly likely to be prime in reality.  Note that this choice of a prime p all but ensures that the random 256-bit binary word W can be properly represented in this field.  If this is not the case, go buy a lottery ticket, or check your random number generator. :)
3. Working over the prime field GF(p) = Z/pZ, let a_1, ..., a_{k-1} be uniform random elements of GF(p), and let f(x) = W + a_1 x + ... + a_{k-1} x^{k-1} be the polynomial with these coefficients.
4. For the desired number of shares, each share is represented by the pair (i, f(i)).  As common knowledge, each shareholder is additionally provided the numbers p and k.
5. A degree k-1 polynomial is determined by any k values, so given any k shares as in the above, a unique interpolating polynomial evaluates to all of the desired points, which must therefore be the original polynomial f above.  This polynomial can be computed, for instance, using Lagrange interpolation.  The secret binary word can then be derived from f by computing W = f(0).
6. Each share of the secret is expressed as a distinct 24-word "seed" phrase by BIP 39, which may be converted back to a 256-bit number as described above.

## Software Usage

Generate shamir secrets for fixed k, n for a given mnemonic phrase

Combine shamir secrets for fixed k for given mnenomic phrase shares


## To do

- (/) unit tests and test coverage framework (!!!!!)
  - tests for CLI
  - tests for adapters
  - use test vector framework
- readme
- license
- specify file for source of randomness (?)
- default separator for prefixes: '.' (?)
- bug: extend with empty string
- does Shamir class do anything as a class?
- (/) proper packaging of binaries
- (X) Propogate nested shares to CLI
- (X) CLI option for random share numbers (specify number of digits)
- (X) group thresholds
- (X) Add functions to combine compatible nested shares
- (X) dependency
- (X) file input for mnemonics
- (X) support for specified polynomial coefficients
- (X) support additional languages
- (X) refactor `prime_modulus` into separate file `shamir.primes`
- (X) refactor `format_mnemonic` function
- (?) test vectors for additional languages in trezor mnemonic library
- (-) CLI option for datatype
- (-) Any additional data types?  Hex, binary, ...


Nested shamir secrets:
- Combine a list of shares:
  - Given a list of shares, combine them up to the depth of their common prefix
- Extend a list of shares:
  - Given an int or a tuple, give a share which extends the pool up to the specified prefix
