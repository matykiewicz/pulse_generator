import logging
import os
import time
from multiprocessing import Process, Queue
from typing import Any, Dict

import numpy as np
import sounddevice as sd
from scipy import signal

from .configs import ExternalConfig, InternalConfig


class Pulser:

    def __init__(
        self,
        pulser_id: int,
        external_config: ExternalConfig,
        audio_dev: Dict[str, Any],
        time_sync: float,
    ):
        self.pulser_id = pulser_id
        self.external_config = external_config
        self.internal_config = InternalConfig()
        self.audio_dev = audio_dev
        self.device_id = audio_dev["index"]
        self.device_name = audio_dev["name"]
        self.sample_rate = 44100
        self.min_length = int(self.sample_rate / external_config.frequency / 2)
        axis_x = np.arange(0, 1, 1 / self.sample_rate)[0 : self.min_length]
        self.pulse_loud = np.zeros((self.min_length, 1), dtype=np.float32)
        self.pulse_loud[:, 0] = external_config.amplitude * signal.square(
            2 * np.pi * external_config.frequency * axis_x
        )
        self.pulse_loud[-1] = 0
        self.not_skip: bool = True
        self.interval_sec: float = 0.0
        self.tempo_in_queue: Queue[int] = Queue()
        self.tempo_out_queue: Queue[int] = Queue()
        self.pause_in_queue: Queue[str] = Queue()
        self.sound_in_queue: Queue[str] = Queue()
        self.steps = self.external_config.steps_init
        self.tempo_bpm = self.external_config.tempos_init
        self.time_sync: float = time_sync
        self.step: int = 1
        self.reset_interval_and_tempo()
        self.next_schedule = self.time_sync
        self.process = Process(target=self.start_schedule)
        logging.info(
            f"Created {self.device_name} pulser with time sync {self.time_sync}"
        )

    def detach_pulser(self):
        self.reset_interval_and_tempo()
        self.process.start()

    def reset_interval_and_tempo(self):
        self.interval_sec = round(1 / (self.tempo_bpm / 60), 3)
        self.tempo_bpm = round(1 / (self.interval_sec / 60))

    def play_sound(self):
        if self.sound_in_queue.empty():
            self.sound_in_queue.put("sound")

    def callback(self, out_data, frames, ts, status):
        self.run_tempo_in_command()
        if not self.sound_in_queue.empty():
            sound = self.sound_in_queue.get()
            out_data[:] = self.pulse_loud
            return None
        time_now = time.time()
        if time_now >= (self.next_schedule - self.internal_config.time_drift):
            if self.not_skip:
                out_data[:] = self.pulse_loud
            else:
                out_data[:] = self.internal_config.min_wave_val
            self.next_schedule += self.interval_sec
            if self.step == self.steps:
                self.run_pause_command()
                self.run_tempo_out_command()
            self.step = self.step % self.steps
            self.step += 1
        else:
            out_data[:] = self.internal_config.min_wave_val

    def start_schedule(self):
        pid = os.getpid()
        if getattr(os, "sched_setaffinity", None) and self.internal_config.set_cpu_aff:
            os.sched_setaffinity(pid, {self.pulser_id + 1})  # type: ignore
        stream = sd.OutputStream(
            device=self.device_id,
            samplerate=self.sample_rate,
            blocksize=self.min_length,
            dtype=np.float32,
            latency=self.internal_config.sd_latency,
            callback=self.callback,
        )
        with stream:
            while True:
                time.sleep(self.internal_config.main_python_sleep_s)
                sd.sleep(self.internal_config.main_sd_sleep_ms)

    def run_tempo_in_command(self):
        if not self.tempo_in_queue.empty():
            self.tempo_bpm = self.tempo_in_queue.get()

    def run_tempo_out_command(self):
        self.reset_interval_and_tempo()
        if self.tempo_out_queue.empty():
            self.tempo_out_queue.put(self.tempo_bpm)

    def run_pause_command(self):
        if not self.pause_in_queue.empty():
            self.pause_in_queue.get()
            self.not_skip = False
        else:
            self.not_skip = True
