import struct
import threading
import time

import matplotlib.pyplot as plt
import numpy as np

from Part3.all_globals import *
from Part3.config.Type import data_frame
from Part3.config.node1 import *
from Part3.config.ACKConfig import *

class MAC(threading.Thread):
    """This class used to detect frame and switch state"""

    def __init__(self, node_name):
        super().__init__()
        self.node_name = node_name

    def run(self):
        global global_pointer
        global stream
        global frame_rece
        global TxFrame
        global retransmit_time
        global global_input_index
        global detected_frames
        global is_noisy
        TxFrame = []
        global_input_index = 0
        pointer = global_pointer
        # Node1 Transmits first
        data = self.gen_data(INPUT_FILE)
        i = 0
        start = time.time()
        for frame in data:
            while is_noisy:
                # if the channel is noisy, backoff 0.05s
                time.sleep(0.05)
            self.put_data_into_TxBuffer(frame.get_modulated_frame())
            self.switch_to_Tx()
            send_time[i] = time.time()
            TxFrame = []
            i += 1
            if i % 1 == 0 and i >= 1:
                while not self.check_ACK(i-1, i, data):
                    pass

        print("Node1 transmission finished! time used: ", time.time() - start)
        # Tx Done to clear Tx frame and set input index to 0
        # Then Node1 to Receive
        TxFrame = []
        flag = True
        start = 0
        global_input_index = 0
        while detected_frames < frame_num_2:
            if pointer + block_size > len(global_buffer):
                continue
            block_buffer = global_buffer[pointer: pointer + block_size]
            pointer_frame = detect_preamble(block_buffer)
            if not pointer_frame == "error":
                if flag:
                    start = time.perf_counter()
                    flag = False
                pointer += pointer_frame
                # detect a frame, first to check its correctness
                if pointer + frame_length_with_CRC - preamble_length > len(global_buffer):
                    time.sleep(0.1)
                frame_with_CRC_detected = global_buffer[pointer: pointer + frame_length_with_CRC - preamble_length]
                self.put_frame_into_RxBuffer(frame_with_CRC_detected)
                self.switch_to_Rx()
                pointer += frame_length - preamble_length
                continue
            pointer += block_size
        end = time.perf_counter()
        global_pointer += pointer
        print("Node1 receive finished! time used: ", end - start)
        for frame in frame_rece:
            write_byte_to_file(OUTPUT_FILE, frame)

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

    def decode_ACK_bits(self, ACK_buffer):
        # first to convert all samples to bits
        str_decoded = ""
        pointer = 0
        for i in range(ACK_length_in_bit):
            decode_buffer = ACK_buffer[pointer: pointer + samples_per_bin]
            if np.sum(decode_buffer * signal0) > 0:
                str_decoded += '0'
            else:
                str_decoded += '1'
            pointer += samples_per_bin
        return str_decoded

    """ generate data to send"""

    def gen_data(self, file_name):
        """
        generate all data to be send, where data is an array containing all of the frames
        like: data = [frame1, frame2,....], the frames are all  PHYFrame Object
        """
        with open(file_name, 'rb') as file:
            file_data = file.read()
        file_data = struct.unpack("c" * len(file_data), file_data)
        input_index = 0
        data = []
        for i in range(frame_num):
            load_bit = ""
            for j in range(bytes_per_frame):
                load_bit += byte_to_str(file_data[input_index])
                input_index += 1
            phy_frame = PhyFrame()
            phy_frame.set_num(i)
            phy_frame.set_load(node2_addr, node1_addr, data_frame, load_bit)
            data.append(phy_frame)
        return data

    def check_ACK(self, range1, range2, data):
        """
        check if ACK received from range1 to range2
        retransmit frame if time out
        """
        global global_buffer
        global TxFrame
        global global_pointer
        global send_time
        while global_pointer < len(global_buffer):
            pointer_ACK = detect_preamble(global_buffer[global_pointer:global_pointer + 1024])
            if not pointer_ACK == 'error':
                global_pointer += pointer_ACK
                ACK_frame_array = global_buffer[global_pointer: global_pointer + ACK_length]
                ACK_frame = PhyFrame()
                ACK_frame.from_array(self.decode_ACK_bits(ACK_frame_array))
                if ACK_frame.check() and ACK_frame.get_destination() == node1_addr:
                    if not ACK_confirmed[ACK_frame.get_decimal_num()]:
                        print("ACK ", ACK_frame.get_decimal_num(), " received!")
                        ACK_confirmed[ACK_frame.get_decimal_num()] = True
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
                    self.put_data_into_TxBuffer(data[i].get_modulated_frame())
                    self.switch_to_Tx()
                    TxFrame = []
                    send_time[i] =time.time()
        return res


class Rx(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        """ receive data and write to file"""
        global Rx_condition
        global detected_frames
        global RxFrame
        global frame_confirmed
        global frame_rece
        Rx_condition.acquire()
        Rx_condition.wait()
        while True:
            decoded_bits = self.decode_to_bits(RxFrame)
            physical_frame = PhyFrame()
            physical_frame.from_array(decoded_bits)
            if physical_frame.check() and physical_frame.get_destination() == node1_addr and physical_frame.get_type() == data_frame:
                # correct frame
                n_frame = physical_frame.get_decimal_num()
                print("send ACK ", n_frame)
                self.send_ACK(n_frame)
                if not frame_confirmed[n_frame]:
                    detected_frames += 1
                    frame_confirmed[n_frame] = 1
                    frame_rece[n_frame] = physical_frame.get_load().get_data()
            else:
                print("CRC broken!")
            # wait until ACK was sent
            while global_status != "":
                pass
            RxFrame = []
            self.switch_to_MAC()

    @staticmethod
    def send_ACK(n_frame):
        global global_status
        global ACK_buffer
        global ACK_predefined
        global is_noisy
        ACK_buffer.append(ACK_predefined[n_frame])
        while is_noisy:
            time.sleep(0.05)
        global_status = "sending ACK"

    def decode_to_bits(self, frame_buffer):
        # first to convert all samples to bits
        str_decoded = ""
        for i in range(frame_length_in_bit_with_CRC):
            decode_buffer = frame_buffer[i * samples_per_bin: (i + 1) * samples_per_bin]
            str_decoded += self.decode_one_bit(decode_buffer)
        return str_decoded

    @staticmethod
    def decode_one_bit(s_buffer):
        sum = np.sum(s_buffer * signal0)
        if sum >= 0:
            return '0'
        else:
            return '1'

    @staticmethod
    def switch_to_MAC():
        global MAC_condition
        global Rx_condition
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

            global_input_index = 0
            # transmitting
            while global_input_index < len(TxFrame):
                global_status = "sending data"
            Idle()
            global_status = ""
            global_input_index = 0
            print("transmit done...")
            self.switch_to_MAC()

    @staticmethod
    def switch_to_MAC():
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
    stream = sd.Stream(sample_rate, blocksize=2048, dtype=np.float32, callback=callback, channels=1)
    return stream

def Idle():
    global global_status
    Idle_start = time.time()
    while time.time() - Idle_start < 0.09:
        global_status = "Idle"

def callback(indata, outdata, frames, time, status):
    global global_buffer
    global global_pointer
    global global_status
    global is_noisy
    global silent_threshold
    if np.average(indata[:, 0]) > silent_threshold:
        is_noisy = True
    else:
        is_noisy = False

    if global_status == "":
        # when not sending, then receiving
        global_buffer = np.append(global_buffer, indata[:, 0])
        outdata.fill(0)

    if global_status == "Idle":
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
        global ACK_buffer
        global ACK_pointer
        global_status = ""
        outdata[:] = np.append(ACK_buffer[ACK_pointer], np.zeros(frames - len(ACK_buffer[ACK_pointer]))).reshape(frames,
                                                                                                                 1)
        ACK_pointer += 1
