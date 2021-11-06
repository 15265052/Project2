"""
This file defines a PHY Frame and supplies functions for decoding the Frame

PHY Frame structure:
    | Preamble | Frame Num | PHY load | CRC |

PHY load here is MAC Frame, which is defined in MACFrame.py

Author: du xiao yuan
Modified At: 2021/10/30
"""
from Part3.frame.MACFrame import *
from Part3.config.globalConfig import *


class PhyFrame:
    """
     A physical frame has three parts:
     1. preamble
     2. physical load (MAC frame)
     3. CRC
     The actual frame is the combination of 2 and 3
     So the class member doesn't contain preamble
     But every time we get the PHY frame in the form of array
     The preamble will be included automatically
     """

    def __init__(self):
        self.phy_load = None
        self.CRC = None
        self.num = None

    def from_array(self, frame_array):
        """setting from the detected array, preamble is excluded"""
        self.num = frame_array[:8]
        self.phy_load = MACFrame()
        self.phy_load.set_destination(frame_array[8:16])
        self.phy_load.set_source(frame_array[16:24])
        self.set_type(frame_array[24:28])
        self.phy_load.set_load(frame_array[28:len(frame_array)-8])
        self.CRC = frame_array[len(frame_array)-8:]

    def get_modulated_frame(self):
        """ Add preamble to the head, get whole modulated frame"""
        phy_frame = np.concatenate([preamble, modulate_string(self.num), self.phy_load.modulate(), modulate_string(self.CRC)])
        return phy_frame

    def get_load(self):
        """get MAC frame, w/o preamble and CRC"""
        return self.phy_load

    def get_type(self):
        """get the type of frame"""
        return self.phy_load.get_type()

    def get_source(self):
        """get the source host of frame"""
        return self.phy_load.get_source()

    def get_destination(self):
        """get the destination of frame"""
        return self.phy_load.get_destination()

    def get_decimal_num(self):
        """in the form of decimal"""
        return int(self.num, 2)

    def set_num(self, num):
        temp_str = bin(num)[2:]
        temp_str = (8 - len(temp_str)) * '0' + temp_str
        return temp_str

    def set_destination(self, destination):
        """set the destination of frame"""
        self.phy_load.set_destination(destination)

    def set_source(self, source):
        """set the source host of frame"""
        self.phy_load.set_source(source)

    def set_type(self, type):
        """set the type of frame"""
        self.phy_load.set_type(type)

    def set_load(self, dest, src, type, MAC_load):
        self.phy_load = MACFrame()
        self.phy_load.set_destination(dest)
        self.phy_load.set_source(src)
        self.phy_load.set_type(type)
        self.phy_load.set_load(MAC_load)
        self.CRC = gen_CRC8(self.num+self.phy_load.get())

    def check(self):
        """
        for check if the physical frame is right.
        Due to the preamble detecting design, 'physical_frame' doesn't contain preamble

        :param physical_frame an array composed of physical frame w/o preamble
        """
        if check_CRC8(self.num+self.phy_load.get()+self.CRC):
            return True
        else:
            return False
