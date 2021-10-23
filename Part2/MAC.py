import threading
from all_globals import *
from constant import *


class MAC(threading.Thread):
    """This class used to detect frame and switch state"""

    def __init__(self, node_name, state_lock, RxFrame_lock):
        super().__init__()
        self.node_name = node_name
        self.state_lock = state_lock
        self.RxFrame_lock = RxFrame_lock

    def switch_state(self, dest_state):
        global node_state
        print("MAC: switching from ", node_state, "to", dest_state)
        self.state_lock.acquire()
        node_state = dest_state
        self.state_lock.release()

    def run(self):
        global global_pointer
        pointer = global_pointer
        while True:
            # wait transmitter's RTX
            if pointer + block_size > len(global_buffer):
                continue
            block_buffer = global_buffer[pointer:pointer + block_size]
            pointer_frame = detect_preamble(block_buffer)
            if not pointer_frame == "error":
                pointer += pointer_frame
                frame_detected = global_buffer[pointer: pointer + len(frame_length) - preamble_length]
                self.put_frame_into_RxBuffer(frame_detected)
            pointer += block_size
        global_pointer += pointer

    def put_frame_into_RxBuffer(self, frame):
        global RxFrame
        self.RxFrame_lock.acquire()
        RxFrame = frame[:]
        self.RxFrame_lock.release()
