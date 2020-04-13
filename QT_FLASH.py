#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import sys
import QP
import MT2625
import argparse
import os.path
from os.path import join
from TEXT import *

msg = TEXT()

def res(cond=False, ok_txt="", err_txt=""):
    if cond:
        msg.ok(ok_txt)
    else:
        msg.error(err_txt)

''' Argument Parser '''
usage_str =  "\033[36mbla.py [--backup] --cfg <cfg_file>\n       bla.py [--backup] <app_file>\033[0m"
parser = argparse.ArgumentParser(usage=usage_str)
parser.add_argument("--backup", help="Backup NVDM", action="store_true")
parser.add_argument("--cfg", help="Loads cfg instead of app file", action="store_true")
parser.add_argument("fp", help="Full path to app-file or cfg file")

parser.add_argument("port", help="COM port")
args = parser.parse_args()

''' Initialization '''
com = serial.Serial(args.port, baudrate=115200)
BC = MT2625.MT2625(com, 'Olimex-NB-IoT-DevKit')

if args.cfg:
	''' CFG parser'''
	ql = QP.QuectelParser(args.fp)
	ql.parse_data()

	fw_path = os.path.dirname(args.fp)

	BL_name = join(fw_path, ql.getData("BOOTLOADER")["file"])
	BL_addr = ql.getData("BOOTLOADER")["begin_address"]
	ROM_name = join(fw_path, ql.getData("ROM")["file"])
	ROM_addr = ql.getData("ROM")["begin_address"]
	APP_name = join(fw_path, ql.getData("APP")["file"])
	APP_addr = ql.getData("APP")["begin_address"]

	''' Begin flashing... '''
	BC.connect(9.0)

	if args.backup:
	    msg.title("NVDM BACKUP")
	    BC.begin(nvdm=1)
	    BC.backupNVDM()
	else:
	    BC.begin()

	if APP_name:
		msg.title("APPLICATION UPLOAD")
		msg.test_line("Upload application")
		result = BC.uploadApplication(APP_addr,"bc66", APP_name)
		res(result, "DONE", "FAILED")

	if BL_name:
		msg.title("BOOTLOADER UPLOAD")
		msg.test_line("Upload bootloader")
		result = BC.uploadApplication(BL_addr,"bc66", BL_name)
		res(result, "DONE", "FAILED")

	if ROM_name:
		msg.title("ROM UPLOAD")
		msg.test_line("Uploading ROM")
		result = BC.uploadApplication(ROM_addr,"bc66", ROM_name)
		res(result, "DONE", "FAILED")

	BC.end()
	BC.s.close()

else:
	BC.connect(9.0)
	if args.backup:
		BC.begin(nvdm=1)
		BC.backupNVDM()
	else:
		BC.begin()

	msg.title("APPLICATION UPLOAD")
	msg.test_line("Upload application")
	result = BC.uploadApplication(0x8292000,"bc66", args.fp)
	res(result, "DONE", "FAILED")

sys.exit(0)
