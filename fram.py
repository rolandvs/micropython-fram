# fram.py Driver for Adafruit 32K Ferroelectric RAM module (Fujitsu MB85RC256V)
# Peter Hinch
# 7th Sep 2016 Adapted to be compatible with ESP8266
# 21st Sep 2015 Tested with two FRAM units

from sys import platform

FRAM_MIN = const(0x50)          # FRAM I2C address 0x50 to 0x57
FRAM_SLAVE_ID = const(0xf8)     # FRAM device ID location
MANF_ID = const(0x0a)
PRODUCT_ID = const(0x510)

class FRAMException(OSError):
    pass

# Dumb file copy utility to help with managing FRAM contents at the REPL.
def cp(source, dest):
    if dest.endswith('/'):                      # minimal way to allow
        dest = ''.join((dest, source.split('/')[-1]))  # cp /sd/file /fc/
    with open(source, 'rb') as infile:          # Caller should handle any OSError
        with open(dest,'wb') as outfile:        # e.g file not found
            while True:
                buf = infile.read(100)
                outfile.write(buf)
                if len(buf) < 100:
                    break

# A logical ferroelectric RAM made up of from 1 to 8 chips
class FRAM():
    def __init__(self, i2c, verbose = False):
        self.verbose = verbose
        self.pyboard = platform == 'pyboard'
        self._i2c = i2c
        devices = self._i2c.scan()
        if self.verbose:
            for d in devices:
                print(hex(d))
        lstdev = [d for d in devices if d in range(FRAM_MIN, FRAM_MIN +8)]
        self.ndevices = len(lstdev)
        if self.ndevices > 1:
            lstdev.sort()
            if lstdev[-1] - lstdev[0] != self.ndevices -1:
                raise FRAMException("FRAM device addresses not contiguous.")
        elif self.ndevices ==0:
            raise FRAMException("No FRAM device detected.")
        if lstdev[0] != FRAM_MIN:
            raise FRAMException("FRAM address jumpers must start at 0.")
        if self.verbose:
            print("{:d} FRAM device(s) detected".format(self.ndevices))
        for device_addr in lstdev:
            if not self.available(device_addr):
                raise FRAMException("FRAM at address 0x{:02x} reports an error".format(device_addr))
        self.addrbuf = bytearray(2)             # Memory offset into current chip
        self.i2c_addr = None                    # i2c address of current chip

    def available(self, device_addr):
        if self.pyboard:
            res = self._i2c.mem_read(3, FRAM_SLAVE_ID >>1, device_addr <<1)
        else:
            res = self._i2c.readfrom_mem(FRAM_SLAVE_ID >>1, device_addr <<1, 3)
        manufacturerID = (res[0] << 4) + (res[1]  >> 4)
        productID = ((res[1] & 0x0F) << 8) + res[2]
        return manufacturerID == MANF_ID and productID == PRODUCT_ID

# Low level access
    def _getaddr(self, addr, nbytes):           # Set up addrbuf and i2c_addr
        self.addrbuf[0] = (addr >> 8) & 0x7f
        self.addrbuf[1] = addr & 0xff
        device = addr >> 15                     # Chip no
        memaddr = addr & 0x7fff                 # offset into chip
        if device >= self.ndevices:
            return 0                            # Error condition: 0 bytes handled
        self.i2c_addr = FRAM_MIN + device
        end_addr = memaddr + nbytes
        if end_addr < 0x8000:                   # return no.of bytes that can be processed
            return nbytes                       # all of them
        return 0x8000 - memaddr                 # no. of bytes available in device

    def readwrite(self, addr, buf, read):
        nbytes = len(buf)
        start = 0
        while nbytes > 0:
            bytes_handled = self._getaddr(addr, nbytes)
            if bytes_handled == 0:
                raise FRAMException("FRAM Address is out of range")
            if self.pyboard:
                if read:
                    self._i2c.send(self.addrbuf, self.i2c_addr)
                    buf[start : start + bytes_handled] = self._i2c.recv(bytes_handled, self.i2c_addr)
                else:
                    self._i2c.send(self.addrbuf +buf[start: start + bytes_handled], self.i2c_addr)
            else:
                if read:
                    self._i2c.writeto(self.i2c_addr, self.addrbuf)
                    buf[start : start + bytes_handled] = self._i2c.readfrom(self.i2c_addr, bytes_handled)
                else:
                    self._i2c.writeto(self.i2c_addr, self.addrbuf +buf[start: start + bytes_handled])
            nbytes -= bytes_handled
            start += bytes_handled
            addr += bytes_handled
        return buf

# Block protocol
    def readblocks(self, blocknum, buf):
        return self.readwrite(blocknum << 9, buf, True)

    def writeblocks(self, blocknum, buf):
        self.readwrite(blocknum << 9, buf, False)

    def count(self):
        return self.ndevices * 64 # 64*512 = 32K

    def ioctl(self, op, arg):
        #print("ioctl(%d, %r)" % (op, arg))
        if op == 4:  # BP_IOCTL_SEC_COUNT
            return self.ndevices * 64
        if op == 5:  # BP_IOCTL_SEC_SIZE
            return 512


# ******* UTILITY TO ENABLE FORCED FORMAT *******
# See README. This wipes the filesystem! Contingency until MicroPython provides a forced format
    def low_level_format(self):
        self.readwrite(0, bytes(512), False)    # Erase FAT block zero
