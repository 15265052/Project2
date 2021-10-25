import threading

from Demos.FileSecurityTest import sd
from constant import *




node_state = ""
RxFrame = []
TxFrame = []
global_pointer = 0
global_buffer = []
global_status = ""
global_input_index = 0
state_lock = threading.Lock()
RxFrame_lock = threading.Lock()
detected_frames = 0
# for thread synchronization
MAC_condition = threading.Condition()
Rx_condition = threading.Condition()
Tx_condition = threading.Condition()
