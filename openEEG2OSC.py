#!/home/gamma/openEEG2OSC/.openEEG2OSC/bin/python

import sys
from pathlib import Path
from typing import Dict, List
import yaml

from pyudev import Context, Monitor, MonitorObserver
        
import serial as s
from serial.tools import list_ports

import numpy as np

from pythonosc import udp_client
 
#constants maybe loaded from yaml config in the future
TD_IP = "192.168.0.104"
TD_PORT = 36663
NUM_CHAN = 2 #per EEG

#Global
reinit_flag = False

def load_configs(args) -> Dict:
    try:
        with open(args.config_path, 'r') as file_pointer:
            config = yaml.safe_load(file_pointer)

        # arrange and check configs here

        return config
    except Exception as err:
        # log errors
        print(err)
        if err == "Really Bad":
            raise err

        # potentionally return some sane fallback defaults if desired/reasonable
        sane_defaults = []
        return sane_defaults
    
def init_eegs() -> List :
    #use FT_PROG from FTDI to set iSerial field to EEGSMT#### 
    # and udev rules to create symlinks in /dev/ttyEEGSMT####
    # the rest of the program depends on fixed alphanumeric 
    # ordering in the serdevs list
    p = Path("/dev/")
    serdevs = list(p.glob("ttyEEGSMT*"))

    eegs = []
    for i in range(len(serdevs)):
        try:
            #open serial port and OSC msg builder into array, inside named dict
            print(f"Opening {str(serdevs[i])}")
            eegs.append(s.Serial(str(serdevs[i]), baudrate= 57600))
        except s.serialutil.SerialException as e:
            print("Failed.")
            #TODO maybe exit here
            print(e)
    return eegs    

def reinit_eegs(action, device):
    global reinit_flag
    #print('{0} - {1}'.format(action, device.device_node))
    reinit_flag = True
        
def main() -> int:
    global reinit_flag
    # config = load_configs(args)
    eegs = init_eegs()
    #main exception structure, all exceptions should fail out of application
    try:
        #start udeve monitor for late comer / haut plugs
        ctx = Context()
        monitor = Monitor.from_netlink(ctx)
        monitor.filter_by(subsystem='usb')
        observer = MonitorObserver(monitor, reinit_eegs)
        observer.start()

        #TODO try catch errors on osc stuff?
        oscClient = udp_client.SimpleUDPClient(TD_IP, TD_PORT)
        
        #begin transmitting all serial data over OSC
        
        #round robin messages from all open eegs
        while(True):
            #did the udev observer detect a new USB connection?
            #  this will brick things if a USB is loose / dying
            if reinit_flag:
                print("reinit triggered by udev un/hautplug")
                for e in eegs:
                    if e.isOpen():
                        e.close()
                eegs = init_eegs()
                reinit_flag = False
            #loop exceptions cant try to recover operations
            try:
                dBuf = np.zeros((len(eegs), NUM_CHAN), dtype=np.int16)
                dIndx = 0
                #loop through each eeg and parse the oldest packet from serial port buffer
                for e in eegs:
                    #double check that serial device is still open
                    if e.isOpen():
                        if e.inWaiting() > 0:
                            m = e.read_until(b'\xa5\x5a\x02')
                            #if we don't have a complete packet, drop it and read the next
                            if len(m) < 17:
                                print (f"dropped partial packet len: {len(m)}")
                                m = e.read_until(b'\xa5\x5a\x02')
                            d = np.frombuffer(m[1:], dtype=np.dtype('>i2'), count=NUM_CHAN).copy()
                            d -= (2**9)
                            #create an empty message and add the two channels
                            oscClient.send_message(f"/eeg/{e.port[-2:]}", 
                                                    (float(d[0]+dBuf[dIndx][0]) / (2**10), 
                                                    float(d[1]+dBuf[dIndx][1]) / (2**10))
                                                    )
                            np.copyto(dBuf[dIndx], d)
                            dIndx = dIndx + 1
                            if dIndx >= len(eegs):
                                dIndx = 0
                    else:
                        # a serial port is closed and was expected to be open
                        try:
                            print(f"tried re-opening {e.port}")
                            e.open()
                        except Exception as e:
                            print(e)
            # likely a serial port died
            # udev observer should trigger reinit 
            except Exception as e:
                print(e)
            
        #try: While(True): forever until a fatal exception

    except KeyboardInterrupt:
        print("Aborted manually.", file=sys.stderr)
        #close serial ports
        for e in eegs:
            if e.isOpen():
                e.close()
        return 1

    except Exception as err:
        # (in real code the `except` would probably be less broad)
        # Turn exceptions into appropriate logs and/or console output.

        # log err and close serial ports
        print("An unhandled exception crashed the application!", err)
        for e in eegs:
            if e.isOpen():
                e.close()
        # non-zero return code to signal error
        # Can of course be more fine grained than this general
        # "something went wrong" code.
        return 1

    return 0  # success


# __main__ support is still here to make this file executable without
# installing the package first.
if __name__ == "__main__":
    sys.exit(main())
