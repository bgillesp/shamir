# Shamir Secret Sharing for BIP 39 Mnemonic Phrases

Various hardware and software wallets for cryptocurrencies make use of the BIP 39 standard for representing a cryptographic wallet as a "seed phrase" consisting of 12 to 24 simple English words.  These words encode the underlying random entropy in an easy-to-read and easy-to-remember format, providing a reasonable improvement in usability and portability over the trivial encoding scheme of "string of 32 to 64 hexadecimal symbols."  However, the seed phrase approach still has the problem of being a single point of failure if used as the entropy for a cryptographic PRNG.

One approach to mitigating this is to use "Shamir secret sharing" to split the seed phrase entropy into multiple parts.  For any positive integers $n$ and $k$, it is possible to produce $n$ "shares" of a secret in such a way that any $k$ shares may be used to reconstitute the original secret, but any collection of fewer than $k$ shares reveals no information about the secret.  This provides a mechanism for backing up a seed phrase in a distributed way, with some resilience against isolated security failures.

This project provides utilities to work with Shamir secret pools on "pure" BIP 39 mnemonic seed phrases, such that both the input secret and the shares of the Shamir pool are represented as standard BIP 39 seed phrases, with minimal additional metadata.  This means that some amount of extra coordination is required to properly manage the shares of a pool (see the usage instructions below for more details), but the design has the advantage of some amount of plausible deniability, in that it is impossible to distinguish between a share of such a Shamir pool and a root secret, both of which are arbitrary BIP 39 seed phrases of a fixed standard length.

**Warning:** This software has not been audited for correctness or security, and so should not be relied upon to provide a secure implementation of its functionality in applications with any value.  Please **do not** type your seed phrase into a general purpose computer without a full understanding of the consequences.


## Installation and Usage

This software uses the `pipenv` tool for Python dependency management.  After installing the `pip` Python package manager on a Unix based system, run

    pip install --user pipenv

After cloning the repository, run the following from the root directory to install the necessary Python dependencies in a local virtual environment:

    pipenv install

To run the utility, either execute

    pipenv run python -m shamir [...]

or first enter a subshell with the appropriate execution environment by running

    pipenv shell
    python -m shamir [...]

For the sake of readability, these instructions will omit the prefix to the `shamir` command for the remainder of this section.


### Generating a Secret Pool

The `shamir` utility has three modes of operation.  First, to create a Shamir secret pool from a root phrase, run

    shamir generate [OPTIONS] N K

The root phrase can be specified from the command line as a string via the `--secret` option, as in

    shamir generate --secret 'WORD1 WORD2 ...' N K

or from standard input, as in

    cat ./bip39-phrase.txt | shamir generate N K

The output of this command is a list of `N` BIP 39 seed phrases in a `K` of `N` Shamir pool, each with an associated "index", an integer representing their position in the Shamir secret sharing polynomial interpolation scheme.  These integers are needed in order to properly recombine the Shamir shares into the original secret.  However, by default, the indices for the pool are chosen to be the integers 1 through `N`, so for small values of `N` and `K` it is feasible to rederive a secret from shares without their associated indices by trial and error.


### Combining Secret Shares

The second mode of operation combines shares from a Shamir secret pool into a root seed phrase.  A share is specified by a string consisting of the associated index of the share, followed by the 12 to 24 words of the corresponding seed phrase (exactly the format produced by the `generate` command), and can again be specified either as part of the command:

    shamir combine --share '1 WORD1 WORD2 ...' --share '2 WORD1 WORD2 ...'

or from standard input:

    cat shares.txt | shamir combine

If at least $k$ shares from a $k$ of $n$ Shamir secret pool are provided to the utility with their correct indices (more than $k$ shares may be provided without issue), then the original root secret will be produced.  Note however that any selection of BIP 39 seed phrases with positive integer indices can be combined with this tool to produce a corresponding "root secret", and in particular, there is no error detection built into the algorithm combining shares in this format.


### Extending a Secret Pool

The third mode of operation extends a previously generated $k$ of $n$ Shamir pool with additional shares, allowing the user to increase the parameter $n$ without invalidating previously generated shares in the pool.  This requires input of a collection of at least $k$ shares from the pool.  Syntax for extending a pool is similar to that for combining shares:

    shamir extend --share '1 WORD1 WORD2 ...' --share '2 WORD1 WORD2 ...' NEW_SHARE_INDEX

or

    cat shares.txt | shamir combine NEW_SHARE_INDEX

The output of these commands is a single new share for the specified Shamir pool which is interoperable with all existing shares, and has the specified index `NEW_SHARE_INDEX`.  The command also allows regeneration of previously generated shares, as the output is deterministic based on input of any quorum of $k$ shares from a given pool.


## Background: BIP 39 Mnemonic Phrases

The [BIP 39 standard](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki) provides a canonical method to represent 128 to 256 bits of random entropy used to derive the keys of a cryptographic wallet in the form of a list of 12 to 24 English words produced by a simple transformation.  For example, a 24-word seed phrase such as those used by the Ledger series of hardware wallets is produced in the following way:

1. Let $W$ denote the binary word of 256 random bits to be represented
2. Apply the SHA256 hashing algorithm to $W$ to get a hash word $H$
3. Let $H'$ denote the first 8 bits of $H$
4. Append $H'$ to the end of $W$ to get the extended binary word $W' = WH'$ of length 264 bits
5. Divide $W'$ into 24 substrings $S_i$, $i = 1, ..., 24$, each of length 11 bits
6. Convert each 11-bit substring $S_i$ into an English word by taking the corresponding entry in the standard English wordlist for BIP 39.  The wordlist begins with "abandon, ability, able, about, ..." and has $2^{11} = 2048$ entries.  Note that the conversion uses 0-based indexing.

In particular, such a seed phrase may be converted back to an original 256 bit binary word by converting each English word to the 11-bit binary sequence associated with its index in the standard English wordlist, and truncating the last 8 bits.


## Background: Shamir Secret Sharing

This project applies the technique of Shamir secret sharing to convert a BIP 39 seed phrase into a collection of several seed phrases of the same length, which may be appropriately combined to reproduce the original seed phrase.  The approach makes use of the mathematical theory of univariate polynomial interpolation.

1. Let $L$ be the bit-length of entropy represented by the input seed phrase, an integer between 128 and 256, and let $p$ be a large prime close to $2^L$.  For this implementation we use the largest prime smaller than $2^L$; for instance, when $L = 256$ we use $p = 2^{256} - 189$.  Let $E$ be the entropy represented by the seed phrase, a random $L$-bit number.  All but a vanishingly small number of values of $E$ can be represented as an integer between $0$ and $p-1$, so our implementation simply throws an error if the seed phrase entropy value lies outside of this range.
2. Working over the prime field $\text{GF}(p) = \mathbb{Z}/p\mathbb{Z}$, choose $a_1$, ..., $a_{k-1}$ uniformly at random from $\text{GF}(p)$, and let $f(x) = E + a_1 x + ... + a_{k-1} x^{k-1}$ be the polynomial with these coefficients.
3. The shares of the resulting pool correspond with $n$ pairs $(i, f(i))$, along with common non-secret parameters $p$ and $k$; each share is expressed as the pair $(i, S_i)$, where $S_i$ is the $L$-bit seed phrase with entropy $f(i)$.
4. A degree $k-1$ polynomial is determined by any $k$ values, so given any $k$ of these shares, a unique interpolating polynomial evaluates to all of the specified points $(i, f(i))$, which must therefore recreate the original polynomial $f$.  This polynomial can be computed, for instance, as a sum of Lagrange interpolating polynomials.
5. The secret entropy can then be retreived from $f$ by computing $E = f(0)$, and the original seed phrase may be derived from this entropy.
