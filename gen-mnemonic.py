from mnemonic import Mnemonic


def main():
    bip39 = Mnemonic("english")
    test_value = bytes((8 * [0]) + [1, 2, 3, 4, 5, 6, 7, 8])
    # test_value = bytes((16 * [0]) + [])
    # mnemo = bip39.to_mnemonic(test_value)
    mnemo = bip39.generate(128)
    # 'abandon abandon abandon abandon abandon abandon advice document advice choice limb awesome'
    print(mnemo)


if __name__ == "__main__":
    main()
