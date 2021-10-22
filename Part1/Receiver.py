import time

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

    while True:
        block_buffer = stream.read(block_size)
        pointer_RTX = detect_preamble(block_buffer)
        if not pointer_RTX == "error":
            remain_RTX_size = len(RTX) - (block_size - pointer_RTX)
            if remain_RTX_size > 0:
                RTX_detected = block_buffer[pointer_RTX:]
                RTX_detected.append(stream.read(remain_RTX_size))
            else:
                RTX_detected = block_buffer[pointer_RTX: pointer_RTX + len(RTX)]
            if verify_RTX(RTX_detected):
                stream.write(CTX)
                break
    stream.stop()


# def decode(buffer):
#     str1 = ''
#     for i in range(symbol_per_frame):
#         sample_buffer = buffer[i * samples_per_symbol:(i + 1) * samples_per_symbol]
#         if len(sample_buffer) < samples_per_symbol:
#             str = '0'
#         else:
#             str = decode_one_bit(sample_buffer)
#         str1 = str1 + str
#     write_file(str1)


# def write_file(str):
#     with open("OUTPUT.txt", 'a') as f:
#         f.write(str)


def decode_one_bit(s_buffer):
    sum = np.sum(s_buffer * signal0)
    if sum >= 0:
        return '0'
    else:
        return '1'


def set_stream():
    sd.default.extra_settings = asio_in, asio_out
    sd.default.latency = latency
    sd.default.device[1] = asio_id
    stream = sd.Stream(sample_rate, block_size, dtype=np.float32)
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

file_name = "test100.wav"
receive(file_name)
# with open('INPUT.txt', 'r') as file:
#     file_data = file.read()
# input_index = 0
# symbols_in_frame = 100
# data = []
# for i in range(frame_num):
#     data.append(header)
#     for j in range(symbols_in_frame):
#         if file_data[input_index] == '0':
#             data.append(signal0)
#         else:
#             data.append(signal1)
#         input_index += 1
# data = np.concatenate(data)

# corr = signal.correlate(data, header)
# plt.plot(range(len(corr)), corr)
# plt.show()
# threshold = 2
# data_length = len(data)
# sync = []
# pointer = 0
# while detected_frame < frame_num and pointer < data_length:
#     if not is_receiving:
#         # fill in sync FIFO
#         sync = data[pointer:pointer + header_length + symbol_per_frame * samples_per_symbol]
#         pointer_header = detect_header(sync)
#         if pointer_header != 'error':
#             # detect a header
#             header_count += 1
#             is_receiving = True
#             pointer += pointer_header
#             continue
#         else:
#             pointer += 240
#     else:
#         # start decode bits
#         # re-locate
#         # pointer += detect_header(data[pointer:pointer+header_length], pointer) + 1
#         frame_buffer = data[pointer + header_length: pointer + header_length + symbol_per_frame * samples_per_symbol]
#         detected_frame += 1
#         decode(frame_buffer)
#         pointer += header_length + symbol_per_frame * samples_per_symbol
#         is_receiving = False
#
# while detected_frame < frame_num:
#     frame_buffer = data[pointer + header_length: pointer + header_length + symbol_per_frame * samples_per_symbol]
#     detected_frame += 1
#     decode(frame_buffer)
#     pointer += header_length + symbol_per_frame * samples_per_symbol
# end = time.time()
# print(header_count)
# print("Receiving time: ", end - start + 10)
