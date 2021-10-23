import threading

from Demos.FileSecurityTest import sd
from constant import *


def set_stream():
    sd.default.extra_settings = asio_in, asio_out
    sd.default.device[0] = asio_id
    sd.default.device[1] = asio_id
    stream = sd.Stream(sample_rate, block_size, dtype=np.float32, callback=callback)
    return stream


def callback(indata, outdata, frames, time, status):
    global global_buffer
    global global_pointer
    global global_status
    global_buffer = np.append(global_buffer, indata[:])
    global_pointer = 0

    if global_status == "":
        outdata.fill(0)


def dump_frames(frames):
    global global_buffer
    global_buffer = global_buffer[frames:]


node_state = ""
RxFrame = []
global_pointer = 0
global_buffer = []
global_status = ""
state_lock = threading.Lock
RxFrame_lock = threading.Lock
