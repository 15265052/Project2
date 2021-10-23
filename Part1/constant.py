import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
from scipy import signal, integrate


def gen_RTX():
    """
    RTX for inform receiver that it is about to transmit data
    structure: | preamble | 1010101 |
    """
    RTX = []
    RTX_array = [1, 0, 1, 0, 1, 0, 1]
    RTX.append(gen_preamble())
    for i in RTX_array:
        if i == 0:
            RTX.append(signal0)
        else:
            RTX.append(signal1)

    return np.concatenate(RTX)


def gen_CTX():
    """
    CTX for confirm that it can receive data
    structure: | preamble | 0101010 |
    """
    CTX = []
    CTX_array = [0, 1, 0, 1, 0, 1, 0]
    CTX.append(gen_preamble())
    for i in CTX_array:
        if i == 0:
            CTX.append(signal0)
        else:
            CTX.append(signal1)

    return np.concatenate(CTX)


def gen_preamble():
    """ header for 0.01 second"""
    t = np.linspace(0, 1, 48000, endpoint=True, dtype=np.float32)
    t = t[0:60]
    f_p = np.concatenate([np.linspace(1000, 10000, 30), np.linspace(10000, 1000, 30)])
    preamble = (np.sin(2 * np.pi * integrate.cumtrapz(f_p, t))).astype(np.float32)
    return preamble


def detect_preamble(block_buffer):
    corr = signal.correlate(block_buffer, preamble)
    if np.max(corr) > threshold:
        # detect preamble
        print("detected a frame!")
        plt.plot(range(len(corr)), corr)
        plt.show()
        return np.argmax(corr) + 1
    else:
        return "error"


def write_to_file(file_name, data):
    with open(file_name, 'a') as f:
        f.write(data)

def clean_file(file_name):
    with open(file_name, 'w') as f:
        f.truncate()

sample_rate = 48000

signal0 = (np.sin(2 * np.pi * 2000 * np.arange(0, 0.0005, 1 / sample_rate))).astype(np.float32)
signal1 = (-np.sin(2 * np.pi * 2000 * np.arange(0, 0.0005, 1 / sample_rate))).astype(np.float32)
latency = 0.0015
block_size = 1024
threshold = 10
asio_id = 10
asio_in = sd.AsioSettings(channel_selectors=[0])
asio_out = sd.AsioSettings(channel_selectors=[1])
preamble = gen_preamble()
RTX = gen_RTX()
CTX = gen_CTX()
preamble_length = len(preamble)
samples_per_symbol = 24
frame_num = 100
frame_length = samples_per_symbol * 100 + preamble_length
