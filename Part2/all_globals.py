import threading

from constant import *

RxFrame = []
TxFrame = []
global_pointer = 0
global_buffer = []
global_status = ""
global_input_index = 0
state_lock = threading.Lock()
RxFrame_lock = threading.Lock()
detected_frames = 0
send_time = [0]*frame_num
ACK_confirmed = [False]*frame_num
frame_confirmed = [False] * frame_num
frame_rece = [None] * frame_num
frame_retransmit = [0] * frame_num
max_retransmit = 7
# for thread synchronization
MAC_condition = threading.Condition()
Rx_condition = threading.Condition()
Tx_condition = threading.Condition()
ACK_pointer = 0