from .networkAdapter import *
import re
import subprocess
class VirtualMachine:
    def __init__(self, cpuCores: str, ram: str, bios: bool, vncEnabled: bool, vncPort: str, vmName: str, vmPath: str, exists: bool, network: list, encrypted: bool) -> None:
        self.cpuCores = cpuCores
        self.ram = ram
        self.bios = bios
        self.vncEnabled = vncEnabled
        self.vncPort = vncPort
        self.vmName = vmName
        self.vmPath = vmPath
        self.exists = exists
        self.network = network
        self.encrypted = encrypted
    def __repr__(self) ->str: 
        return str(self.cpuCores) + ' ' + str(self.ram) + ' ' + self.bios + ' ' + str(self.vncEnabled) + ' ' + str(self.vncPort) + ' ' + self.vmName + ' ' + self.vmPath + ' ' 

#Checks for a specific line and gives everything that comes next to the given part of the string
def CheckForSpecs(specString: str, txt: str) -> str:
    for line in txt:
        vmSpec = ''
        if specString in line:
            line = line.replace(specString, "")
            for letter in line:
                if letter != '"':
                    vmSpec+=letter
                else:
                    break
            return vmSpec

def GetSlicedVMXPath(path: str) -> str:
    for match in re.finditer(' = "', path):
        slicePosition = match.end()
        slicedPath = path[slicePosition:]
        slicedPath = slicedPath.replace('"\n', "")
    return slicedPath

def SearchVMsInFileWorkstation(txt: str, vmPathList: list)->list:
    #TODO: use DisplayName field instead of the vmx file name
    vmList = ''
    for line in txt:
        lineToSearch = '.config = "'
        lineNotToSearch = '.config = ""'
        if lineToSearch in line and lineNotToSearch not in line and not(re.search('folder.', line)):
            vmPathList.append(GetSlicedVMXPath(line))
            vmNum = line[0:line.find(".")]
            for line2 in txt:
                if vmNum in line2 and 'DisplayName' in line2:
                    vmList+=line2[line2.find('=')+3:len(line2)-2]
                    vmList+="    "
                    break

            # sliceIndex = 0
            # for match in re.finditer('.vmx', line):
            #     vmxPosition = match.start()
            #     slicedLine = line[:vmxPosition]
            #     i = 0
            #     for letter in slicedLine:
            #         if slicedLine[-i] == "\\" or slicedLine[-i] == "/":
            #             sliceIndex = -i
            #             break
            #         i+=1
            # vmList+=slicedLine[sliceIndex:]
            # vmList+="    "
            
    print(vmList)
    return vmList

def SearchVMsInFilePlayer(txt: str, vmPathList: list) -> list:
    #TODO: use DisplayName field instead of the vmx file name
    vmList = ''
    for line in txt:
        lineToSearch = '.filename = "'
        if lineToSearch in line:
            vmPathList.append(GetSlicedVMXPath(line))
            sliceIndex = 0
            for match in re.finditer('.vmx', line):
                vmxPosition = match.start()
                slicedLine = line[:vmxPosition]
                i = 0
                for letter in slicedLine:
                    if slicedLine[-i] == "\\"  or slicedLine[-i] == "/":
                        sliceIndex = -i
                        break
                    i+=1
            vmList+=slicedLine[sliceIndex:]
            vmList+="    "
    return vmList

def RemoveVMNameFromPath(txt: str)->str:
    firstSlash = False
    for i in range(1,len(txt)):
        if txt[-i] == "\\" or txt[-i] == "/":
            if not firstSlash: firstSlash = True
            else: return txt[0:-i]
            
def RemoveFileNameFromPath(txt: str)->str:
    for i in range(1,len(txt)):
        if txt[-i] == "\\" or txt[-i] == "/":
            return txt[0:-i]

def isON(vmrunPath: str, vmPath: str)->bool:
    #Checking if the VM is running based on the output of 'vmrun list'
    result = subprocess.run([vmrunPath ,'list'], stdout=subprocess.PIPE)
    result = str(result.stdout)
    list = result.split('\\r\\n')
    for item in list:
        item = item.encode().decode('unicode_escape') #get rid of // 
        if item == vmPath:
            return True
    return False


            
