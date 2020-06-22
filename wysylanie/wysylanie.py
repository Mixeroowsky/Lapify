import serial

ser = serial.Serial('COM6', baudrate=9600, timeout=1)
buffor = ""
while 1:
    data = ser.read()
    if len(data) != 0 and ord(data) >= 32 and ord(data) <= 128:
        buffor += str(data)
    if data == b'\r' or data == b'\n':
        print(buffor)
        buffor = ""
