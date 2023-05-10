import os
import binascii

# Config variables
class Config:
    root_dir = os.path.dirname(os.path.realpath(__file__+'/..'))
    cluster_root_dir = '/home2/yesylevskyy/work/FF'
    ssh_host = 'yesylevskyy@aurum.uochb.cas.cz'


# Computes hash of a file
def CRC32_from_file(filename):
    buf = open(filename,'rb').read()
    buf = (binascii.crc32(buf) & 0xFFFFFFFF)
    return ("%08X" % buf).lower()
