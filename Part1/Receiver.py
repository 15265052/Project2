import time

import matplotlib.pyplot as plt
import soundfile as sf
import sounddevice as sd
import numpy as np
from scipy import signal, integrate


def receive(file_name):
    sample_rate = 48000
    channels = 1
    record_seconds = 14
    print("start recording")
    frame = sd.rec(int(sample_rate * record_seconds),
                   samplerate=sample_rate,
                   channels=channels,
                   blocking=True,
                   dtype="float32")
    sf.write(file_name, frame, sample_rate)
    print("finish recording")


def gen_header():
    ''' header for 0.01 second'''
    t = np.linspace(0, 1, 48000, endpoint=True, dtype=np.float32)
    t = t[0:240]
    f_p = np.concatenate([np.linspace(2500, 8000, 120), np.linspace(8000, 2500, 120)])
    header = (np.sin(2 * np.pi * integrate.cumtrapz(f_p, t))).astype(np.float32)
    return header


def detect_header(sync):
    ref_header = gen_header()
    corr = signal.correlate(sync, ref_header, mode='full', method='fft')
    max = np.max(abs(corr))
    argmax = np.argmax(abs(corr))

    if max > threshold:
        print("max: ", max)
        return argmax - header_length + 1
    else:
        return 'error'


def decode(buffer):
    str1 = ''
    for i in range(symbol_per_frame):
        sample_buffer = buffer[i * samples_per_symbol:(i + 1) * samples_per_symbol]
        if len(sample_buffer) < samples_per_symbol:
            str = '0'
        else:
            str = decode_one_bit(sample_buffer)
        str1 = str1 + str
    write_file(str1)


def write_file(str):
    with open("OUTPUT.txt", 'a') as f:
        f.write(str)


def decode_one_bit(s_buffer):
    sum = np.sum(s_buffer * signal0)
    if sum >= 0:
        return '0'
    else:
        return '1'


# file_name = "test100.wav"
# receive(file_name)

start = time.time()
is_receiving = False
header = gen_header()
header_length = 239
sample_rate = 48000
header_count = 0
# skip the time when micro is heating

signal0 = [0.5, 0.5, -0.5, -0.5]
signal1 = [-0.5, -0.5, 0.5, 0.5]

frame_num = 100
detected_frame = 0
symbol_per_frame = 100
samples_per_symbol = 4
# with sf.SoundFile(file_name) as sf_dest:
#     data = sf_dest.read(dtype=np.float32)
with open('INPUT.txt', 'r') as file:
    file_data = file.read()
input_index = 0
symbols_in_frame = 100
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

corr = signal.correlate(data, header)
plt.plot(range(len(corr)), corr)
plt.show()
threshold = 2
data_length = len(data)
sync = []
pointer = 0
while detected_frame < frame_num and pointer < data_length:
    if not is_receiving:
        # fill in sync FIFO
        sync = data[pointer:pointer + header_length + symbol_per_frame * samples_per_symbol]
        pointer_header = detect_header(sync)
        if pointer_header != 'error':
            # detect a header
            header_count += 1
            is_receiving = True
            pointer += pointer_header
            continue
        else:
            pointer += 240
    else:
        # start decode bits
        # re-locate
        # pointer += detect_header(data[pointer:pointer+header_length], pointer) + 1
        frame_buffer = data[pointer + header_length: pointer + header_length + symbol_per_frame * samples_per_symbol]
        detected_frame += 1
        decode(frame_buffer)
        pointer += header_length + symbol_per_frame * samples_per_symbol
        is_receiving = False

while detected_frame < frame_num:
    frame_buffer = data[pointer + header_length: pointer + header_length + symbol_per_frame * samples_per_symbol]
    detected_frame += 1
    decode(frame_buffer)
    pointer += header_length + symbol_per_frame * samples_per_symbol
end = time.time()
print(header_count)
print("Receiving time: ", end - start + 10)
