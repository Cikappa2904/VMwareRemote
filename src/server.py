from flask import Flask, jsonify, render_template, request
import re
import os
import subprocess
import platform
import json
from modules.networkAdapter import NetworkAdapter, NetworkTypes
from modules.virtualMachine import VirtualMachine

app = Flask(__name__)

vmPathList = []
vmList = []
vmArray = []

#TODO: add networking back

if 'Linux' in platform.uname():
    import modules.LinuxSpecsCheck as OSSpecsCheck
    hostOS = 'Linux'
    vmrunPath = 'vmrun'
    isWorkstation = True #workaround for now
elif 'Windows' in platform.uname():
    import modules.WindowsSpecsCheck as OSSpecsCheck
    hostOS = 'Windows' #Setting this variable here so calling functions is not needed again later in the program

    #vmrun.exe has a different path based on if VMware is Workstation or Player
    if os.path.exists('C:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe'):
        vmrunPath = 'C:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe'
        isWorkstation = True
    elif os.path.exists('C:\Program Files (x86)\VMware\VMware Player\\vmrun.exe'):
        vmrunPath = 'C:\Program Files (x86)\VMware\VMware Player\\vmrun.exe'
        isWorkstation = False
else:
    raise Exception("Platform not supported: " + platform.uname())

maxRAMSize = OSSpecsCheck.maxRAM()

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

def SearchVMsInFileWorkstation(txt: str)->list:
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

def SearchVMsInFilePlayer(txt: str) -> list:
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

    #Clearing the content of the arrays in casexmlHttp of a reload of the page since this are global arrays
    vmPathList.clear()
    vmList = ''
    vmArray.clear()

    #VMware Workstation
    if hostOS == 'Windows':
        filePath = os.getenv('APPDATA') + "\VMware\inventory.vmls"
    elif hostOS == 'Linux':
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
            networkSet = set()
            for line in txt:
                if "ethernet" in line:
                    networkSet.add(line[0:9])
            print(networkSet)
            networkList = []
            for el in networkSet:
                enabled = False
                if CheckForSpecs(el + '.present = "', txt) == 'TRUE':
                    enabled = True
                #VMware .vmx files don't have the 'ethernetX.connectionType =' line when the network type is bridged 
                networkType = 'bridged' if CheckForSpecs(el + '.connectionType = "', txt) == None else CheckForSpecs(el + '.connectionType = "',  txt)
                networkList.append({"enabled": enabled, "networkType": networkType, "name": el})
            tempVM = VirtualMachine(coreNumber, ramSize, isEFI, vncEnabled, vncPort, vmName, path, True, networkList)
            vmArray.append(tempVM)
            del tempVM
            f.close()
        else:
            tempVM = VirtualMachine('1','1024',True,False,'5900','',path,False, []) #Creating a fake VM because the actual one doesn't exist
            vmArray.append(tempVM)
            del tempVM
            f.close()
    
    #print(vmArray)
    return render_template("list.html", vmList=vmList)


@app.route("/specs.html")
def spec():
    return render_template("specs.html", vmNumber=request.args.get("vmNumber"))

@app.route("/spec")
def specs():
    global vmArray
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    isON = None
    #Checking if the VM is running based on the output of 'vmrun list'
    if vmrunPath!='':
        isON = False
        result = subprocess.run([vmrunPath ,'list'], stdout=subprocess.PIPE)
        result = str(result.stdout)
        list = result.split('\\r\\n')
        for item in list:
            item = item.encode().decode('unicode_escape') #get rid of // 
            if item == vmPathList[x]:
                isON = True
    specsDict = {
        'cpuSpecs': vmArray[x].cpuCores, 
        'RAMSpecs': vmArray[x].ram, 
        'biosType':vmArray[x].bios, 
        'vmPath':vmPathList[x], 
        'vmNumber': vmNumber, 
        'vncPort':vmArray[x].vncPort, 
        'vmName':vmArray[x].vmName, 
        'isON':str(isON), 
        'exists':vmArray[x].exists, 
        'networkList':vmArray[x].network
    } 
    return specsDict

@app.route("/runVM")
def runVM():
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    if vmrunPath != '':
        if isWorkstation:
            subprocess.run([vmrunPath, '-T', 'ws', 'start', vmPathList[x]])
        else:
            subprocess.run([vmrunPath, '-T', 'player', 'start', vmPathList[x]])
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
    return render_template("edit.html", vmNumber=vmNumber, hostCPUCores = os.cpu_count(), hostRAM = maxRAMSize, networkCardNumber=len(vmArray[x].network))



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

        networkCardNumber = request.form.get('networkCardNumber')

        f = open(vmPathList[vmNumber], 'r')
        txt = f.readlines()

        for i in range(int(networkCardNumber)):
            foundEnabled = False
            foundType = False
            tempEnabled = request.form.get("ethernet"+str(i)+"_enabled")
            tempType = request.form.get("ethernet"+str(i)+"_type")
            if tempEnabled == 'on':
                for j in range(len(txt)):
                    if "ethernet" + str(i) + ".present" in txt[j]:
                        foundEnabled = True
                        txt[j] = "ethernet" + str(i) + '.present = "TRUE"' + '\n'
            else:
                for j in range(len(txt)):
                    if "ethernet" + str(i) + ".present" in txt[j]:
                        txt[j]=''
            for j in range(len(txt)):
                if "ethernet" + str(i) + ".connectionType" in txt[j]:
                    foundType = True
                    if tempType != "bridged":
                        txt[j] = "ethernet" + str(i) + '.connectionType = "' + tempType + '"\n'
                    else:
                        txt[j] = ''
            if foundEnabled == False and tempEnabled != 'off':
                txt.append("ethernet" + str(i) + '.present = "TRUE"' + '\n')
            if foundType == False and tempType != 'bridged':
                txt.append("ethernet" + str(i) + '.connectionType = "' + tempType + '"\n')



        biosType = request.form.get('biosType')
        

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
            if "firmware = " in txt[i]:
                txt[i] = 'firmware = "' + biosType + '"\n'
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

if __name__ == "__main__":
    app.run()