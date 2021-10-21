import numpy as np
from scipy import signal, integrate
import time
import sounddevice as sd
import matplotlib.pyplot as plt


def transmit(file_name):
    sample_rate = 48000
    signal0 = [0.5, 0.5, -0.5, -0.5]
    signal1 = [-0.5, -0.5, 0.5, 0.5]
    with open(file_name, 'r') as file:
        file_data = file.read()
    input_index = 0
    symbols_in_frame = 100
    frame_num = int(len(file_data) / symbols_in_frame)
    if frame_num * 100 < len(file_data):
        frame_num += 1
    header = gen_header()
    data = []
    for i in range(frame_num):
        data.append(header)
        for j in range(symbols_in_frame):
            if file_data[input_index] == '0':
                data.append(signal0)
            else:
                data.append(signal1)
            input_index += 1
    data = np.concatenate(data)
    play_with_ASIO(data, sample_rate, 0.005)


def gen_header():
    """ header for 0.01 second"""
    t = np.linspace(0, 1, 48000, endpoint=True, dtype=np.float32)
    t = t[0:240]
    f_p = np.concatenate([np.linspace(2500, 8000, 120), np.linspace(8000, 2500, 120)])
    header = (np.sin(2 * np.pi * integrate.cumtrapz(f_p, t))).astype(np.float32)
    return header


def play_with_ASIO(data, sample_rate, latency):
    """use ASIO4all to play audio"""
    asio_id = 12
    asio_out = sd.AsioSettings(channel_selectors=[1])
    sd.default.extra_settings = None, asio_out
    sd.default.latency = latency
    sd.default.device[1] = asio_id
    sd.play(data, blocking=True, samplerate=sample_rate, mapping=None)
    sd.wait()


start = time.time()
transmit("INPUT.txt")
end = time.time()
print("Transmitting time: ", end - start)
