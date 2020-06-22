import serial
from datetime import datetime
import crc16
import random
import time
from enum import Enum

packet_num = 0

ser = serial.Serial('COM5', baudrate=9600, timeout=1)



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


def generate_packet_start(type, gps):
    sensor_id = "AABBCCDD"
    tag_id = "EEFFAABB"
    packet_type = ""

    if type == Type.ping:
        packet_type = "01"
        tag_id = "FFFFFFFF"
    elif type == Type.proximity:
        packet_type = "02"
    elif type == Type.photocell:
        packet_type = "03"

    packet = "01" + sensor_id + get_packet_num_increment() + packet_type + tag_id + get_timestamp(gps)
    return add_crc(packet)


def generate_packet_checkpoint(type, gps):
    sensor_id = "AABBCCEE"
    tag_id = "EEFFAABB"
    packet_type = ""

    if type == Type.ping:
        packet_type = "01"
        tag_id = "FFFFFFFF"
    elif type == Type.proximity:
        packet_type = "02"
    elif type == Type.photocell:
        packet_type = "03"

    packet = "01" + sensor_id + get_packet_num_increment() + packet_type + tag_id + get_timestamp(gps)
    return add_crc(packet)


def generate_packet_finish(type, gps):
    sensor_id = "AABBCCFF"
    tag_id = "EEFFAABB"
    packet_type = ""

    if type == Type.ping:
        packet_type = "01"
        tag_id = "FFFFFFFF"
    elif type == Type.proximity:
        packet_type = "02"
    elif type == Type.photocell:
        packet_type = "03"

    packet = "01" + sensor_id + get_packet_num_increment() + packet_type + tag_id + get_timestamp(gps)
    return add_crc(packet)

def generate_packet2(type, gps):
    sensor_id = "AACCCCDD"
    tag_id = "EECCAABB"

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
j = 1
gps = GPS.fixed
while True:
    # photocell = generate_packet(Type.photocell, gps)
    proximity_start = generate_packet_start(Type.proximity, gps)
    ping_start = generate_packet_start(Type.ping, gps)
    proximity_checkpoint = generate_packet_checkpoint(Type.proximity, gps)
    ping_checkpoint = generate_packet_checkpoint(Type.ping, gps)
    proximity_finish = generate_packet_finish(Type.proximity, gps)
    ping_finish = generate_packet_finish(Type.ping, gps)
    reset = False
    race = True

    if i == 10 and race is True:
        print(f"\nPakiety {j} (start):")
        print(generate_packet_start(Type.proximity, gps))
        ser.write((proximity_start + '\r').encode())
        ser.reset_input_buffer()
        time.sleep(0.2)
        print(generate_packet_checkpoint(Type.ping,gps))
        ser.write((ping_checkpoint + '\r').encode())
        ser.reset_input_buffer()
        time.sleep(0.2)
        print(generate_packet_finish(Type.ping,gps))
        ser.write((ping_finish + '\r').encode())
        ser.reset_input_buffer()


    elif i == 20 and race is True:

        print(f"\nPakiety {j} (checkpoint):")
        print(generate_packet_start(Type.ping,gps))
        ser.write((ping_start + '\r').encode())
        ser.reset_input_buffer()
        time.sleep(0.2)
        print(generate_packet_checkpoint(Type.proximity, gps))
        ser.write((proximity_checkpoint + '\r').encode())
        ser.reset_input_buffer()
        time.sleep(0.2)
        print(generate_packet_finish(Type.ping,gps))
        ser.write((ping_finish + '\r').encode())

    photocell2 = generate_packet2(Type.photocell, gps)
    proximity2 = generate_packet2(Type.proximity, gps)
    ping2 = generate_packet2(Type.ping, gps)



    ser.reset_input_buffer()



