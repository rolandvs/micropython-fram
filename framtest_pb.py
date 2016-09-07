# Simple demo of FRAM on Pyboard I2C bus 2.
# assumes device has already been formatted
# Has been tested with two contiguous FRAM boards
import uos
from fram import FRAM
i2c = pyb.I2C(2, pyb.I2C.MASTER)
i2c.scan()
fram = FRAM(i2c, verbose=True)
pyb.mount(fram, '/fram')
uos.listdir('/fram')

