############################################################################
 #
 # Mediatek MT2625 Flash Utility ver 1.00
 #
 #   Copyright (C) 2019 Georgi Angelov. All rights reserved.
 #   Author: Georgi Angelov <the.wizarda@gmail.com> WizIO
 #
 # Redistribution and use in source and binary forms, with or without
 # modification, are permitted provided that the following conditions
 # are met:
 #
 # 1. Redistributions of source code must retain the above copyright
 #    notice, this list of conditions and the following disclaimer.
 # 2. Redistributions in binary form must reproduce the above copyright
 #    notice, this list of conditions and the following disclaimer in
 #    the documentation and/or other materials provided with the
 #    distribution.
 # 3. Neither the name WizIO nor the names of its contributors may be
 #    used to endorse or promote products derived from this software
 #    without specific prior written permission.
 #
 # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 # "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 # LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 # FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 # COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 # INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 # BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 # OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 # AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 # LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 # ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 # POSSIBILITY OF SUCH DAMAGE.
 #
 ############################################################################
 # Dependency:
 #      https://github.com/pyserial/pyserial/tree/master/serial
 ############################################################################
from __future__ import print_function
import os, sys, struct, time, inspect
import os.path
from os.path import join
from serial import Serial
from binascii import hexlify

DEBUG = False

NONE                        =''
CONF                        =b'\x69'
STOP                        =b'\x96'
ACK                         =b'\x5A'
NACK                        =b'\xA5'

CMD_READ16                  =b'\xD0'
CMD_READ32                  =b'\xD1'
CMD_WRITE16                 =b'\xD2'
CMD_WRITE32                 =b'\xD4'
CMD_JUMP_DA                 =b'\xD5'
CMD_SEND_DA                 =b'\xD7'
CMD_SEND_EPP                =b'\xD9'

DA_READ                     =b'\xD6'
DA_FINISH                   =b'\xD9'
DA_NWDM_INFO                =b'\x80'
DA_P2A                      =b'\xB0'
DA_A2P                      =b'\xB1'
DA_WRITE_ADDR               =b'\xB2'

def DBG(s):
    if DEBUG:
        print(s)

def ERROR(message):
    print("\n\033[31mERROR: {}".format(message) )
    time.sleep(0.1)
    exit(2)

def ASSERT(flag, message):
    if flag == False:
        ERROR(message)

def PB_BEGIN(text):
    if DEBUG == False:
        print('\033[94m' + text, end='')

def PB_STEP():
    if DEBUG == False:
        print('.', end='')

def PB_END():
    if DEBUG == False:
        print("> DONE")

def hexs(s):
    return hexlify(s).decode("ascii").upper()

def rem_zero(str):
    r = ""
    for i in range(len(str)):
        if i % 2 != 0: r = r + str[i]
    return r

def checksum(data, c = 0):
    for i in range(len(data)):
        c += ord(data[i])
    return c

class MT2625:
    DEVICE = {
        "bc66": {
               "max_size"  : 0x00032000
        }
    }

    DA = { #MT2625.bin
        "0x8100.0": {
            "1":{"offset":0x00000, "size":0X00CB5, "address":0x04015000},
            "2":{"offset":0x00CB5, "size":0X0BCA4, "address":0x04001000},
            "3":{"offset":0x0C959, "size":48}
        },
        "0x8300.0": {
            "1":{"offset":0x0D019, "size":0X00CB5, "address":0x04015000},
            "2":{"offset":0x0DCCE, "size":0X0BCA4, "address":0x04001000},
            "3":{"offset":0x19972, "size":48}
        }
    }

    def __init__(self, ser, auto_reset):
        self.s = ser
        self.dir = os.path.dirname( os.path.realpath(__file__) )
        self.nvdm_address = 0
        self.nvdm_length = 0
        self.auto_reset = auto_reset

    def read(self, read_size = 0):
        r = ""
        if read_size > 0:
            r = self.s.read(read_size)
            if DEBUG:
                print("<-- {}".format(hexs(r)))
            else:
                PB_STEP()
            #ASSERT(len(r) == read_size, "read size")
        return r

    def send(self, data, read_size = 0):
        r = ""
        if len(data):
            if DEBUG:
                print("--> {}".format(hexs(data)))
            else:
                PB_STEP()
            self.s.write(data)
        return self.read(read_size)

    def cmd(self, cmd, read_size = 0):
        r = ""
        size = len(cmd)
        if size > 0:
            ASSERT(self.send(cmd, size) == cmd, "cmd echo")
        return self.read(read_size)

    def boot(self, timeout):
        self.s.timeout = 0.01
        step = 0
        if self.auto_reset:
            # Toggle PWRKEY for 600ms
            self.s.dtr = 0
            time.sleep(0.6)
            self.s.dtr = 1
            # Toggle RESET for 100ms
            self.s.rts = 0
            time.sleep(0.1)
            self.s.rts = 1
        PB_BEGIN( 'Wait for Power ON or Reset module <' )
        while True:
            if step % 10 == 0: PB_STEP()
            step += 1
            self.s.write( b"\xA0" )
            if self.s.read(1) == b"\x5F":
                self.s.timeout = 1.0
                self.s.write(b"\x0A\x50\x05")
                r = self.s.read(3)
                if r == b"\xF5\xAF\xFA":
                    break
                else: ERROR("Boot answer")
            timeout -= self.s.timeout
            if timeout < 0:
                ERROR("Boot timeout")

    def da_read16(self, addr, sz=1):
        r = self.cmd(CMD_READ16 + struct.pack(">II", addr, sz), (sz*2)+4)
        return struct.unpack(">" + sz * 'HHH', r)

    def da_write16(self, addr, val):
        r = self.cmd(CMD_WRITE16 + struct.pack(">II", addr, 1), 2)
        r = self.cmd(struct.pack(">H", val), 2)

    def da_read(self, address, size=4096, block=4096):
        DBG("READ: %08X | %08X | %08X" % (address, size, block))
        ASSERT(self.send(DA_READ + struct.pack(">III", address, size, block), 1) == ACK, "answer")

    def da_read_buffer(self, block=4096):
        data = self.s.read(block)
        crc = self.read(2) # check sum
        self.s.write(ACK)
        return data, crc

    def da_write_address(self, address, size, block=4096):
        DBG("WRITE: %08X | %08X | %08X" % (address, size, block))
        ASSERT(self.send(DA_WRITE_ADDR + struct.pack(">III", address, size, block), 2) == ACK+ACK, "da_write_address")

    def da_write_buffer(self, data, cs):
        c = checksum(data)
        self.s.write(data)
        self.send(struct.pack(">H", c & 0xFFFF))
        if self.read(1) != CONF:
            self.read(4)
            ASSERT(False, "da_write_buffer crc") #A5 00 00 0B F5
        PB_STEP()
        return cs + c

    def da_write_all(self, data, size, block=4096):
        cs = 0
        for i in xrange(0, size, block):
            DBG("--> data[{}]".format(block))
            d = data[:block]
            data = data[block:]
            cs = self.da_write_buffer(d, cs)
        ASSERT(self.read(1) == ACK, "da_write_all ack")
        ASSERT(self.send(struct.pack(">H", cs & 0xFFFF), 1) == ACK, "da_write_all crc")
        ASSERT(self.send("\xA5", 1) == ACK, "da_write_all end")

    def da_p2a(self, page): # page to address
        r = self.send(DA_P2A + struct.pack(">I", page), 5) # res = 08292000-5A
        ASSERT(r[4] == ACK, "page to address")
        return struct.unpack(">I", r[:4])[0]

    def da_a2p(self, address): # address to page
        r = self.send(DA_A2P + struct.pack(">I", address), 5) # res = 00000292-5A
        ASSERT(r[4] == ACK, "address to page")
        return struct.unpack(">I", r[:4])[0]


    def get_da(self, offset, size):
        self.fd.seek( offset )
        data = self.fd.read( size )
        return data

    def get_da_info(self, flashid, offset, size):
        self.fd.seek( offset )
        while size > 0:
            data = self.fd.read( 36 )
            if flashid in data:
                return data
            size -= 1
        ERROR("Flash not supported")

    def uart_speed_max(self):
        self.s.write(ACK)
        self.s.read(2)
        self.s.write(ACK+b'\x01')
        self.s.read(2)
        self.s.write(ACK)
        self.s.read(2)
        self.s.write(ACK+ACK)
        time.sleep(0.1)
        # SET BAUDRATE
        self.s.baudrate = 921600
        self.s.write(CONF)
        ASSERT(self.s.read(1) == CONF, "uart brg 69")
        self.s.write(ACK)
        ASSERT(self.s.read(1) == ACK, "uart brg 5A")
        # SYNC UART
        for i in xrange(15, 255, 15):
            self.s.write( chr( i ) )
            ASSERT( self.s.read( 1 ) == chr( i ), "uart sync")
        ASSERT(self.s.read(2) == "\0\0", "uart test 0")
        self.s.write(ACK)
        ASSERT(self.s.read(2) == "\0\0", "uart test 2")
        self.s.write(ACK)
        ASSERT(self.s.read(4) == "\0\0\0\0", "uart test 4")
        self.s.write(ACK)
        ASSERT(self.s.read(6) == "\0\0\0\0\0\0", "uart test 6")
        self.s.reset_input_buffer()
        self.s.reset_output_buffer()

    def init(self):
        self.da_write16(0xA2090000, 0x11) # WDT_Base = 0xA2090000 , WDT_Disable = 0x11
        # GET CHIP INFO
        self.chip_0 = self.da_read16(0x80000000)
        self.chip_4 = self.da_read16(0x80000004)
        if self.da_read16(0x80000008)[1] != 0x2625:
            ERROR("unknown chipset id")
        self.chip_ver = self.da_read16(0x8000000C)[1]
        if self.chip_ver != 0x8300 and self.chip_ver != 0x8100:
            ERROR("unknown chipset version")
        self.chip = hex(self.chip_ver) + ".0" # or ".1"
        PB_END()

    def connect(self, timeout = 9.0):
        fname = join(self.dir, 'MT2625.bin')
        ASSERT( os.path.isfile(fname) == True, "No such file: " + fname )
        self.fd = open( fname, "rb")
        self.boot(timeout)
        self.init()

    def find_imei(self, data):
        global imei
        while 'Enas\0IMEI' in data:
            n = data.find('Enas\0IMEI')
            if n > -1:
                imei = hexs(data[n+10 : n+26])
                imei = rem_zero(imei)
                #DBG(imei)
            data = data[n+1:]

    def backupNVDM(self, fname = ""):
        global imei
        imei = ''
        PB_BEGIN( 'Read nvdm <' )
        ASSERT(self.nvdm_address != 0 or self.nvdm_length != 0, "nvdm params")
        self.da_read(self.nvdm_address, self.nvdm_length)
        if fname == "":
            fname = join(self.dir, "nvdm.bin")
        f = open(fname,'wb')
        for i in xrange(self.nvdm_address, self.nvdm_address + self.nvdm_length, 4096):
            data, crc = self.da_read_buffer(4096)
            f.write(data)
            self.find_imei(data)
        f.close()
        name = fname.replace(".bin", '_'+imei+".dat")
        try:
            if os.path.exists(name):
                os.remove(name)
            os.rename(fname, name)
            print('NVDM File: ' + name)
        except OSError:
            print('NVDM File: ' + fname)
        PB_END()

    def end(self):
        self.s.write(DA_FINISH+'\x00')
        ASSERT( self.s.read(1) == b'\x5A', "Finish")
        # Power-up the board after upload
        if self.auto_reset:
            self.s.dtr = 0
            time.sleep(0.6)
            self.s.dtr = 1

    def begin(self, nvdm = 0):
        ASSERT( self.chip in self.DA, "Unknown module: {}".format(self.chip) )
        self.s.timeout = 0.1
        PB_BEGIN( 'Begin <' )
        # DA_1
        offset  = self.DA[self.chip]["1"]["offset"]
        size    = self.DA[self.chip]["1"]["size"]
        address = self.DA[self.chip]["1"]["address"]
        data    = self.get_da(offset, size)
        ASSERT( self.cmd(CMD_SEND_EPP + struct.pack(">IIII", address, size, 0x04002000, 0x00001000), 2) == b"\0\0", "CMD_SEND_EPP")
        while data:
            self.s.write(data[:1024])
            data = data[1024:]
            PB_STEP()
        ASSERT( self.cmd("", 10) == b"\x1D\x3D\0\0\0\0\0\0\0\0", "EPP answer" )
        self.uart_speed_max()
        # DA_2
        offset  = self.DA[self.chip]["2"]["offset"]
        size    = self.DA[self.chip]["2"]["size"]
        address = self.DA[self.chip]["2"]["address"]
        data    = self.get_da(offset, size)
        ASSERT( self.cmd(CMD_SEND_DA + struct.pack(">III", address, size, 0x00000000), 2) == b"\0\0", "CMD_SEND_DA" )
        while data:
            self.s.write(data[:4096])
            data = data[4096:]
            PB_STEP()
        r = self.read(4) # checksum D6AE0000 XOR
        # JUMP DA
        ASSERT( self.cmd(CMD_JUMP_DA + struct.pack(">I", address), 2) == b"\0\0", "CMD_JUMP_DA")# D5-04001000
        r = self.read(1)                        # <-- C0
        r = self.send(b"\x3F\xF3\xC0\x0C", 4)   # <-- 0C3FF35A - Magic ?
        r = self.send(b"\x00\x00", 2)           # <-- 6969
        flashID = self.send(ACK, 6)             # <-- 00C200250036 - FlashID
        flashData = self.get_da_info(flashID, self.DA[self.chip]["3"]["offset"], self.DA[self.chip]["3"]["size"])
        r = self.send(b"\x24", 1)               # <-- 5A
        self.send(flashData)                    # ????
        flashInfo = self.s.read(80)
        ASSERT( flashInfo[-1] == ACK, "flash info")
        self.send(ACK)
        if nvdm > 0:
            self.send(DA_NWDM_INFO)
            for i in range(256):
                if self.s.read(1) == ACK:
                    r = self.read(4)
                    self.nvdm_address = struct.unpack(">I", r)[0]
                    r = self.read(4)
                    self.nvdm_length = struct.unpack(">I", r)[0]
                    PB_END()
                    DBG('NVDM Address: 0x%08X' % self.nvdm_address)
                    DBG('NVDM Length : 0x%08X' % self.nvdm_length)
                    return
            ERROR("NWDM Info")
        else:
            PB_END()

    def openApplication(self, fname):
        ASSERT( os.path.isfile(fname) == True, "No such file: " + fname )
        self.app_name = fname
        with open(fname,'rb') as f:
            data = f.read()
        if len( data ) < 0x40:
            ERROR("Bin min size")
        return data

    def uploadApplication(self, __aaddr, id="-", filename="", check=True):
        app_address = int(__aaddr, 16)
        app_max_size = self.DEVICE[id]["max_size"]
        app_data = self.openApplication(filename)
        app_size = len(app_data)
        # ASSERT( app_size <= app_max_size, "Application max size limit" )
        PB_BEGIN( 'Writhing <' )
        first_page = self.da_a2p(app_address)
        first_address = self.da_p2a(first_page)
        last_page = self.da_a2p(app_address + app_size)
        last_address = self.da_p2a(last_page + 1)
        rem_first = app_address - first_address
        rem_last = last_address - (app_address+app_size)
        DBG("app  SIZE: %08X" % app_size)
        DBG("app-b ADR: %08X" % app_address)
        DBG("app-e ADR: %08X" % (app_address + app_size))
        DBG("FIRST ADR: %08X" % first_address)
        DBG("FIRST REM: %08X" % rem_first)
        DBG("LAST  ADR: %08X" % last_address)
        DBG("LAST  REM: %08X" % rem_last)
        bin = ''
        if rem_first > 0:
            self.da_read(first_address)
            data, crc = self.da_read_buffer()
            ASSERT( len(data) == 4096, "first data size" )
            bin = data[0: rem_first]
            bin += app_data
            DBG("REPLACED FIRST PAGE")
        else:
            bin = app_data
        if rem_last > 0: # REPLACE LAST PAGE
            self.da_read(last_address)
            data, crc = self.da_read_buffer()
            ASSERT( len(data) == 4096, "last data size" )
            bin += data[-rem_last:]
            DBG("REPLACED LAST PAGE")
        # WRITE
        self.s.timeout = 1.0
        size = len(bin)
        DBG("BIN SIZE: %08X" % size)
        self.da_write_address(first_address, size)
        self.da_write_all(bin, size)
        PB_END()
        DBG("Application <{}> READY".format(self.app_name ))
  

m = MT2625( Serial(sys.argv[1], 115200),  True )
m.connect(9.0)

if len(sys.argv) < 2:
	print("\033[31mMissing arguments\033[0m")
	sys.exit(1)

elif len(sys.argv) == 2:
	if sys.argv[1] == "--backup":
		m.begin(nvdm=1)
		m.backupNVDM()
		m.end()
	else:
		print("\033[31m Missing arguments\033[0m")

else:
	if ("--backup" in sys.argv):
		m.begin(nvdm=1)
		m.backupNVDM()
	else:
		m.begin(nvdm=0)
	m.uploadApplication(sys.argv[2], "bc66", sys.argv[3])
	m.end()

