import struct
import threading
import time

import matplotlib.pyplot as plt
import numpy as np

import matplotlib.pyplot as plt

from all_globals import *
from constant import *


class MAC(threading.Thread):
    """This class used to detect frame and switch state"""

    def __init__(self, node_name):
        super().__init__()
        self.node_name = node_name

    def switch_state(self, dest_state):
        global node_state
        global state_lock
        state_lock.acquire()
        node_state = dest_state
        state_lock.release()

    def run(self):
        global global_pointer
        global stream
        global TxFrame
        global retransmit_time

        global global_input_index
        global detected_frames
        TxFrame = []
        global_input_index = 0
        retransmit = 0
        pointer = global_pointer
        if self.node_name == "Transmitter":
            # Transmitter to send data first
            # generating all data with CRC but a frame with CRC per send
            data = self.gen_data("INPUT.bin")
            i = 0
            start = time.time()
            while i < frame_num:

                frame_with_CRC = data[i * frame_length_with_CRC: (i + 1) * frame_length_with_CRC]
                self.put_data_into_TxBuffer(frame_with_CRC)
                self.switch_state("Tx")
                self.switch_to_Tx()
                TxFrame = []
                i += 1
                if i % 49 and i >= 49:
                    self.check_ACK(0, i, data)
            while not self.check_ACK(0, frame_num, data):
                pass
            print("Transmission finished! time used: ", time.time()-start)
        print(1)
        # Tx Done to clear Tx Frame and set input index to 0

        while detected_frames < frame_num:
            if pointer + block_size > len(global_buffer):
                continue
            block_buffer = global_buffer[pointer:pointer + block_size]
            pointer_frame = detect_preamble(block_buffer)
            if not pointer_frame == "error":
                pointer += pointer_frame
                continue
                if pointer + frame_length_with_CRC - preamble_length > len(global_buffer):
                    time.sleep(0.2)
                # detect a frame, first to check its correctness
                frame_with_CRC_detected = global_buffer[pointer: pointer + frame_length_with_CRC - preamble_length]
                self.put_frame_into_RxBuffer(frame_with_CRC_detected)
                self.switch_state("Rx")
                self.switch_to_Rx()
                pointer += frame_length - preamble_length
                continue
            pointer += block_size
        global_pointer += pointer
        stream.stop()

    def put_data_into_TxBuffer(self, data):
        global TxFrame
        TxFrame = data[:]

    def put_frame_into_RxBuffer(self, frame):
        global RxFrame
        global RxFrame_lock
        RxFrame_lock.acquire()
        RxFrame = frame[:]
        RxFrame_lock.release()

    def switch_to_Rx(self):
        global MAC_condition
        global Rx_condition
        Rx_condition.acquire()
        Rx_condition.notify()
        Rx_condition.release()
        MAC_condition.acquire()
        MAC_condition.wait()

    def switch_to_Tx(self):
        global MAC_condition
        global Tx_condition
        Tx_condition.acquire()
        Tx_condition.notify()
        Tx_condition.release()
        MAC_condition.acquire()
        MAC_condition.wait()

    def decode_ACK(self, ACK_buffer):
        # first to convert all samples to bits
        str_decoded = ""
        pointer = 0
        for i in range(8):
            decode_buffer = ACK_buffer[pointer: pointer + samples_per_bin]
            if np.sum(decode_buffer * signal0) > 0:
                str_decoded += '0'
            else:
                str_decoded += '1'
            pointer += samples_per_bin
        return str_decoded

    """ generate data to send"""

    def gen_data(self, file_name):
        with open(file_name, 'rb') as file:
            file_data = file.read()
        file_data = struct.unpack("c" * len(file_data), file_data)
        input_index = 0
        data = []
        for i in range(frame_num):
            data.append(preamble)
            bytes_str_buffer = ""
            temp_str = bin(i)[2:]
            temp_str = (8 - len(temp_str)) * '0' + temp_str
            bytes_str_buffer += temp_str
            for j in range(bytes_per_frame):
                bytes_str_buffer += byte_to_str(file_data[input_index])
                input_index += 1
            for m in gen_CRC8(bytes_str_buffer):
                if m == '0':
                    data.append(signal0)
                else:
                    data.append(signal1)
        return np.concatenate(data)

    def check_ACK(self, range1, range2, data):
        global global_buffer
        global TxFrame
        global global_pointer
        while global_pointer < len(global_buffer):
            pointer_ACK = detect_preamble(global_buffer[global_pointer:global_pointer + 1024])
            if not pointer_ACK == 'error':
                global_pointer += pointer_ACK
                ACK_frame = int(self.decode_ACK(global_buffer[global_pointer:global_pointer + 48]), 2)
                if not ACK_confirmed[ACK_frame]:
                    print("ACK ", ACK_frame, " received!")
                    ACK_confirmed[ACK_frame] = True
                global_pointer += 48
            global_pointer += 1024
        global_pointer = len(global_buffer) >> 2
        res = True
        for i in range(range1, range2):
            if not ACK_confirmed[i]:
                res = False
                if time.time() - send_time[i] > retransmit_time and send_time[i] != 0:
                    print("ACK ", i, " time out, time used: ", time.time() - send_time[i], ", retransmit")
                    # retransmit
                    frame_with_CRC_re = data[i * frame_length_with_CRC: (i + 1) * frame_length_with_CRC]
                    TxFrame = []
                    self.put_data_into_TxBuffer(frame_with_CRC_re)
                    self.switch_state("Tx")
                    self.switch_to_Tx()
                    TxFrame = []
                    res = False
        return res


class Rx(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        """ receive data and write to file"""
        global Rx_condition
        Rx_condition.acquire()
        Rx_condition.wait()
        while True:
            global RxFrame
            if check_CRC8(self.decode_to_bits(RxFrame)):
                # frame is right
                self.send_ACK()
            RxFrame = []
            self.switch_state("MAC")
            self.switch_to_MAC()

    def switch_state(self, dest_state):
        global node_state
        global state_lock
        state_lock.acquire()
        node_state = dest_state
        state_lock.release()

    def send_ACK(self):
        global global_status
        global_status = "sending ACK"

    def decode_to_bits(self, frame_buffer):
        # first to convert all samples to bits
        str_decoded = ""
        pointer = 0
        for i in range(frame_length_with_CRC):
            decode_buffer = frame_buffer[pointer: pointer + samples_per_bin]
            str_decoded += self.decode_one_bit(decode_buffer)
            pointer += samples_per_bin
        return str_decoded

    def decode_one_bit(self, s_buffer):
        sum = np.sum(s_buffer * signal0)
        if sum >= 0:
            return '0'
        else:
            return '1'

    def switch_to_MAC(self):
        global MAC_condition
        global Rx_condition
        print("Frame Detecting")
        MAC_condition.acquire()
        MAC_condition.notify()
        MAC_condition.release()
        Rx_condition.acquire()
        Rx_condition.wait()


class Tx(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        """transmit data in the Tx Buffer"""
        global Tx_condition
        Tx_condition.acquire()
        Tx_condition.wait()
        while True:
            global global_status
            global TxFrame
            global global_input_index

            # transmitting
            while global_input_index < len(TxFrame):
                global_status = "sending data"
            global_status = ""
            global_input_index = 0
            self.switch_state("MAC")
            self.switch_to_MAC()

    def switch_state(self, dest_state):
        global node_state
        global state_lock
        state_lock.acquire()
        node_state = dest_state
        state_lock.release()

    def switch_to_MAC(self):
        global MAC_condition
        global Tx_condition
        MAC_condition.acquire()
        MAC_condition.notify()
        MAC_condition.release()
        Tx_condition.acquire()
        Tx_condition.wait()


def set_stream():
    sd.default.extra_settings = asio_in, asio_out
    sd.default.device[0] = asio_id
    sd.default.device[1] = asio_id
    sd.default.latency = latency
    stream = sd.Stream(sample_rate, blocksize=block_size, dtype=np.float32, callback=callback)
    return stream


def callback(indata, outdata, frames, time, status):
    global global_buffer
    global global_pointer
    global global_status
    global_buffer = np.append(global_buffer, indata[:, 0])

    if global_status == "":
        outdata.fill(0)

    if global_status == "sending data":
        global global_input_index
        global TxFrame
        if len(TxFrame) - global_input_index > frames:
            outdata[:] = np.array(TxFrame[global_input_index:global_input_index + frames]).reshape(frames, 1)
        else:
            if len(TxFrame) - global_input_index >= 0:
                outdata[:] = np.append(TxFrame[global_input_index:],
                                       np.zeros(frames - len(TxFrame) + global_input_index)).reshape(frames, 1)
        global_input_index += frames

    if global_status == "sending ACK":
        outdata[:] = np.append(preamble, np.zeros(block_size - preamble_length)).reshape(1024, 1)
        global_status = ""


stream = set_stream()
stream.start()
