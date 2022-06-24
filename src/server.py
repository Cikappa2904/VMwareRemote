from hashlib import new
from flask import Flask, jsonify, render_template, request, abort, Response
import re
import os
import subprocess
import platform
import modules.virtualMachine as VM

app = Flask(__name__)

#global variables
vmPathList = []
vmList = []
vmArray = []


if 'Linux' in platform.uname():
    import modules.LinuxSpecsCheck as OSSpecsCheck
    hostOS = 'Linux'
elif 'Windows' in platform.uname():
    import modules.WindowsSpecsCheck as OSSpecsCheck
    hostOS = 'Windows' #Setting this variable here so calling functions is not needed again later in the program   
else:
    raise Exception("Platform not supported: " + platform.uname())

isWorkstation = OSSpecsCheck.isWorkstationInstalled()
vmrunPath = OSSpecsCheck.vmrunPath()
maxRAMSize = OSSpecsCheck.maxRAM()


@app.errorhandler(400)
def bad_request(e):
    print(e)
    return str(e)


@app.route("/")
def main():

    global vmPathList, vmrunPath, vmArray

    #Clearing the content of the arrays in casexmlHttp of a reload of the page since this are global arrays
    vmPathList.clear()
    vmList = ''
    vmArray.clear()

    #VMware Workstation and VMware Player have different schemas for storing the VM inventory 
    #VMware Workstation
    filePath = OSSpecsCheck.inventory()
    if os.path.exists(filePath):
        f = open(filePath)
        txt = f.readlines()
        vmList+=VM.SearchVMsInFileWorkstation(txt, vmPathList)
        f.close()


    #VMware Player
    filePath = OSSpecsCheck.preferences()
    if os.path.exists(filePath):
        f = open(filePath)
        txt = f.readlines()
        vmList+=VM.SearchVMsInFilePlayer(txt, vmPathList)
        f.close()
    
    for path in vmPathList:
        if os.path.exists(path):
            with open(path) as f:
                txt = f.readlines()
                encrypted = False
                for line in txt: 
                    if 'encryption' in line: encrypted = True

                #VMware .vmx files don't have the 'numvcpus=' line when the VM only has 1 core, so we say the VM only has 1 core when we don't find that line
                coreNumber = VM.CheckForSpecs('numvcpus = "', txt)
                if coreNumber == None: coreNumber = '1'

                ramSize = VM.CheckForSpecs('memsize = "', txt)
                vmName = VM.CheckForSpecs('displayName = "', txt)

                #VMware .vmx files don't have the 'firmware=' line when the VM is legacy, so we say the VM is legacy when we don't find that line
                isEFI = True if VM.CheckForSpecs('firmware = "', txt) == 'efi' else False

                #VMware .vmx files don't have the 'RemoteDisplay.vnc.port =' line when using the default port 5900
                vncPort = VM.CheckForSpecs('RemoteDisplay.vnc.port = "', txt)
                if VM.CheckForSpecs('RemoteDisplay.vnc.enabled = "', txt) == 'TRUE':
                    vncEnabled = True
                    if vncPort == None:
                        vncPort = '5900'
                else:
                    vncEnabled = False
                    vncPort = None

                networkSet = set()
                for line in txt:
                    if "ethernet" in line:
                        networkSet.add(line[0:line.find(".")])
                print(networkSet)
                networkList = []
                for el in networkSet:
                    enabled = False
                    if VM.CheckForSpecs(el + '.present = "', txt) == 'TRUE':
                        enabled = True
                    #VMware .vmx files don't have the 'ethernetX.connectionType =' line when the network type is bridged
                    temp =  VM.CheckForSpecs(el + '.connectionType = "', txt)
                    networkType = 'bridged' if temp == None else temp

                    networkList.append({"enabled": enabled, "networkType": networkType, "name": el})
                tempVM = VM.VirtualMachine(coreNumber, ramSize, isEFI, vncEnabled, vncPort, vmName, path, True, networkList, encrypted)
                vmArray.append(tempVM)
                del tempVM
        else:
            tempVM = VM.VirtualMachine('1','1024',True,False,'5900','',path,False, [], False) #Creating a fake VM because the actual one doesn't exist
            vmArray.append(tempVM)
            del tempVM
            f.close()
    return render_template("list.html", vmNumbers=len(vmArray))


@app.route("/vmOverview")
def overview():
    x = int(request.args.get("vmNumber"))
    if vmArray[x].encrypted == True: return render_template("encrypted.html", vmPath = vmPathList[x]) 
    overviewDict = {
        'cpuSpecs': vmArray[x].cpuCores,
        'RAMSpecs': vmArray[x].ram,
        'biosType': 'efi' if vmArray[x].bios else 'bios',
        'vmName': vmArray[x].vmName
    }
    return overviewDict

@app.route("/specs.html")
def spec():
    x = int(request.args.get("vmNumber"))
    if vmArray[x].encrypted == True: return render_template("encrypted.html", vmPath = vmPathList[x]) 
    return render_template("specs.html", vmNumber=request.args.get("vmNumber"))

@app.route("/spec")
def specs():
    global vmArray
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    isON = None
    if vmrunPath!='':
        isON = VM.isON(vmrunPath, vmPathList[x])
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
            try:
                subprocess.run([vmrunPath, '-T', 'ws', 'start', vmPathList[x]])
            except:
                return 'VM not run'
        else:
            try:
                subprocess.run([vmrunPath, '-T', 'player', 'start', vmPathList[x]])
            except:
                return 'VM not run'
        return 'VM Run'
    else:
        return 'VM not run'

@app.route("/stopVM")
def stopVM():
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    if vmrunPath != '':
        if isWorkstation:
            try:
                subprocess.run([vmrunPath, '-T', 'ws', 'stop', vmPathList[x]])
            except:
                return 'VM not run'
        else:
            try:
                subprocess.run([vmrunPath, '-T', 'player', 'stop', vmPathList[x]])
            except:
                return 'VM not stop'
        return 'VM stop'
    else:
        return 'VM not stop'

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
        if not cpuCores.isnumeric(): abort(400)

        ram = request.form.get('ram')
        if not ram.isnumeric(): abort(400)
        
        vncEnabled = request.form.get('VNC')
        vncPort = request.form.get('VNCPort')
        if not vncPort.isnumeric(): abort(400)

        networkCardNumber = request.form.get('networkCardNumber')
        biosType = request.form.get('biosType')

        #f = open(vmPathList[vmNumber], 'r')
        with open(vmPathList[vmNumber], 'r') as f:
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
            
            for i in range(len(txt)):
                if 'ethernet' in txt[i] and int(txt[i][8:txt[i].find(".")])>int(networkCardNumber)-1:
                    txt[i] = ''

            trovatoEnabled = False
            trovatoPort = False

            for i in range(len(txt)):
                if "numvcpus" in txt[i]:
                    if int(cpuCores)>os.cpu_count(): #Limiting the CPU cores assigned to the VM to the limit of cores in the host system
                        cpuCores = os.cpu_count()
                    txt[i] = 'numvcpus = "' + str(cpuCores) + '"\n'
                elif "memsize" in txt[i]: #Limiting the RAM assigned to the VM to the RAM in the host system
                    if int(ram)>maxRAMSize:
                        ram = maxRAMSize
                    txt[i] = 'memsize = "' + str(ram) + '"\n'
                elif "firmware = " in txt[i]:
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

        #f = open(vmPathList[vmNumber], 'w')
        with open(vmPathList[vmNumber], 'w') as f:
            f.write(''.join(line for line in txt))
            f.close()
        return '<script>window.location.href = "/";</script>'

@app.route("/notFound.html")
def notFound():
    #this is different from error 404 as it means a VM contained in the .vmx file was not found (this sometimes happens also on the VMware UI)
    return render_template("notFound.html", vmPath=request.args.get('vmPath')) 


@app.route("/cloneVM")
def clone():
    vmNumber = request.args.get("vmNumber")
    vmName = request.args.get("vmName")
    newVMPath = VM.RemoveFileNameFromPath(vmPathList[int(vmNumber)]) + "/" + vmName + "/" + vmName
    if isWorkstation:
        listPath = OSSpecsCheck.inventory()
        try:
            subprocess.run([vmrunPath, '-T', 'ws', 'clone', vmPathList[int(vmNumber)], VM.RemoveFileNameFromPath(vmPathList[int(vmNumber)]) + "/" + vmName + "/" + vmName + ".vmx", "full", "-cloneName=" + vmName])
        except:
            return 'VM Not Clone'
    else:
        listPath = OSSpecsCheck.preferences()
        try:
            subprocess.run([vmrunPath, '-T', 'player', 'clone', vmPathList[int(vmNumber)], VM.RemoveFileNameFromPath(vmPathList[int(vmNumber)]) + "/" + vmName + "/" + vmName + ".vmx", "full", "-cloneName=" + vmName])
        except:
            return 'VM Not Clone' 
    with open(listPath) as f:
        txt = f.readlines()
        numberList = set()
        for line in txt:
            if 'vmlist' in line:
                numberList.add(line[6:line.find('.')])
        f = open(listPath, 'w')
        txt.append('vmlist' + str(int(max(numberList))+1) + '.config = "' + newVMPath + '.vmx"\n')
        txt.append('vmlist' + str(int(max(numberList))+1) + '.DisplayName = "' + vmName + '"\n')
        f.write(''.join(line for line in txt))
    return 'VM Clone'
if __name__ == "__main__":
    app.run()