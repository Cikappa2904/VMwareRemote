from flask import Flask, render_template, request
import re
import os
import subprocess

app = Flask(__name__)

cpuSpecs = []
RAMSpecs = []
biosType = []
vmPathList = []
vncPorts = []
vmNames = []



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
                    if slicedLine[-i] == "\\":
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
                    if slicedLine[-i] == "\\":
                        sliceIndex = -i
                        break
                    i+=1
            vmList+=slicedLine[sliceIndex:]
            vmList+="    "
    
    return vmList


@app.route("/")
def listVMs():

    global cpuSpecs, RAMSpecs, biosType, vmPathList, vncPorts

    #Clearing the content of the arrays in case of a reload of the page since this are global arrays
    cpuSpecs.clear()
    RAMSpecs.clear()
    biosType.clear()
    vmPathList.clear()
    vncPorts.clear()
    vmList = ''

    appDataPath = os.getenv('APPDATA') + "\VMware\inventory.vmls"
    if os.path.exists(appDataPath):
        f = open(appDataPath)
        txt = f.readlines()
        vmList+=SearchVMsInFileWorkstation(txt)
        f.close()

    appDataPath = os.getenv('APPDATA') + "\VMware\preferences.ini"
    if os.path.exists(appDataPath):
        f = open(appDataPath)
        txt = f.readlines()
        vmList+=SearchVMsInFilePlayer(txt)
        f.close()
    
    for path in vmPathList:
        f = open(path)
        txt = f.readlines()

        #VMware .vmx files don't have the 'numvcpus=' line when the VM only has 1 core, so we say the VM only has 1 core when we don't find that line
        coreNumber = CheckForSpecs( 'numvcpus = "', txt)
        if coreNumber!=None:
            cpuSpecs.append(coreNumber)
        else:
            cpuSpecs.append('1')

        RAMSpecs.append(CheckForSpecs('memsize = "', txt))
        vmNames.append(CheckForSpecs('displayName = "', txt))

        #VMware .vmx files don't have the 'firmware=' line when the VM is legacy, so we say the VM is legacy when we don't find that line
        isEFI = CheckForSpecs('firmware = "', txt)
        if isEFI=='efi':
            biosType.append('efi')
        else:
            biosType.append('legacy')

        #VMware .vmx files don't have the 'RemoteDisplay.vnc.port =' line when using the default port 5900
        vncPort = CheckForSpecs('RemoteDisplay.vnc.port = "', txt)
        if CheckForSpecs('RemoteDisplay.vnc.enabled = "', txt) == 'TRUE':
            if vncPort == None:
                vncPorts.append('5900')
            elif vncPorts != None:
                vncPorts.append(vncPort)
        else:
            vncPorts.append(None)
        f.close()

    print(cpuSpecs, RAMSpecs, biosType, vmPathList, vncPorts)
    return render_template("list.html", vmList=vmList)


@app.route("/specs.html")
def specs():
    global cpuSpecs, RAMSpecs, vncPorts
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    isON = None
    if os.path.exists('C:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe'):
        isON = False
        result = subprocess.run(['C:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe' ,'list'], stdout=subprocess.PIPE)
        result = str(result.stdout)
        list = result.split('\\r\\n')
        print(vmPathList)
        for el in list:
            el = el.encode().decode('unicode_escape')
            print(el)
            if el == vmPathList[x]:
                isON = True
        
    return render_template("specs.html", cpuSpecs1=cpuSpecs[x], RAMSpecs1=RAMSpecs[x], biosType1=biosType[x], vmPath1=vmPathList[x], vmNumber=vmNumber, vncPort=vncPorts[x], vmName=vmNames[x], isON=str(isON))

@app.route("/runVM")
def runVM():
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    os.system('""C:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe" start "' + vmPathList[x] + '""')
    return 'VM Run'

@app.route("/stopVM")
def stopVM():
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    os.system('""C:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe" stop "' + vmPathList[x] + '""')
    return 'VM Stop'