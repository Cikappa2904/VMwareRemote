from importlib.resources import path
import subprocess
import os
import platform, sys

def installPackages():
    print('Installing pip (if not already installed): ')
    # Installing pip
    subprocess.run(['python3', '-m', 'ensurepip'])

    # Installing Flask
    print('Installing Flask, if not already installed')
    subprocess.run(['python3', '-m', 'pip', 'install', 'flask'])

    # Installing requests
    print('Installing requests, if not already installed')
    subprocess.run(['python3', '-m', 'pip', 'install', 'requests'])

    # Installing pywin32
    if hostOS == "Windows":
        print('Installing pywin32, if not already installed')
        subprocess.run(['python3', '-m', 'pip', 'install', 'pywin32'])

def chooseBetweenProAndPlayer(config):
        while True:
            choice = input("I have found both VMware Workstation Pro and VMware Workstation Player\n What would you prefer to use?\n 1. VMware Workstation Pro\n 2. VMware Workstation Player")
            if choice == "1":
                config.set("VMware_Configuration", "VMware_Version", "Pro")
                return choice
            elif choice == "2":
                config.set("VMware_Configuration", "VMware_Version", "Player")
                return choice
            else:
                print(choice + " is not a valid option")



def main():
    config = configparser.ConfigParser()
    config.add_section("VMware_Configuration")
   

    # Setting up the config file
    if os.path.exists(workstationPath):
        chooseBetweenProAndPlayer(config)    
        config.set("VMware_Configuration", "VMware_Path", workstationPath)
    elif os.path.exists(playerPath):
        config.set("VMware_Configuration", "VMware_Version", "Player")
        config.set("VMware_Configuration", "VMware_Path", playerPath)
    else:
        print("Unable to find your VMware installation. Maybe it's in a different path?: ")
        while True:
            installPath = input("Please insert a valid installation path for VMware Workstation Pro/Player")
            if (os.path.exists(installPath + "\\vmware.exe")):
                choice = chooseBetweenProAndPlayer(config)
                if choice == 1:
                    config.set("VMware_Configuration", "VMware_Path", installPath + "\\vmware.exe")
                elif choice == 2:
                    config.set("VMware_Configuration", "VMware_Path", installPath + "\\vmplayer.exe")
                break
            elif (os.path.exists(installPath + "\\vmplayer.exe")):
                config.set("VMware_Configuration", "VMware_Version", "Player")
                break

    # Downloading the repo from GitHub
    installPath = input('Where do you want to install VMwareRemote? ("' + os.path.join(os.path.expanduser("~"), 'VMwareRemote") + "')) or os.path.join(os.path.expanduser("~"), "VMwareRemote")
    if not os.path.exists(installPath):
        os.makedirs (installPath)


    repoURL = "https://github.com/Cikappa2904/VMwareRemote/archive/development.zip"
    r = requests.get(repoURL, allow_redirects=True)
    open(os.path.join(tempFolder, 'VMwareRemote.zip'), 'wb').write(r.content)
    with zipfile.ZipFile(os.path.join(tempFolder, 'VMwareRemote.zip'),"r") as zip_ref:
        zip_ref.extractall(tempFolder)

        source_dir = os.path.join(tempFolder, "VMwareRemote-development")
        target_dir = installPath
            
        file_names = os.listdir(source_dir)
            
        for file_name in file_names:
            shutil.move(os.path.join(source_dir, file_name), os.path.join(target_dir, file_name))

    # Creating the .lnk shortcut to the .bat in the Windows Start Menu
    if hostOS == "Windows":
        from win32com.client import Dispatch
        path = os.path.join (tempFolder, "VMwareRemote.lnk")
        target = os.path.join (installPath, "start.bat")
        wDir = installPath

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wDir
        shortcut.save()

        # For whatever reason every Python function didn't want to work on the Start Menu directory so I have to use the Windows Shell for this
        subprocess.run(["move", path, os.path.join(os.getenv('APPDATA'), "Microsoft\Windows\Start Menu\Programs\VMwareRemote.lnk")], shell=True)
    # Creating the .desktop file to show VMware Remote in the Linux DE app list
    elif hostOS == "Linux":
        shPath =  os.path.join(installPath, "start.sh")
        with open(os.path.join(os.path.expanduser("~"), ".local/share/applications/vmwareremote.desktop"), "w") as desktopFile:
            desktopEntry = """[Desktop Entry]
Type=Application
Version=1.0
Name=VMwareRemote
Comment=Tool used to remote control VMware Workstation Player and VMware Workstation Pro
Path= {}
Exec={}
Terminal=true""".format(installPath, shPath)
            desktopFile.write(desktopEntry)

        # Making the script executable       
        st = os.stat(shPath)  
        os.chmod(shPath, st.st_mode | stat.S_IEXEC)
        with open(os.path.join(installPath, "config.ini"), 'w') as configfile:    # save
            config.write(configfile)

    print("Installation completed. You may now run the start script from the installation folder.")

if __name__ == "__main__":
    
    # Checking operating system

    if 'Linux' in platform.uname():
        hostOS = 'Linux'
        workstationPath = "/usr/bin/vmware"
        playerPath = "/usr/bin/vmplayer"
        tempFolder = "/tmp"
    elif 'Windows' in platform.uname():
        hostOS = 'Windows' #Setting this variable here so calling functions is not needed again later in the program   
        workstationPath = os.environ['SYSTEMDRIVE'] + "\Program Files (x86)\VMware\VMware Workstation\\vmware.exe"
        playerPath = os.environ['SYSTEMDRIVE'] + "\Program Files (x86)\VMware\VMware Player\\vmplayer.exe"
        tempFolder = os.environ['TEMP']
    else:
        raise Exception("Platform not supported: " + platform.uname())

    if len(sys.argv) == 1 or sys.argv[1] != "-skipinstall":
        installPackages()
        subprocess.run(["python3", "installer.py", "-skipinstall"])

    if len(sys.argv) > 1 and sys.argv[1] == "-skipinstall":
        import configparser, zipfile, shutil, requests, stat
        main()

