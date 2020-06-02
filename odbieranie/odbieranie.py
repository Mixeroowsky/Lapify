import serial
from datetime import datetime
import crc16
import random
import time
from enum import Enum

packet_num = 0
ser = serial.Serial('COM3', baudrate=9600, timeout=1)


class Type(Enum):
    ping = 0
    proximity = 1
    photocell = 2


class GPS(Enum):
    fixed = 0
    lost = 1
    never = 2


def get_packet_num_increment():
    global packet_num
    packet_num += 1
    if (packet_num > 255):
        packet_num = 0
    return "%02X" % packet_num


def get_timestamp(valid):
    if valid == GPS.fixed:
        now = datetime.now()
        timestamp = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() * 1000
        return "%08X" % int(timestamp)
    elif valid == GPS.lost:
        return "FFFFFFFE"
    elif valid == GPS.never:
        return "FFFFFFFF"


def add_crc(packet):
    crc = crc16.crc16xmodem(packet.encode('utf-8'))
    return packet + str("%04X" % crc)


def generate_packet(type, gps):
    sensor_id = "AABBCCDD"
    tag_id = "EEFFAABB"

    if type == Type.ping:
        packet_type = "01"
        tag_id = "FFFFFFFF"
    elif type == Type.proximity:
        packet_type = "02"
    elif type == Type.photocell:
        packet_type = "03"

    packet = "01" + sensor_id + get_packet_num_increment() + packet_type + tag_id + get_timestamp(gps)
    return add_crc(packet)


i = 1
gps = GPS.fixed
while True:
    photocell = generate_packet(Type.photocell, gps)
    proximity = generate_packet(Type.proximity, gps)
    ping = generate_packet(Type.ping, gps)

    if (i % 20 == 0):
        print(generate_packet(Type.photocell, gps))
        ser.write((photocell + '\r').encode())
        ser.reset_input_buffer()
    elif (i % 10 == 0):
        print(generate_packet(Type.proximity, gps))
        ser.write((proximity + '\r').encode())
        ser.reset_input_buffer()
    else:
        print(generate_packet(Type.ping,gps))
        ser.write((ping + '\r').encode())
        ser.reset_input_buffer()
    time.sleep(random.randint(5, 15) / 10)
    i += 1

    #if i > 10:
      #  gps = GPS.lost
