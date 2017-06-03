#/usr/bin/env python

import serial
import sys

port = '/dev/ttyACM0'
baud = 115200

def main():
    ser = serial.Serial(port, baud, timeout=0.1)
    print("STARTED")
    try:
        for line in to_lines(ser):
            print(line)
            sys.stdout.flush()
    except KeyboardInterrupt:
        ser.close()
        print("CLOSED")

def to_lines(ser):
    data = b""
    while True:
        data += ser.read(10)
        splited = data.split(b'\r\n', 1)
        while len(splited) > 1:
            line = splited[0]
            yield line.decode()
            data = splited[-1]
            splited = data.split(b'\r\n', 1)

if __name__ == '__main__':
    main()
