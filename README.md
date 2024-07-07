# openEEG2OSC
A simple python venv project plus udev and systemd setup for streaming multiple EEG-SMT data over OSC from a raspberry pi 

- use FT_PROG to configure the FTDI chips inside the EEG-SMT with ordered serial numbers that begin with "EEGSMT"
- install ubuntu server (or whatever, should work with basically any systemd poisoned distro) on raspberry pi and setup os, network, and update stuff 
- install python-venv and a few other python packages with apt (or similar tool)
- `$ python -m venv .openEEG2OSC` to create virtual env... change this name and the `#!` command in openEEG2OSC.py must also change
- `$ source .openEEG2OSC/bin/activate`
- `$ pip install -r requirements.txt`
- `$ sudo cp 99-usb-serial.rules /etc/udev/rules.d/99-usb-serial.rules` to make EEG-SMT /dev symlinks based on their USB serial number...  its up to you to 
- `$ sudo udevadm trigger` or wait until reboot
- in openEEG2OSC.py modify lines 18 and 19 based on your local network
```
TD_IP = "192.168.0.104"
TD_PORT = 36663
EEG_SERIAL_HEADER = "ttyEEGSMT"
```
- to enable start at boot up: 
    - `$ sudo cp openEEG2OSC.service /etc/systemd/system/openEEG2OSC.service`
    - `$ sudo systemctl enable openEEG2OSC`
    - `$ sudo systemctl start openEEG2OSC` or wait until reboot

- code is only tested with the included touchdesigner file...

(![screenshot of touchdesigner program with a connected grid of light in the stars overlaying a brain](https://github.com/exitrip/openEEG2OSC/blob/81d9aa38649766b69be1807ba29baf856142ab52/Screenshot%202024-07-07.png))