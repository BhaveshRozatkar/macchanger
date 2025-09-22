# macchanger
README.txt


Contents:

* linux\_macchanger.py   (Python script — for Linux)
* macchanger\_windows.exe (Windows executable — run as Administrator)

Linux (Python):

1. Download linux\_macchanger.py to your Linux machine.
2. Open a terminal in the file's folder.
3. Make it executable (optional) and run:
   chmod +x linux\_macchanger.py
   sudo python3 linux\_macchanger.py
   (If the script requires arguments, run: sudo python3 linux\_macchanger.py <args>)

Windows (Executable):

1. Download macchanger\_windows.exe.
2. Right-click the .exe and choose "Run as administrator" (required for changing NIC settings).
3. Follow on-screen prompts.

Important:

* Changing MAC addresses requires administrative/root permissions.
* Only run code and executables you trust. I am not responsible for misuse.
* If the Python script has extra dependencies, install them with:
  sudo apt update && sudo apt install python3-pip
  sudo pip3 install -r requirements.txt
  (only if a requirements.txt is included)

Contact:

* Issues / questions: open an issue on the GitHub repo.

