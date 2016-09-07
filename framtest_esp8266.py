# Simple demo of FRAM on ESP8266 using pins marked on Feather Huzzah (4,5).
# assumes device has already been formatted
# Has been tested with two contiguous FRAM boards
from fram import FRAM
import uos
import machine
scl = machine.Pin(5, machine.Pin.OUT)
sda = machine.Pin(4, machine.Pin.OUT)
i2c = machine.I2C(scl, sda)
i2c.scan()
fram = FRAM(i2c, verbose=True)
uos.umount() # alas can only mount one FS
fs = uos.VfsFat(fram, '/')
uos.listdir('/')

