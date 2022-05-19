from http.client import NETWORK_AUTHENTICATION_REQUIRED
from flask import Flask, render_template, request
import re
import os
import subprocess
import platform
import errno

app = Flask(__name__)

class VirtualMachine:
    def __init__(self, cpuCores, ram, bios, vncEnabled, vncPort, vmName, vmPath, exists):
        self.cpuCores = cpuCores
        self.ram = ram
        self.bios = bios
        self.vncEnabled = vncEnabled
        self.vncPort = vncPort
        self.vmName = vmName
        self.vmPath = vmPath
        self.exists = exists
    def __repr__(self): 
        return str(self.cpuCores) + ' ' + str(self.ram) + ' ' + self.bios + ' ' + str(self.vncEnabled) + ' ' + str(self.vncPort) + ' ' + self.vmName + ' ' + self.vmPath + ' ' 

cpuSpecs = []
RAMSpecs = []
biosType = []
vmPathList = []
vncPorts = []
vmNames = []
vmList = []
vmArray = []

#TODO: add networking back
vmrunPath = '' 

if 'Linux' in platform.uname():
    import LinuxSpecsCheck as OSSpecsCheck
    hostOS = 'Linux'
    vmrunPath = 'vmrun'
elif 'Windows' in platform.uname():
    import WindowsSpecsCheck as OSSpecsCheck
    hostOS = 'Windows' #Setting this variable here so calling functions is not needed again later in the program

    #vmrun.exe has a different path based on if VMware is Workstation or Player
    if os.path.exists('C:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe'):
        vmrunPath = 'C:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe'
    elif os.path.exists('C:\Program Files (x86)\VMware\VMware Player\\vmrun.exe'):
        vmrunPath = 'C:\Program Files (x86)\VMware\VMware Player\\vmrun.exe'
else:
    raise Exception("Platform not supported: " + platform.uname())

maxRAMSize = OSSpecsCheck.maxRAM()

#Checks for a specific line and gives everything that comes next to the given part of the string
def CheckForSpecs(specString, txt):
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

def GetSlicedVMXPath(path):
    for match in re.finditer(' = "', path):
        slicePosition = match.end()
        slicedPath = path[slicePosition:]
        slicedPath = slicedPath.replace('"\n', "")
    return slicedPath

def SearchVMsInFileWorkstation(txt):
    vmList = ''
    for line in txt:
        lineToSearch = '.config = "'
        lineNotToSearch = '.config = ""'
        if lineToSearch in line and lineNotToSearch not in line and not(re.search('folder.', line)):
            vmPathList.append(GetSlicedVMXPath(line))
            sliceIndex = 0
            for match in re.finditer('.vmx', line):
                vmxPosition = match.start()
                slicedLine = line[:vmxPosition]
                i = 0
                for letter in slicedLine:
                    if slicedLine[-i] == "\\" or slicedLine[-i] == "/":
                        sliceIndex = -i
                        break
                    i+=1
            vmList+=slicedLine[sliceIndex:]
            vmList+="    "
    
    return vmList

def SearchVMsInFilePlayer(txt):
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


@app.route("/")
def main():

    global vmPathList, vmrunPath, vmArray

    #Clearing the content of the arrays in case of a reload of the page since this are global arrays
    vmPathList.clear()
    vmList = ''



    #VMware Workstation
    if platform.system() == 'Windows':
        filePath = os.getenv('APPDATA') + "\VMware\inventory.vmls"
    elif 'Linux' in platform.uname():
        filePath = os.path.expanduser('~') + '/.vmware/inventory.vmls'


    if os.path.exists(filePath):
        f = open(filePath)
        txt = f.readlines()
        vmList+=SearchVMsInFileWorkstation(txt)
        f.close()


    #VMware Player

    if hostOS == 'Windows':
        filePath = os.getenv('APPDATA') + "\VMware\preferences.ini"
    elif hostOS == 'Linux':
        filePath = os.path.expanduser('~') + '/.vmware/preferences.ini'

    if os.path.exists(filePath):
        f = open(filePath)
        txt = f.readlines()
        vmList+=SearchVMsInFilePlayer(txt)
        f.close()
    
    for path in vmPathList:
        if os.path.exists(path):
            f = open(path)
            txt = f.readlines()

            #VMware .vmx files don't have the 'numvcpus=' line when the VM only has 1 core, so we say the VM only has 1 core when we don't find that line
            coreNumber = CheckForSpecs('numvcpus = "', txt)
            if coreNumber == None: coreNumber = '1'

            ramSize = CheckForSpecs('memsize = "', txt)
            vmName = CheckForSpecs('displayName = "', txt)

            #VMware .vmx files don't have the 'firmware=' line when the VM is legacy, so we say the VM is legacy when we don't find that line
            isEFI = True if CheckForSpecs('firmware = "', txt) == 'efi' else False

            #VMware .vmx files don't have the 'RemoteDisplay.vnc.port =' line when using the default port 5900
            vncPort = CheckForSpecs('RemoteDisplay.vnc.port = "', txt)
            if CheckForSpecs('RemoteDisplay.vnc.enabled = "', txt) == 'TRUE':
                vncEnabled = True
                if vncPort == None:
                    vncPort = '5900'
            else:
                vncEnabled = False
                vncPort = None
            tempVM = VirtualMachine(coreNumber, ramSize, isEFI, vncEnabled, vncPort, vmName, path, True)
            vmArray.append(tempVM)
            del tempVM
            f.close()
        else:
            tempVM = VirtualMachine('1','1024',True,False,'5900','',path,False) #Creating a fake VM because the actual one doesn't exist
            vmArray.append(tempVM)
            del tempVM
            f.close()
    
    #print(vmArray)
    return render_template("list.html", vmList=vmList)


@app.route("/specs.html")
def specs():
    #global cpuSpecs, RAMSpecs, vncPorts, vmrunPath
    global vmArray
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    isON = None
    #Checking if the VM is running based on the output of 'vmrun list'
    #print(vmrunPath)
    if vmrunPath!='':
        isON = False
        result = subprocess.run([vmrunPath ,'list'], stdout=subprocess.PIPE)
        result = str(result.stdout)
        list = result.split('\\r\\n')
        for item in list:
            item = item.encode().decode('unicode_escape') #get rid of // 
            if item == vmPathList[x]:
                isON = True
        
    return render_template("specs.html", cpuSpecs1=vmArray[x].cpuCores, RAMSpecs1=vmArray[x].ram, biosType1=vmArray[x].bios, vmPath1=vmPathList[x], vmNumber=vmNumber, vncPort=vmArray[x].vncPort, vmName=vmArray[x].vmName, isON=str(isON), exists=vmArray[x].exists)

@app.route("/runVM")
def runVM():
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    if vmrunPath != '':
        subprocess.run([vmrunPath, '-T', 'ws', 'start', vmPathList[x]])
        return 'VM Run'
    else:
        return 'VM not run'

@app.route("/stopVM")
def stopVM():
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    if vmrunPath != '':
        print(vmrunPath)
        subprocess.run([vmrunPath, '-T', 'ws', 'stop', vmPathList[x]])
        return 'VM Stop'
    else:
        return 'VM not Stop'

@app.route("/edit.html")
def editPage():
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    return render_template("edit.html", vmNumber=vmNumber, hostCPUCores = os.cpu_count(), hostRAM = maxRAMSize)



@app.route("/editVM", methods=['POST'])
def editVM():
    if request.method == 'POST':
        vmNumber = int(request.form.get('vmNumber'))

        cpuCores = request.form.get('cpuCores')
        if not cpuCores.isnumeric(): raise TypeError("cpuCores needs to be an int")

        ram = request.form.get('ram')
        if not ram.isnumeric(): raise TypeError("ram needs to be an int")
        
        vncEnabled = request.form.get('VNC')
        vncPort = request.form.get('VNCPort')
        if not vncPort.isnumeric(): raise TypeError("vncPort needs to be an int")

        f = open(vmPathList[vmNumber], 'r')
        txt = f.readlines()

        trovatoEnabled = False
        trovatoPort = False

        for i in range(len(txt)):
            if "numvcpus" in txt[i]:
                if int(cpuCores)>os.cpu_count(): #Limiting the CPU cores assigned to the VM to the limit of cores in the host system
                    cpuCores = os.cpu_count()
                txt[i] = 'numvcpus = "' + str(cpuCores) + '"\n'
            if "memsize" in txt[i]: #Limiting the RAM assigned to the VM to the RAM in the host system
                if int(ram)>maxRAMSize:
                    ram = maxRAMSize
                txt[i] = 'memsize = "' + str(ram) + '"\n'
            #yes all of this needs to be refactored but i can't be bothered right now
            if vncEnabled == "on":
                if 'RemoteDisplay.vnc.enabled' in txt[i]:
                    txt[i] = 'RemoteDisplay.vnc.enabled = "TRUE"\n'
                    trovatoEnabled = True
                if vncPort != '5900':
                    if "RemoteDisplay.vnc.port" in txt[i]:
                        txt[i] = 'RemoteDisplay.vnc.port = "' + vncPort + '"\n'
                        trovatoPort = True
            else:
                if 'RemoteDisplay.vnc.enabled = "TRUE"' in txt[i]:
                    txt[i]=''
                elif 'RemoteDisplay.vnc.port =' in txt[i]:
                    txt[i]=''

        if vncEnabled == 'on':
            if not trovatoEnabled:
                txt.append('RemoteDisplay.vnc.enabled = "TRUE"\n')
            if not trovatoPort and vncPort != '5900':
                txt.append('RemoteDisplay.vnc.port = "' + vncPort + '"\n')
        f.close()

        f = open(vmPathList[vmNumber], 'w')
        f.write(''.join(line for line in txt))
        f.close()
        return '<script>window.location.href = "/";</script>'

@app.route("/notFound.html")
def notFound():
    return render_template("notFound.html", vmPath=request.args.get('vmPath')) 