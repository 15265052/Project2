"""The config of Node1 is for the laptop of lenovo"""
import sounddevice as sd

asio_id = 8
asio_in = sd.AsioSettings(channel_selectors=[0])
asio_out = sd.AsioSettings(channel_selectors=[1])

INPUT_FILE = "INPUT1to2.bin"
OUTPUT_FILE = "OUTPUT2to1.bin"
