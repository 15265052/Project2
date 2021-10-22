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
    # send RTX and wait for CTX
    while True:
        stream.write(RTX)
        if can_send(stream):
            break
    print("1")



def can_send(stream):
    #confirm that can transmit
    max_waiting_time = 5
    start_waiting_time = stream.time
    while stream.time - start_waiting_time < max_waiting_time:
        block_buffer = stream.read(block_size)
        pointer_CTX = detect_preamble(block_buffer)
        if not pointer_CTX == "error":
            remain_CTX_size = len(CTX) - (block_size - pointer_CTX)
            if remain_CTX_size > 0:
                CTX_detected = block_buffer[pointer_CTX:]
                CTX_detected.append(stream.read(remain_CTX_size))
            else:
                CTX_detected = block_buffer[pointer_CTX: pointer_CTX + len(CTX)]
            return verify_CTX(CTX_detected)

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
    sd.default.device[1] = asio_id
    stream = sd.Stream(sample_rate, block_size, dtype=np.float32)
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


start = time.time()
transmit("INPUT.txt")
end = time.time()
print("Transmitting time: ", end - start)
