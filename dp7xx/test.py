#!/usr/bin/python

import serial

def main():
  s = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
  s.write(b'*IDN?\n')
  x = s.read(100)
  print x

main()

