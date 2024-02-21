import logging
from typing import Any, Dict

import numpy as np
import sounddevice as sd
from scipy import signal

from .configs import ExternalConfig


class Pulser:

    def __init__(
        self,
        pulser_id: int,
        external_config: ExternalConfig,
        audio_dev: Dict[str, Any],
        n_jobs: int = 3,
    ):
        self.pulser_id = pulser_id
        self.external_config = external_config
        self.audio_dev = audio_dev
        self.device_id = audio_dev["index"]
        self.device_name = audio_dev["name"]
        self.sample_rate = int(audio_dev["default_samplerate"])
        min_length = int(self.sample_rate / external_config.frequency / 2)
        axis_x = np.arange(0, 1, 1 / self.sample_rate)[0:min_length]
        self.pulse = np.zeros((min_length, 1), dtype=np.float32)
        self.pulse[:, 0] = external_config.amplitude * signal.square(
            2 * np.pi * external_config.frequency * axis_x
        )
        self.skip = False
        sd.default.device = self.device_id
        logging.info(f"Created {self.device_name} pulser")

    def start_skipping(self):
        self.skip = True

    def stop_skipping(self):
        self.skip = False

    def play(self):
        sd.stop()
        sd.play(
            self.pulse,
            samplerate=self.sample_rate,
            blocking=True,
            device=self.device_name,
        )

    def make_sound(self):
        if not self.skip:
            self.play()
