import struct
import threading
import time

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
        print("MAC: switching from ", node_state, "to", dest_state)
        state_lock.acquire()
        node_state = dest_state
        state_lock.release()

    def run(self):
        global global_pointer
        global stream
        pointer = global_pointer
        print("Frame Detecting")
        if self.node_name == "Transmitter":
            # Transmitter to send data first
            s = time.time()
            data = self.gen_data("INPUT.bin")
            self.put_data_into_TxBuffer(data)
            self.switch_state("Tx")
            self.switch_to_Tx()
            print("Time: ", time.time()-s)
        # Tx Done to clear Tx Frame and set input index to 0
        global TxFrame
        global global_input_index
        global  detected_frames
        TxFrame = []
        global_input_index = 0

        while True:
            if pointer + block_size > len(global_buffer):
                continue
            if detected_frames >= frame_num:
                break
            block_buffer = global_buffer[pointer:pointer + block_size]
            pointer_frame = detect_preamble(block_buffer)
            if not pointer_frame == "error":
                detected_frames += 1
                print(detected_frames)
                pointer += pointer_frame
                if pointer + frame_length - preamble_length > len(global_buffer):
                    time.sleep(0.2)
                frame_detected = global_buffer[pointer: pointer + frame_length - preamble_length]
                self.put_frame_into_RxBuffer(frame_detected)
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

    """ generate data to send"""

    def gen_data(self, file_name):
        with open(file_name, 'rb') as file:
            file_data = file.read()
        file_data = struct.unpack("c" * len(file_data), file_data)
        input_index = 0
        bytes_in_frame = 25
        data = []
        for i in range(frame_num):
            data.append(np.zeros(240))
            data.append(preamble)
            for j in range(bytes_in_frame):
                for m in byte_to_str(file_data[input_index]):
                    if m == '0':
                        data.append(signal0)
                    else:
                        data.append(signal1)
                input_index += 1
        return np.concatenate(data)


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
            self.decode(RxFrame)
            RxFrame = []
            print("received one packet...")
            self.switch_state("MAC")
            self.switch_to_MAC()

    def switch_state(self, dest_state):
        global node_state
        global state_lock
        print("Rx: switching from ", node_state, "to", dest_state)
        state_lock.acquire()
        node_state = dest_state
        state_lock.release()

    def decode(self, frame_buffer):
        str_decoded = ""
        pointer = 0
        for i in range(bytes_per_frame):
            for j in range(bins_per_byte):
                decode_buffer = frame_buffer[pointer: pointer + samples_per_bin]
                str_decoded += self.decode_one_bit(decode_buffer)
                pointer += samples_per_bin
            write_to_file("OUTPUT.bin", str_to_byte(str_decoded))
            str_decoded = ""

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
            print("Tx: transmitting data")
            while global_input_index < len(TxFrame):
                global_status = "sending data"
            global_status = ""
            print("transmit done...")
            self.switch_state("MAC")
            self.switch_to_MAC()

    def switch_state(self, dest_state):
        global node_state
        global state_lock
        print("Tx: switching from ", node_state, "to", dest_state)
        state_lock.acquire()
        node_state = dest_state
        state_lock.release()

    def switch_to_MAC(self):
        global MAC_condition
        global Tx_condition
        print("Frame Detecting")
        MAC_condition.acquire()
        MAC_condition.notify()
        MAC_condition.release()
        Tx_condition.acquire()
        Tx_condition.wait()


def set_stream():
    sd.default.extra_settings = asio_in, asio_out
    sd.default.device[0] = asio_id
    sd.default.device[1] = asio_id
    stream = sd.Stream(sample_rate, blocksize=block_size, dtype=np.float32, callback=callback, channels=1)
    return stream


def callback(indata, outdata, frames, time, status):
    global global_buffer
    global global_pointer
    global global_status
    global_buffer = np.append(global_buffer, indata[:,0])

    if global_status == "":
        outdata.fill(0)

    if global_status == "sending data":
        global global_input_index
        global TxFrame
        if len(TxFrame) - global_input_index > block_size:
            outdata[:] = np.array(TxFrame[global_input_index:global_input_index + block_size]).reshape(block_size, 1)
        else:
            if len(TxFrame) - global_input_index >= 0:
                outdata[:] = np.append(TxFrame[global_input_index:],
                                       np.zeros(block_size - len(TxFrame) + global_input_index)).reshape(block_size, 1)
        global_input_index += block_size


stream = set_stream()
stream.start()
