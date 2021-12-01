import struct
import time

from all_globals import *
from constant import *


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
        TxFrame = []
        global_input_index = 0
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
                self.switch_to_Tx()
                # send_time[i] = time.time()
                TxFrame = []
                i += 1
            #     if i % 49 == 0 and i >= 49:
            #         self.check_ACK(0, i, data)
            # while not self.check_ACK(0, frame_num, data):
            #     pass
            print("Transmission finished! time used: ", time.time() - start)
        # Tx Done to clear Tx frame and set input index to 0
        else:
            TxFrame = []
            flag = True
            start = 0
            global_input_index = 0
            while detected_frames < frame_num:
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
            print("receive finished! time used: ", end - start)
            for frame in frame_rece:
                write_byte_to_file("OUTPUT.bin", frame)

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
        """
        check if ACK received from range1 to range2
        retransmit frame if time out
        """
        global global_buffer
        global TxFrame
        global global_pointer
        while global_pointer < len(global_buffer):
            pointer_ACK = detect_preamble(global_buffer[global_pointer:global_pointer + 1024])
            if not pointer_ACK == 'error':
                global_pointer += pointer_ACK
                ACK_frame = int(self.decode_ACK(global_buffer[global_pointer:global_pointer + samples_per_bin*8]), 2)
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
                    frame_retransmit[i] += 1
                    if frame_retransmit[i] >= max_retransmit:
                        print("link error! exit")
                        exit(-1)
                    else:
                        print("ACK ", i, " time out, time used: ", time.time() - send_time[i], ", retransmit")
                        # retransmit
                        frame_with_CRC_re = data[i * frame_length_with_CRC: (i + 1) * frame_length_with_CRC]
                        TxFrame = []
                        self.put_data_into_TxBuffer(frame_with_CRC_re)
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
        global detected_frames
        global RxFrame
        global frame_confirmed
        global frame_rece
        Rx_condition.acquire()
        Rx_condition.wait()
        while True:
            decoded_bits = self.decode_to_bits(RxFrame)
            if check_CRC8(decoded_bits):
                # frame is right
                n_frame = int(decoded_bits[:8], 2)
                print("sending ACK", n_frame)
                self.send_ACK(n_frame)
                if not frame_confirmed[n_frame]:
                    frame_confirmed[n_frame] = True
                    frame_rece[n_frame] = decoded_bits[8:]
                    detected_frames += 1
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
        ACK_buffer.append(ACK_predefined[n_frame])
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

            # transmitting
            while global_input_index < len(TxFrame):
                global_status = "sending data"
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
    stream = sd.Stream(sample_rate, blocksize=block_size, dtype=np.float32, callback=callback, channels=1)
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
        global ACK_buffer
        global ACK_pointer
        global_status = ""
        outdata[:] = np.append(ACK_buffer[ACK_pointer], np.zeros(frames - len(ACK_buffer[ACK_pointer]))).reshape(frames,
                                                                                                                 1)
        ACK_pointer += 1
