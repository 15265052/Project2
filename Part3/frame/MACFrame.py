"""This file defines the MAC frame structure and supplies some functions to implement the frame"""
import numpy as np

from ..config.globalConfig import *
from ..config.globalConfig import modulate_string


class MACFrame:
    """
    A MAC Frame structure is shown below:
        | DEST | SRC | TYPE | MAC load |
    Where 8 bits for destination and source respectively
        4 bits for type field
    MAC load's length is limited, its limitation is defined in config/globalConfig.py
    User should not use this class directly, it mostly used in the PHYFrame class

    ps: A Frame is stored in the form of string composed all of bits, like: "100000011101"
    """

    def __init__(self):
        """initialize destination, source and host to None"""
        self.destination = None
        self.source = None
        self.type = None
        self.load = None

    def get(self):
        """get the whole MAC frame in the form of string"""
        return self.destination + self.source + self.type + self.load

    def get_data(self):
        return self.load

    def set_destination(self, dest):
        """ :param dest: an 8 bit string, the address of the frame destination"""
        if not len(dest) == 8:
            print("destination must be 8 bits long string!")
            return
        self.destination = dest

    def set_source(self, src):
        """:param src: an 8 bit string, the address of the frame source host """
        if not len(src) == 8:
            print("source must be 8 bits long string!")
            return
        self.destination = src

    def set_type(self, type):
        """:param type: indicate what type the frame is"""
        self.type = type

    def set_load(self, load):
        if len(load) > MAC_load_limit:
            print("load overflows!")
            return
        self.load = load

    def get_destination(self):
        return self.destination

    def get_source(self):
        return self.source

    def get_type(self):
        return self.type

    def modulate(self):
        """modulate the whole frame into signals"""
        return [modulate_string(self.destination), modulate_string(self.source),
                modulate_string(self.type), modulate_string(self.load)]
