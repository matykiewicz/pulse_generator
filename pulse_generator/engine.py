from argparse import Namespace
from typing import List

import numpy as np
import sounddevice as sd


class Engine:
    pulse: np.ndarray

    @classmethod
    def start(cls, args: Namespace):
        frequency = args.frequency
        bpm_init = args.bpm_init
        length_pulse = args.length_pulse
        amplitude = args.amplitude
        audio_devs = cls.get_audio_devs()

    @staticmethod
    def get_audio_devs() -> List:
        devs = sd.query_devices()
