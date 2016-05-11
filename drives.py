import ctypes
import ctypes.wintypes

from config import shares


RESOURCETYPE_DISK = 1
CONNECT_UPDATE_PROFILE = 1
DRIVE_REMOTE = 4

class NETRESOURCE(ctypes.Structure):
    _fields_ = [
        ('scope', ctypes.wintypes.DWORD),
        ('type', ctypes.wintypes.DWORD),
        ('display_type', ctypes.wintypes.DWORD),
        ('usage', ctypes.wintypes.DWORD),
        ('local_name', ctypes.c_char_p),
        ('remote_name', ctypes.c_char_p),
        ('comment', ctypes.c_char_p),
        ('provider', ctypes.c_char_p),
    ]
    
    
def _charp_ascii(unicode):
    return ctypes.c_char_p(bytes(unicode, 'ascii'))
    
    
def get_network_drives():
    GetLogicalDriveStrings = ctypes.windll.kernel32.GetLogicalDriveStringsA

    GetLogicalDriveStrings.restype = ctypes.wintypes.DWORD
    GetLogicalDriveStrings.argtypes = [
        ctypes.wintypes.DWORD,
        ctypes.c_char_p,
    ]
    
    GetDriveType = ctypes.windll.kernel32.GetDriveTypeA
    GetDriveType.argtypes = [ctypes.c_char_p]
    
    WNetGetConnection = ctypes.windll.mpr.WNetGetConnectionA
    WNetGetConnection.restype = ctypes.wintypes.DWORD
    WNetGetConnection.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.wintypes.DWORD),
    ]
    
    res = GetLogicalDriveStrings(0, ctypes.c_char_p())
    buffer = ctypes.create_string_buffer(res)
    res = GetLogicalDriveStrings(res, buffer)
    drive_letters = list(filter(None, buffer.raw.decode().split('\x00')))
    
    # Average str/bytes dance...
    network_drives = []
    for dl in drive_letters:
        drive_type = GetDriveType(_charp_ascii(dl))
        if drive_type == DRIVE_REMOTE:
            dl = dl.replace('\\', '')
            required = ctypes.wintypes.DWORD(0)
            WNetGetConnection(_charp_ascii(dl), None, required)
            buffer = ctypes.create_string_buffer(required.value)
            res = WNetGetConnection(_charp_ascii(dl), buffer, required)
            unc_name = buffer.value.decode()
            if unc_name in shares.values():
                network_drives.append(dl)
            
    return network_drives
    
    
def disconnect_drive(drive_letter):
    WNetCancelConnection = ctypes.windll.mpr.WNetCancelConnection2A
    WNetCancelConnection.restype = ctypes.wintypes.DWORD
    WNetCancelConnection.argtypes = [
        ctypes.c_char_p,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.BOOL,
    ]
    
    # Dunno why CONNECT_UPDATE_PROFILE is required.
    res = WNetCancelConnection(_charp_ascii(drive_letter), CONNECT_UPDATE_PROFILE, 1)

    
def connect_drive(drive_letter, unc):
    WNetAddConnection = ctypes.windll.mpr.WNetAddConnection2A
    WNetAddConnection.restype = ctypes.wintypes.DWORD
    WNetAddConnection.argtypes = [
        ctypes.POINTER(NETRESOURCE),
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.wintypes.DWORD,
    ]
    
    nr = NETRESOURCE()
    nr.type = RESOURCETYPE_DISK
    nr.local_name = _charp_ascii(drive_letter)
    nr.remote_name = _charp_ascii(unc)

    WNetAddConnection(ctypes.pointer(nr), None, None, CONNECT_UPDATE_PROFILE)