#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import MT2625
import serial
import sys
#import Olimex-NB-IoT-DevKit

com = serial.Serial("/dev/ttyUSB0", baudrate=115200)

BC = MT2625.MT2625(com, 'Olimex-NB-IoT-DevKit')

BC.connect(9.0)
BC.begin(nvdm=1)
BC.backupNVDM(fname="./bla.dat")
BC.end()
BC.s.close()
sys.exit(0)
