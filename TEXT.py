#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

''' Reset codes '''
RESET= "\033[0m"
RESET_BOLD = "\033[21m"
RESET_DIM = "\033[22m"
RESET_UNDERLINED = "\033[24m"
RESET_BLINK = "\033[25m"
RESET_REVERSE = "\033[27m"
RESET_HIDDEN = "\033[28m"

''' Text format  '''
BOLD = "\033[1m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
REVERSE = "\033[7m"
HIDDEN = "\033[8m"


''' Text Colors '''
DEFAULT = "\033[39m"
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
LGRAY = "\033[37m"
DGRAY = "\033[90m"
LRED = "\033[31m"
LGREEN = "\033[32m"
LYELLOW = "\033[93m"
LBLUE = "\033[94m"
LMAGENTA = "\033[95m"
LCYAN = "\033[96m"
WHITE = "\033[97m"

''' Background Colors '''

BG_DEFAULT = "\033[49m"
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_LGRAY = "\033[47m"
BG_DGRAY = "\033[100m"
BG_LRED = "\033[101m"
BG_LGREEN = "\033[102m"
BG_LYELLOW = "\033[103m"
BG_LBLUE = "\033[104m"
BG_LMAGENTA = "\033[105m"
BG_LCYAN = "\033[106m"
BG_WHITE = "\033[107m"


class TEXT:
	columns = 0
	rows = 0

	def __init__(self):
		rows, columns = os.popen('stty size', 'r').read().split()
		self.rows = int(rows)
		self.columns = int(columns)

	def title(self, message, color=DEFAULT, fill_char='='):
		msg_len = len(message) + 2

		if (msg_len % 2) > 0:
			msg_len += 1

		fill_len = (self.columns - msg_len) / 2
		fill_msg = fill_char * int(fill_len)

		msg =  color + fill_msg + " " + message + " " + fill_msg + RESET + "\n"
		sys.stdout.write(msg)
		sys.stdout.flush()

	def test_line(self, message, color=DEFAULT, fill_char='.', fill_chr_num=None, res_chr_num=11):
		if fill_chr_num == None:
			fill_chr_num = self.columns - len(message) - res_chr_num

		msg = color + message + (fill_char * int(fill_chr_num)) + RESET

		sys.stdout.write(msg)
		sys.stdout.flush()

	def ok(self, message):
		msg = GREEN + "[" + message  + "]" + RESET + "\n"
		sys.stdout.write(msg)
		sys.stdout.flush()

	def error(self, message):
		msg = RED + "[" + message + "]" + RESET + "\n"
		sys.stdout.write(msg)
		sys.stdout.flush()
