import ctypes
from socket import AF_INET


NO_ERROR = 0
ERROR_NOT_ENOUGH_MEMORY = 8
ERROR_INVALID_PARAMETER = 87
ERROR_BUFFER_OVERFLOW = 111
ERROR_NO_DATA = 232
ERROR_ADDRESS_NOT_ASSOCIATED = 1228


class IP_ADAPTER_ADDRESSES(ctypes.Structure):
    pass
PIP_ADAPTER_ADDRESSES = ctypes.POINTER(IP_ADAPTER_ADDRESSES)


IP_ADAPTER_ADDRESSES._fields_ = [
    ('__unused_1', ctypes.c_byte * (4 + 4)),
    ('next', PIP_ADAPTER_ADDRESSES),
    ('adapter_name', ctypes.c_char_p),
    ('__unused_2', ctypes.c_void_p * 4),
    ('dns_suffix', ctypes.c_wchar_p),
    # A lot of other unused fields past here but we are not really interested.
]


GetAdaptersAddresses = ctypes.windll.iphlpapi.GetAdaptersAddresses
GetAdaptersAddresses.argtypes = [
    ctypes.c_ulong,  # Family
    ctypes.c_ulong,  # Flags
    ctypes.c_void_p,  # Reserved
    PIP_ADAPTER_ADDRESSES,  # AdapterAddresses
    ctypes.POINTER(ctypes.c_ulong),  # SizePointer
]
GetAdaptersAddresses.restype = ctypes.c_ulong


def get_suffixed_addresses():
    """Return dict of adapter GUID to local DNS suffix of adapters with local DNS suffixes."""
    # Find required size first
    size = ctypes.c_ulong()
    res = GetAdaptersAddresses(AF_INET, 0, None, None, size)
    if res != ERROR_BUFFER_OVERFLOW:
        raise RuntimeError(ctypes.FormatError(res))

    # Now allocate
    buffer = ctypes.create_string_buffer(size.value)
    addresses = ctypes.cast(buffer, PIP_ADAPTER_ADDRESSES)
    res = GetAdaptersAddresses(AF_INET, 0, None, addresses, size)
    
    if res != NO_ERROR:
        raise RuntimeError(ctypes.FormatError(res))
        
    address_list = []
    while addresses:
        address_list.append(addresses.contents)
        addresses = addresses.contents.next
    
    address_map = {
        info.adapter_name.decode(): info.dns_suffix
        for info in address_list
        if info.dns_suffix
    }
    
    return address_map