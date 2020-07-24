import pyaudio
import wave
import threading
import time
import subprocess

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "tmp/mic_tmp.wav"


class recorder:
    def __init__(self):
        self.going = False
        self.process = None
        self.filename = "ScreenCapture.mpg"

    def record(self, filename):
        try:
            if self.process.is_alive():
                self.going = False
        except AttributeError:
            pass
        self.process = threading.Thread(target=self._record)
        self.process.start()
        self.filename = filename

    def _record(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        print("* mic recording")

        frames = []

        self.going = True

        while self.going:
            data = stream.read(CHUNK)
            frames.append(data)

        print("* done mic recording")

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

    def stop_recording(self):
        self.going = False