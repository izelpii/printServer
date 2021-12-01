import os
import cups
import time
import subprocess
from dothat import lcd
from dothat import backlight
import fcntl
import socket
import struct
import urllib2
import logging
from datetime import datetime

myPrinter = "HP_LaserJet_1320_series"
testURL = "http://www.google.com"
kasaIP = "10.1.5.153"
cupsON = 0
logging.basicConfig(filename="/opt/printServer/checkCups.log",
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')


def internet_on():
    try:
        urllib2.urlopen(testURL, timeout=2)
        return("Online")
    except urllib2.URLError as err: 
        logging.info((str(err)))
        return("Disconnected")

def get_addr(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])
    except IOError:
        return 'Not Found!'

def print_lcd_status():
    online = internet_on()
    wlan0 = get_addr('wlx00223fa9253b')
    #eth0 = get_addr('eth0')
    
    lcd.clear()
    backlight.off()

    lcd.set_cursor_position(0,0)
    lcd.write('{}'.format(online))
    
    lcd.set_cursor_position(0,1)
    if wlan0 != 'Not Found!':
        lcd.write(wlan0)
    else:
        lcd.write('wlan0 {}'.format(wlan0))
    
    lcd.set_cursor_position(0,2)
    now = datetime.now()
    
    dt_string = now.strftime("%d/%m/%y %H:%M")
    lcd.write(dt_string)


def run_light():
    power = 0.0
    backlight.set_graph(abs(1))
    time.sleep(0.2)
    backlight.set_graph(abs(0))
    time.sleep(0.1)
    backlight.set_graph(abs(1))
    time.sleep(0.2)
    backlight.set_graph(abs(0))
    lcd.clear()
    backlight.rgb(0,255,0)
    lcd.set_cursor_position(0,0)
    lcd.write("Printing...")
    lcd.set_cursor_position(0,1)
    lcd.write("HP 1320")
    

def clearScreen():
    lcd.clear()
    backlight.off()
    backlight.set_graph(0)


def execute(command):
    result = ""
    try:
        result = subprocess.check_output(command,shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
    return(result)

def turnOnPrinter():
    myCommand = "kasa --host "+kasaIP+" --plug on"
    status = execute(myCommand)
    
def turnOffPrinter():
    myCommand = "kasa --host "+kasaIP+" --plug off"
    status = execute(myCommand)


def getPrinterStatus():
    result = ""
    myCommand = "kasa --host "+kasaIP+" --plug state"
    status = execute(myCommand)
    lines = status.splitlines()
    for line in lines:
        if "Device state" in line:
            result = line[15:18]
    return(result)


def checkPort():
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    location = ("10.1.1.130", 631)
    result_of_check = a_socket.connect_ex(location)

    if result_of_check == 0:
       logging.info("CUPS is online")
       return(1)
    else:
       logging.info("Turning on CUPS") 
       clearScreen()
       backlight.rgb(1,41,64)
       lcd.set_cursor_position(0,1)
       lcd.write("Starting CUPS")
       execute("sudo /usr/bin/systemctl restart cups")
       time.sleep(2)
       return(0)
    a_socket.close()

while(cupsON==0):
    cupsON = checkPort()


conn = cups.Connection()
timeOutCounter = 0
printerIsON=0
while 1==1:
    printers = conn.getPrinters()
    myStatus = printers[myPrinter]["printer-state"]
    
    if(getPrinterStatus()=="ON"):
        printerIsON=1
    else:
        printerIsON=0

    if(myStatus == 4):
        logging.info("Printing")
        if(printerIsON==0):
            run_light()
            turnOnPrinter()
        timeOutCounter = 0
    if(myStatus == 3):
        print_lcd_status()
        timeOutCounter = timeOutCounter+1

    if(timeOutCounter > 60):
        if(printerIsON ==1):
            logging.info("Turning off printer")
            turnOffPrinter()
        timeOutCounter = 0
    time.sleep(1)
