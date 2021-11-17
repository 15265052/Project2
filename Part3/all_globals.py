import threading
from Part3.config.globalConfig import *
RxFrame = []  # frame for Rx to deal with
TxFrame = []  # frame for Tx to send

global_pointer = 0  # for telling the position that is being processed in global buffer
global_buffer = []  # for receiving all the data from speaker
global_status = ""  # determines what to send
global_input_index = 0  # the global input index of data

send_time = [0]*frame_num
ACK_confirmed = [False]*frame_num
frame_confirmed = [False] * frame_num
frame_rece = [None] * frame_num

# for recording how many frames has been detected
detected_frames = 0

# for thread synchronization
MAC_condition = threading.Condition()
Rx_condition = threading.Condition()
Tx_condition = threading.Condition()

state_lock = threading.Lock()
RxFrame_lock = threading.Lock()

# detect if the channel is noisy
is_noisy = False
silent_threshold = 0.05
ACK_pointer = 0
macperf = True
macperf_bits = 0
macperf_time = 0
send_buffer_size = 2

