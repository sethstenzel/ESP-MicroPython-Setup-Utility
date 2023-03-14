import serial.tools.list_ports
from serial import SerialException
import time

def get_com_ports():
    available_ports = serial.tools.list_ports.comports()
    ports = list()
    for port, desc, hwid in sorted(available_ports):
        ports.append((port, desc, hwid))
    return ports

def port_is_avaiable(com_port, baud=11500, timeout=1):
    try:
        serial_con = serial.Serial(com_port, baud, timeout=1)
        available = serial_con.isOpen()
        serial_con.close()
        time.sleep(0.5)
        return available
    except SerialException:
        return False