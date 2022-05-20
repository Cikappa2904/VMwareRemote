# VMwareRemote

## What is it?
VMwareRemote (temporary name), is a tool written in Python that let's you see a list of your VMware VMs inside a web browser, in order to use them in another computer on the same network.

## What it **ISN'T**?
VMwareRemote DOES NOT let you remote control a running VM, for that you may want to use a VNC Client and the built in VNC Server of VMware Workstation.

## Roadmap 
- [ ] Config File
- [X] Linux Support
- [ ] GUI Installer
- [ ] VM Creation
- [ ] VM Cloning
- [X] VM Editing
- [X] Enabling VNC
- [X] Running VMware Player VMs
- [ ] Decent look
- [ ] Automatic Updater

## Compatibility
- Host OS: Windows, Linux
- VMware: Workstation 16, Player 16 (with limitation)

# How to run
Install Python (either from the MS Store or from the official website) and Pip.\
In a terminal (CMD or PowerShell) type:
```powershell
pip install flask
```
## 1. Using shell script
### **Run start.bat/start.sh from the copied folder**
` `
` `

## 2. Using terminal
Open a terminal in the folder you clone the repo into and run this 2 commands:
### Windows
```powershell
$env:FLASK_APP = "server"
flask run
```
### Linux
```bash
export FLASK_APP=server
flask run
```
Sometimes **flask run** may not work so try:
```powershell
python3 -m flask run
```