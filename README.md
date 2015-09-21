# micropython-fram
A driver to enable the Pyboard to access the Ferroelectric RAM (FRAM) board from [Adafruit](http://www.adafruit.com/product/1895).
FRAM is a technology offering nonvolatile memory with extremely long endurance and fast access, avoiding
the limitations of Flash memory. Its endurance is specified as 10^13 writes, contrasted with 10,000 which is
the quoted endurance of the Pyboard's onboard Flash memory. In data logging applications this can be exceeded
relatively rapidly. Flash writes can be slow because of the need for a sector erase: this is not a fast process.
FRAM is byte addressable and is not subject to this limitation. The downside is limited capacity. Compared to
a Micro SD card fitted to the Pyboard it offers lower power consumption and longer endurance.

From one to eight boards may be used to construct a nonvoltile memory module with size ranging from 32KB to 256KB.
The driver allows the memory either to be mounted in the Pyboard filesystem as a disk device or to be addressed
as an array of bytes.

# Connections

To wire up a single FRAM module, connect to the Pyboard as below (nc indicates no connection).

| FRAM    |  L  |  R  |
|:-------:|:---:|:---:|
| Vcc     | 3V3 | 3V3 |
| Gnd     | GND | GND |
| WP      | nc  | nc  |
| SCL     | X9  | Y9  |
| SDA     | X10 | Y10 |
| A2      | nc  | nc  |
| A1      | nc  | nc  |
| A0      | nc  | nc  |

For multiple modules the address lines A0, A1 and A2 of each module need to be wired to 3V3 in such a way as
to give each device a unique address. These must start at zero and be contiguous. Thus with three modules, the
first would have address lines unconnected (address 0), the second would have A0 connected to 3V3 (address 1) and the
third would have A1 connected to 3V3 (address 2).

Multiple modules should have 3V3, Gnd, SCL and SDA lines wired in parallel.

# Driver

The driver supports mounting the FRAM modules as a filesystem. Initially the device will be unformatted so
it is necessary to issue code along these lines to format the device.

```python
import pyb 
from fram import FRAM
f = FRAM(side = 'L')
pyb.mount(f, '/fram', mkfs = True)
pyb.mount(None, '/fram')
```

At the time of writing the ``pyb`` module provides no way to reformat a drive which already has a filesystem. As
a workround the following will perform this:

```python
import pyb 
from fram import FRAM
f = FRAM('L')
f.low_level_format()
pyb.mount(f, '/fram', mkfs = True)
pyb.mount(None, '/fram')
```

Note that, at the outset, you need to decide whether to use the array as a mounted filesystem or as
a byte array. As a filesystem the limited size is an issue, but a potential use case is for
pickling Python objects for example to achieve persistence when issuing ``pyb.standby()``.

### Constructor

``FRAM()`` Takes two arguments:
 1. ``side`` "L" or "R" indicating the left and right sides of the board as seen with the
 USB connector at the top.
 2. ``verbose`` (default False). If True, the constructor issues information on the FRAM devices it has detected.
 
 A ``FRAMException`` will be raised if a device is not detected or if device address lines are not
 wired as  described in Connections above.

### Methods providing the block protocol

For the protocol definition see
[the pyb documentation](http://docs.micropython.org/en/latest/library/pyb.html)

``readblocks()``  
``writeblocks()``  
``count()``  

### Methods providing byte level access

The following methods are available for general use.
``available()`` Returns True if the device is detected and is supported.  
``readwrite()`` Provides byte level access to the memory array. Arguments:
 1. ``addr`` Starting byte address
 2. ``buf`` A buffer containing the data to write or to hold read data
 3. ``read`` If True, perform a read otherwise write. The size of the buffer determines the quantity
 of data read or written. A ``FRAMException`` will be thrown if the read or write extends beyond the
 end of the array.

``low_level_format()`` Erases the filesystem! Currently (this may change) the pyb module doesn't
provide a means of forcing a drive format. Issuing a ``low_level_format()`` followed by
``pyb.mount()`` with ``mkfs-True`` will format the drive deleting all files.

Other than for debugging there is no need to call ``available()``: the constructor will throw
a ``FRAMException`` if it fails to communicate with and correctly identify the chip.

## File copy

A rudimentary ``cp(source, dest)`` function is provided as a generic file copy routine for
setup and debugging purposes at the REPL. The first argument is the full pathname to the source file. The
second may be a full path to the destination file or a directory specifier which must have a
trailing '/'. If an OSError is thrown (e.g. by the source file not existing or the FRAM becoming
full) it is up to the caller to handle it. For example (assuming the FRAM is mounted on /fram):

```python
cp('/flash/main.py','/fram/')
```
