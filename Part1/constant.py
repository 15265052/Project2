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
    t = t[0:120]
    f_p = np.concatenate([np.linspace(2500, 8000, 60), np.linspace(8000, 2500, 60)])
    preamble = (np.sin(2 * np.pi * integrate.cumtrapz(f_p, t))).astype(np.float32)
    return preamble


def detect_preamble(block_buffer):
    corr = np.abs(signal.correlate(block_buffer, preamble))
    plt.plot(range(len(corr)), corr)
    plt.show()
    if np.max(corr) > threshold:
        # detect preamble
        return np.argmax(corr) + 1
    else:
        return "error"


sample_rate = 48000

signal0 = (np.sin(2 * np.pi * 2000 * np.arange(0, 0.0005, 1 / sample_rate))).astype(np.float32)
signal1 = (-np.sin(2 * np.pi * 2000 * np.arange(0, 0.0005, 1 / sample_rate))).astype(np.float32)
latency = 0.0015
block_size = 1024
threshold = 20
asio_id = 10
asio_in = sd.AsioSettings(channel_selectors=[0])
asio_out = sd.AsioSettings(channel_selectors=[1])
preamble = gen_preamble()
RTX = gen_RTX()
CTX = gen_CTX()
preamble_length = len(preamble)
samples_per_symbol = 24
