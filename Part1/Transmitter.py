import numpy as np
from scipy import signal, integrate
import time
import sounddevice as sd
import matplotlib.pyplot as plt
from constant import *


def transmit(file_name):
    data = gen_data(file_name)
    # send RTX to custom
    stream = set_stream()
    stream.start()
    global global_status
    # send RTX and wait for CTX
    dump_frames(100000)
    while True:
        global_status = "sending RTX"
        if can_send(stream):
            break
    print("1")


def can_send(stream):
    # confirm that can transmit
    max_waiting_time = 5 * 1000
    start_waiting_time = stream.time
    global global_pointer
    pointer = global_pointer
    while stream.time - start_waiting_time < max_waiting_time:
        if pointer + block_size > len(global_buffer):
            continue
        block_buffer = global_buffer[pointer:pointer + block_size]
        pointer_CTX = detect_preamble(block_buffer)
        if not pointer_CTX == "error":
            CTX_detected = global_buffer[pointer + pointer_CTX:pointer + pointer_CTX + len(CTX)]
            global_pointer += pointer + pointer_CTX + len(CTX)
            return verify_CTX(CTX_detected)
        pointer += block_size
    global_pointer += pointer
    return False


def gen_data(file_name):
    with open(file_name, 'r') as file:
        file_data = file.read()
    input_index = 0
    symbols_in_frame = 100
    frame_num = int(len(file_data) / symbols_in_frame)
    if frame_num * 100 < len(file_data):
        frame_num += 1
    data = []
    for i in range(frame_num):
        data.append(preamble)
        for j in range(symbols_in_frame):
            if file_data[input_index] == '0':
                data.append(signal0)
            else:
                data.append(signal1)
            input_index += 1
    return np.concatenate(data)


def set_stream():
    sd.default.extra_settings = asio_in, asio_out
    sd.default.latency = latency
    sd.default.device[0] = asio_id
    sd.default.device[1] = asio_id
    stream = sd.Stream(sample_rate, block_size, dtype=np.float32, device=asio_id, channels=1, callback=callback)
    return stream


def verify_CTX(CTX_buffer):
    CTX_string = "0101010"
    str_decoded = ""
    pointer = 0
    for i in range(7):
        decode_buffer = CTX_buffer[pointer: pointer + samples_per_symbol]
        str_decoded += decode_one_bit(decode_buffer)
        pointer += samples_per_symbol

    if CTX_string == str_decoded:
        return True
    else:
        return False


def decode_one_bit(s_buffer):
    if np.sum(s_buffer * signal0) >= 0:
        return '0'
    else:
        return '1'


def callback(indata, outdata, frames, time, status):
    global global_buffer
    global global_pointer
    global global_status
    global_buffer = np.append(global_buffer, indata[:])
    dump_frames(global_pointer)
    global_pointer = 0

    if global_status == "":
        outdata.fill(0)

    if global_status == "sending RTX":
        outdata[:] = np.append(RTX, np.zeros(block_size-len(RTX))).reshape(1024, 1)
        global_status = ""


def dump_frames(frames):
    global global_buffer
    global_buffer = global_buffer[frames:]


global_buffer = np.array([])
global_pointer = 0
global_status = ""

start = time.time()
transmit("INPUT.txt")
end = time.time()
print("Transmitting time: ", end - start)
