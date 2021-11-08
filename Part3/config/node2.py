"""The config is for the laptop of thinkbook"""
import sounddevice as sd

asio_id = 14
asio_in = sd.AsioSettings(channel_selectors=[0])
asio_out = sd.AsioSettings(channel_selectors=[1])

INPUT_FILE = "INPUT2to1.bin"
OUTPUT_FILE = "OUTPUT1to2.bin"
