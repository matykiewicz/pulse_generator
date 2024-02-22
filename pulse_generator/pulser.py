import logging
import math
import sched
import time
from multiprocessing import Process, Queue
from threading import Thread
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
        time_sync: float,
    ):
        self.pulser_id = pulser_id
        self.external_config = external_config
        self.audio_dev = audio_dev
        self.device_id = audio_dev["index"]
        self.device_name = audio_dev["name"]
        self.sample_rate = int(audio_dev["default_samplerate"])
        min_length = int(self.sample_rate / external_config.frequency / 2)
        axis_x = np.arange(0, 1, 1 / self.sample_rate)[0:min_length]
        self.pulse_loud = np.zeros((min_length, 1), dtype=np.float32)
        self.pulse_loud[:, 0] = external_config.amplitude * signal.square(
            2 * np.pi * external_config.frequency * axis_x
        )
        self.skip = False
        self.interval_sec = 0
        self.process = Process(target=self.schedule_sounds)
        self.tempo_in_queue = Queue()
        self.tempo_out_queue = Queue()
        self.pause_queue = Queue()
        self.step_queue = Queue()
        self.steps = self.external_config.steps_init
        self.tempo_bpm = self.external_config.tempos_init
        self.time_sync = time_sync
        self.min_int_sec = self.test_play_speed()
        self.total_time_for_steps = 0
        self.reset_interval_and_tempo()
        self.next_schedule = self.time_sync + self.total_time_for_steps
        self.f = 0
        logging.info(
            f"Created {self.device_name} pulser with min int {self.min_int_sec} sec"
        )

    def detach_pulser(self):
        self.reset_interval_and_tempo()
        thread = Thread(target=self.process.start, daemon=True)
        thread.start()

    def test_play_speed(self) -> float:
        self.play_sound(1.0)
        time_now_0 = time.time()
        self.play_sound(0.0)
        time_now_1 = time.time()
        self.play_sound(1.0)
        time_now_2 = time.time()
        self.play_sound(0.0)
        time_now_3 = time.time()
        time_now_3 = time.time()
        time_int_1 = time_now_3 - time_now_2
        time_int_2 = time_now_2 - time_now_1
        time_int_3 = time_now_1 - time_now_0
        time_int = (
            math.ceil(max(time_int_1 * 100, time_int_2 * 100, time_int_3 * 100)) + 1
        )
        sd.stop()
        return time_int / 100

    def reset_interval_and_tempo(self):
        self.interval_sec = round(1 / (self.tempo_bpm / 60), 3)
        if self.interval_sec <= self.min_int_sec:
            self.interval_sec = self.min_int_sec
        self.tempo_bpm = round(1 / (self.interval_sec / 60))
        self.total_time_for_steps = self.steps * self.interval_sec

    def start_pause(self):
        self.pause_queue.put("pause")

    def set_tempo(self, tempo_bpm: int):
        self.tempo_in_queue.put(tempo_bpm)

    def get_tempo(self) -> int:
        if not self.tempo_out_queue.empty():
            return int(self.tempo_out_queue.get())
        else:
            return -1

    def play_sound(self, loud: float = 1.0):
        sd.stop()
        if loud:
            sd.play(
                self.pulse_loud,
                samplerate=self.sample_rate,
                blocking=True,
                device=self.device_name,
            )

    def schedule_sounds(self):
        scheduler = sched.scheduler(time.time, time.sleep)
        self.f = open("zzz.txt", "w")
        while True:
            scheduler.enterabs(self.next_schedule, 1, self.play_sounds)
            scheduler.run(blocking=True)
            if not self.pause_queue.empty():
                self.pause_queue.get()
                self.skip = True
            else:
                self.skip = False
            if not self.tempo_in_queue.empty():
                self.tempo_bpm = self.tempo_in_queue.get()
                self.reset_interval_and_tempo()
                self.tempo_out_queue.put(self.tempo_bpm)
            self.next_schedule += self.total_time_for_steps

    def play_sounds(self):
        should_be = self.next_schedule
        for i in range(self.steps):
            self.f.write(f"{should_be} {i+1.0} {1.0 * self.skip} {should_be - time.time()}\n")
            self.f.flush()
            should_be = should_be + self.interval_sec
            self.play_sound(1.0 - 1.0 * self.skip)
            is_now = time.time()
            time_diff = should_be - is_now
            if time_diff > 0 and i < (self.steps - 1):
                time.sleep(time_diff - 0.001)
