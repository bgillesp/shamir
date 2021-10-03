adapter_types = dict()


def register_adapter(adapter_str, adapter_class, kwargs):
    """
    Register an adapter type in a global registry.  For each adapter,
    specifies type string, adapter class, and a dict of additional
    initialization kwargs. Each adapter class is responsible for registring
    relevant adapter types in this dictionary.
    """
    adapter_types[adapter_str] = {
        "class": adapter_class,
        "kwargs": kwargs,
    }


def get_adapter(adapter_str, bitlength):
    if adapter_str in adapter_types:
        a = adapter_types[adapter_str]
        AdapterClass = a['class']
        kwargs = a['kwargs']
        return AdapterClass(bitlength, **kwargs)
    else:
        return None


# def guess_adapter(input, spec_):
#     # binary?

#     # integer?

#     # hex?

#     # bip39?
#     pass

# if type specified, use this to get adapter class and determine bitlength
# if type unspecified, guess by cases
