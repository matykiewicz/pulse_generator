import math
import sched
import time
from multiprocessing import Process, Queue
from threading import Thread
from typing import Any, Dict, List

import numpy as np
import sounddevice as sd
from scipy import signal

from .configs import ArgsConfig, DynamicConfig, StaticConfig
from .key import is_keypress_readable, read_single_keypress


class Pulser:

    def __init__(
        self,
        args_config: ArgsConfig,
        static_config: StaticConfig,
        audio_dev: Dict[str, Any],
        dynamic_config: DynamicConfig,
        command_queue: Queue,
    ):
        self.args_config = args_config
        self.static_config = static_config
        self.command_queue = command_queue
        self.audio_dev = audio_dev
        self.device = audio_dev["index"]
        self.sample_rate = int(audio_dev["default_samplerate"])
        self.dynamic_config = dynamic_config
        min_length = int(self.sample_rate / args_config.frequency / 2)
        axis_x = np.arange(0, 1, 1 / self.sample_rate)[0:min_length]
        self.pulse = np.zeros((min_length, 1))
        self.pulse[:, 0] = args_config.amplitude * signal.square(
            2 * np.pi * args_config.frequency * axis_x
        )
        sd.default.device = self.device

    def sound(self):
        if self.dynamic_config.step == self.dynamic_config.steps:
            self.dynamic_config.part += 1
        self.dynamic_config.step = self.dynamic_config.step % self.dynamic_config.steps
        if (
            self.dynamic_config.stop
            and self.dynamic_config.pause + self.dynamic_config.wait
            == self.dynamic_config.part
        ):
            self.dynamic_config.stop = False
            self.dynamic_config.pause = 0
        if not self.dynamic_config.stop:
            sd.play(self.pulse, samplerate=self.sample_rate, blocking=True)
            self.dynamic_config.pause = self.dynamic_config.part
        self.dynamic_config.step += 1


class Keyboard:
    def __init__(self, static_config: StaticConfig, key_queue: Queue):
        self.static_config = static_config
        self.key_queue = key_queue

    def read(self) -> str:
        if is_keypress_readable():
            ch = read_single_keypress()[0]
        else:
            time.sleep(0.1)
            ch = "x"
        self.key_queue.put(ch)
        return ch


class Display:
    pass


class Scheduler:
    def __init__(self, args_config: ArgsConfig):
        self.args_config = args_config
        self.static_config = StaticConfig()
        self.audio_devs = self.get_audio_devs()
        self.key_queue = Queue()
        self.keyboard = Keyboard(
            static_config=self.static_config,
            key_queue=self.key_queue,
        )
        self.stop_thread = False
        self.command_queues: List[Queue] = list()
        self.processes: List[Process] = list()

    def get_audio_devs(self) -> List:
        all_devs = sd.query_devices()
        some_devs = list()
        for dev in all_devs:
            if (
                self.static_config.audio_dev_match in dev["name"]
                and dev["max_output_channels"] > 0
            ):
                some_devs.append(dev)
        return some_devs

    def keyboard_runner(self):
        while not self.stop_thread:
            ch = self.keyboard.read()
            if ch == "\x03":
                self.stop_thread = True

    def pulse_runner(
        self, time_sync: float, audio_dev: Dict[str, Any], command_queue: Queue
    ):
        dynamic_config = DynamicConfig(
            bpm=self.args_config.bpm_init, steps=self.static_config.steps_init
        )
        pulser = Pulser(
            args_config=self.args_config,
            static_config=self.static_config,
            dynamic_config=dynamic_config,
            audio_dev=audio_dev,
            command_queue=command_queue,
        )
        scheduler = sched.scheduler(time.time, time.sleep)
        new_time = time_sync
        while True:
            bpm = pulser.dynamic_config.bpm
            every_x_sec = 1 / (bpm / 60)
            new_time += every_x_sec
            scheduler.enterabs(new_time, priority=1, action=pulser.sound)
            scheduler.run(blocking=True)

    def start(self):
        thread = Thread(target=self.keyboard_runner)
        time_sync = math.ceil(time.time()) + self.static_config.first_start_delay
        processes: List[Process] = list()
        command_queues: List[Queue] = list()
        for dev in self.audio_devs:
            command_queue = Queue()
            process = Process(
                target=self.pulse_runner, args=(time_sync, dev, command_queue)
            )
            processes.append(process)
            command_queues.append(command_queue)
        for process in processes:
            process.start()
        self.processes += processes
        self.command_queues += command_queues
        thread.start()

    def finish(self):
        for process in self.processes:
            process.kill()
        self.stop_thread = True
