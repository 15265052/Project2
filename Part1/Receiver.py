import time as t

import matplotlib.pyplot as plt
import soundfile as sf
import sounddevice as sd
import numpy as np
from scipy import signal, integrate
from constant import *


def receive(file_name):
    print("start receiving")
    stream = set_stream()
    stream.start()
    global global_status
    global global_pointer
    global global_buffer
    dump_frames(100000)
    pointer = global_pointer
    while True:
        if pointer + block_size > len(global_buffer):
            continue
        block_buffer = global_buffer[pointer:pointer + block_size]
        pointer_RTX = detect_preamble(block_buffer)
        if not pointer_RTX == "error":
            pointer += pointer_RTX
            RTX_detected = global_buffer[pointer : pointer + len(RTX) - preamble_length]
            global_pointer += pointer + len(RTX)-preamble_length
            if verify_RTX(RTX_detected):
                global_status = "sending CTX"
                break
        pointer += block_size
    global_pointer += pointer

    print("test finished!")


def decode_one_bit(s_buffer):
    sum = np.sum(s_buffer * signal0)
    if sum >= 0:
        return '0'
    else:
        return '1'


def set_stream():
    sd.default.extra_settings = asio_in, asio_out
    sd.default.latency = latency
    sd.default.device[0] = asio_id
    sd.default.device[1] = asio_id
    stream = sd.Stream(sample_rate, block_size, dtype=np.float32, callback=callback)
    return stream


def verify_RTX(RTX_buffer):
    RTX_string = "1010101"
    str_decoded = ""
    pointer = 0
    for i in range(7):
        decode_buffer = RTX_buffer[pointer: pointer + samples_per_symbol]
        str_decoded += decode_one_bit(decode_buffer)
        pointer += samples_per_symbol

    if RTX_string == str_decoded:
        return True
    else:
        return False


def callback(indata, outdata, frames, time, status):
    global global_buffer
    global global_pointer
    global global_status
    # global ed
    global_buffer = np.append(global_buffer, indata[:, 0])
    dump_frames(global_pointer)
    global_pointer = 0
    # if t.time() - t1 > 15 and ed:
    #     plt.plot(range(len(global_buffer)), global_buffer)
    #     plt.show()
    #     ed = False
    if global_status == "":
        outdata.fill(0)

    if global_status == "sending CTX":
        print(global_status)
        outdata[:] = np.append(CTX, np.zeros(block_size-len(CTX))).reshape(1024, 1)
        global_status = ""


def dump_frames(frames):
    global global_buffer
    global_buffer = global_buffer[frames:]


global_buffer = np.array([])
global_pointer = 0
global_status = ""
file_name = "test100.wav"
receive(file_name)

