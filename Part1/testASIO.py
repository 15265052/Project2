import sounddevice as sd
import soundfile as sf

data, sample_rate = sf.read("test100.wav")
asio_id = 16

asio_in = sd.AsioSettings(channel_selectors=[0])
asio_out = sd.AsioSettings(channel_selectors=[1])
sd.default.extra_settings = None, asio_out
sd.default.latency = 0.002
sd.default.device[1] = asio_id
sd.play(data, blocking=True, samplerate=sample_rate, mapping=None)
