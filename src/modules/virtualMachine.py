from .networkAdapter import *
class VirtualMachine:
    def __init__(self, cpuCores: str, ram: str, bios: bool, vncEnabled: bool, vncPort: str, vmName: str, vmPath: str, exists: bool, network: NetworkAdapter) -> None:
        self.cpuCores = cpuCores
        self.ram = ram
        self.bios = bios
        self.vncEnabled = vncEnabled
        self.vncPort = vncPort
        self.vmName = vmName
        self.vmPath = vmPath
        self.exists = exists
        self.network = network
    def __repr__(self) ->str: 
        return str(self.cpuCores) + ' ' + str(self.ram) + ' ' + self.bios + ' ' + str(self.vncEnabled) + ' ' + str(self.vncPort) + ' ' + self.vmName + ' ' + self.vmPath + ' ' 
