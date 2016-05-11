import sys
from datetime import datetime

# COM is fucked up
from comtypes.client import CreateObject, GetEvents, GetModule, PumpEvents

from config import config, shares
from drives import connect_drive, disconnect_drive, get_network_drives
from suffixed import get_suffixed_addresses


NETWORKLIST_TLBID = "{DCB00D01-570F-4A9B-8D69-199FDBA5723B}"


class NetworkListManagerEventSink(object):
    RPC_S_CALLPENDING = -2147417835
    TIMEOUT = 5 # seconds

    def __init__(self):
        self.nlm = CreateObject(nlm.NetworkListManager)
        self.connection = GetEvents(self.nlm, self)
        self.at_home = None
        
        self._check_home_network()
        self._log("Done initing, starting pump")
        self._pump()

    # These events give a useless fake network_id. Ignore them and don't attempt to query.
    def NetworkAdded(self, network_id):
        self._log('Network added: {}'.format(network_id))
        self._check_home_network()
        
    def NetworkConnectivityChanged(self, network_id, new_connectivity):
        self._log("Connectivity changed: {} => {}".format(network_id, bin(new_connectivity)))
        self._check_home_network()
        
    def NetworkDeleted(self, network_id):
        self._log("Network deleted: {}".format(network_id))
        self._check_home_network()
        
    def NetworkPropertyChanged(self, network_id, property_change):
        self._log("Network property changed: {} => {}".format(network_id, bin(property_change)))
        self._check_home_network()
        
    def _check_home_network(self):
        # Enumerate everybody
        conns = [conn.QueryInterface(nlm.INetworkConnection) for conn in list(self.nlm.GetNetworkConnections())]
        active_adapters = [str(conn.GetAdapterId()) for conn in conns]
        local_adapters = [
            adapter_id
            for adapter_id, suffix in get_suffixed_addresses().items()
            if suffix == config['general']['local_suffix']
        ]
        
        active_local_adapters = set(local_adapters).intersection(active_adapters)
        at_home = bool(active_local_adapters)
        
        if self.at_home == None:  # We have no idea what the previous state was
            self.at_home = at_home
            return
            
        if self.at_home != at_home:
            network_drives = get_network_drives()
            self._log("Present network drives: {}".format(network_drives))
            if at_home:
                to_add = set(shares.keys()).difference(network_drives)
                self._log("Will add {}".format(to_add))
                for drive in to_add:
                    connect_drive(drive, shares[drive])
            else:
                self._log("Will remove {}".format(network_drives))
                for drive in network_drives:
                    disconnect_drive(drive)
        else:
            self._log("at home state didn't change, doing nothing")
        
        self.at_home = at_home
        
    def _log(self, message):
        print("{}: {}".format(str(datetime.now()), message))
        
    def _pump(self):
        while True:
            try:
                PumpEvents(self.TIMEOUT)  # timeout, required for some reason
            except OSError as ex:
                if not NetworkListManagerEventSink.RPC_S_CALLPENDING == ex.winerror:
                    raise
            except KeyboardInterrupt:  # Get the FUCK out
                sys.exit()
        
# Thanks for the song and dance, comtypes
if __name__ == "__main__":
    GetModule((NETWORKLIST_TLBID, 1, 0))
    from comtypes.gen import NETWORKLIST as nlm
    NetworkListManagerEventSink()