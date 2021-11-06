import time

import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
from scipy import signal, integrate


def gen_preamble():
    t = np.linspace(0, 1, 48000, endpoint=True, dtype=np.float32)
    t = t[0:60]
    f_p = np.concatenate([np.linspace(1000, 10000, 30), np.linspace(10000, 1000, 30)])
    preamble = (np.sin(2 * np.pi * integrate.cumtrapz(f_p, t))).astype(np.float32)
    return preamble


def detect_preamble(block_buffer):
    corr = signal.correlate(block_buffer, preamble)
    if np.max(corr) > threshold:
        # detect preamble
        return np.argmax(corr) + 1
    else:
        return "error"


def write_to_file(file_name, data):
    with open(file_name, 'ab') as f:
        f.write(data)


def clean_file(file_name):
    with open(file_name, 'w') as f:
        f.truncate()


def str_to_one_byte(str_buffer):
    temp = int(str_buffer, 2)
    return temp.to_bytes(1, 'big')


def str_to_byte(all_str):
    bytes_res = []
    for i in range(bytes_per_frame):
        bytes_res.append(str_to_one_byte(all_str[i * bins_per_byte:(i + 1) * bins_per_byte]))
    return bytes_res


def byte_to_str(byte):
    temp_bin = int.from_bytes(byte, 'big')
    bi = bin(temp_bin)[2:]
    return (8 - len(bi)) * "0" + bi


def write_byte_to_file(file_name, decoded_bits):
    for byte in str_to_byte(decoded_bits):
        write_to_file(file_name, byte)


def gen_CRC8(string):
    loc = [8, 2, 1, 0]
    p = [0 for i in range(9)]
    for i in loc:
        p[i] = 1
    info = list(string)
    info = [int(i) for i in info]
    info1 = list(string)
    info1 = [int(i) for i in info1]
    # print(info)
    times = len(info)
    n = 9
    for i in range(8):
        info.append(0)
    consult = []
    for i in range(times):
        if info[i] == 1:
            consult.append(1)
            for j in range(n):
                info[j + i] = info[j + i] ^ p[j]
        else:
            consult.append(0)
    mod = info[-8::]
    # print(mod)
    code = info1.copy()
    # print(code)
    for i in mod:
        code.append(i)
    code = "".join('%s' % id for id in code)
    # print(code)
    return code


def check_CRC8(string):
    loc = [8, 2, 1, 0]
    p = [0 for i in range(9)]
    for i in loc:
        p[i] = 1
    info = list(string)
    info = [int(i) for i in info]
    times = len(info)
    n = 9
    consult = []
    for i in range(times - 8):
        if info[i] == 1:
            consult.append(1)
            for j in range(n):
                info[j + i] = info[j + i] ^ p[j]
        else:
            consult.append(0)
    mod = info[-8::]
    # print(mod)
    mod = int("".join('%s' % id for id in mod))
    if mod == 0:
        return True
    else:
        return False


def modulate_string(string):
    modulated_array = []
    for i in string:
        if i == '0':
            modulated_array.append(signal0)
        else:
            modulated_array.append(signal1)
    return modulated_array


sample_rate = 48000

signal0 = (np.sin(2 * np.pi * 9800 * np.arange(0, 0.000125, 1 / sample_rate))).astype(np.float32)
signal1 = (-np.sin(2 * np.pi * 9800 * np.arange(0, 0.000125, 1 / sample_rate))).astype(np.float32)

latency = 0.0015
block_size = 2048
threshold = 10

preamble = gen_preamble()
preamble_length = len(preamble)

bins_per_byte = 8
samples_per_bin = 6
frame_num = 250
bytes_per_frame = 25
frame_length = samples_per_bin * bins_per_byte * bytes_per_frame + preamble_length + 8 * samples_per_bin
frame_length_with_CRC = frame_length + 28 * samples_per_bin
frame_length_in_bit = bins_per_byte * (bytes_per_frame + 1) + 20
frame_length_in_bit_with_CRC = frame_length_in_bit + 8

node1_addr = "10010011"
node2_addr = "01101100"

# 8: frame num bits 8: dest bits 8: src bits 4: type bits 8: CRC bits
ACK_length_in_bit = 8 + 8 + 8 + 4 + 8
ACK_length = samples_per_bin * ACK_length_in_bit

retransmit_time = 1
max_retransmit = 10
