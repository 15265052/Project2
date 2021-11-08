from Part3.frame.PHYFrame import *


def predefine_ACK():
    ACK_pre = []
    for i in range(frame_num):
        ACK_pre.append(single_ACK(i))
    return ACK_pre


def single_ACK(num):
    """generate a single ACK frame"""
    ACK_frame = PhyFrame()
    ACK = "1010"
    ACK_frame.set_num(num)
    ACK_frame.set_load(node1_addr, node2_addr, ACK, "")
    return ACK_frame.get_modulated_frame()


ACK_buffer = []
ACK_predefined = predefine_ACK()
