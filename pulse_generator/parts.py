import logging
import math
import sched
import time
from multiprocessing import Process
from multiprocessing.shared_memory import ShareableList
from typing import Any, Callable, Dict, List

import numpy as np
import sounddevice as sd
from scipy import signal

from .configs import ArgsConfig, DynamicConfig, StaticConfig
from .ui import PulserApp


class Pulser:

    def __init__(
        self,
        pulser_id: int,
        args_config: ArgsConfig,
        static_config: StaticConfig,
        audio_dev: Dict[str, Any],
        dynamic_config: DynamicConfig,
        sharable_tempos: ShareableList,
        sharable_steps: ShareableList,
        sharable_stops: ShareableList,
        sharable_pauses: ShareableList,
    ):
        self.pulser_id = pulser_id
        self.args_config = args_config
        self.static_config = static_config
        self.shareable_tempos = sharable_tempos
        self.shareable_steps = sharable_steps
        self.shareable_stops = sharable_stops
        self.shareable_pauses = sharable_pauses
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
        self.shareable_steps[self.pulser_id] = self.dynamic_config.step


class Scheduler:
    def __init__(self, args_config: ArgsConfig):
        self.args_config = args_config
        self.static_config = StaticConfig()
        self.audio_devs = self.get_audio_devs()
        self.shareable_tempos = ShareableList()
        self.shareable_steps = ShareableList()
        self.shareable_stops = ShareableList()
        self.shareable_pauses = ShareableList()
        self.processes: List[Process] = list()

    def get_audio_devs(self) -> List:
        all_devs = sd.query_devices()
        some_devs = list()
        for dev in all_devs:
            if (
                self.args_config.audio_dev_match in dev["name"]
                and dev["max_output_channels"] > 0
            ):
                some_devs.append(dev)
        logging.info(f"Found {len(some_devs)} audio devices")
        return some_devs

    def pulse_runner(
        self,
        pulser_id: int,
        time_sync: float,
        audio_dev: Dict[str, Any],
        shareable_tempos: ShareableList,
        shareable_steps: ShareableList,
        shareable_stops: ShareableList,
        shareable_pauses: ShareableList,
    ):
        dynamic_config = DynamicConfig(
            bpm=self.args_config.bpm_init, steps=self.static_config.steps_init
        )
        pulser = Pulser(
            pulser_id=pulser_id,
            args_config=self.args_config,
            static_config=self.static_config,
            dynamic_config=dynamic_config,
            audio_dev=audio_dev,
            sharable_tempos=shareable_tempos,
            sharable_steps=shareable_steps,
            sharable_stops=shareable_stops,
            sharable_pauses=shareable_pauses,
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
        time_sync = math.ceil(time.time()) + self.static_config.first_start_delay
        processes: List[Process] = list()
        tempos = [self.args_config.bpm_init] * len(self.audio_devs)
        steps = [0] * len(self.audio_devs)
        stops = [False] * len(self.audio_devs)
        pauses = [False] * len(self.audio_devs)
        shareable_tempos = ShareableList(tempos)
        shareable_steps = ShareableList(steps)
        shareable_stops = ShareableList(stops)
        shareable_pauses = ShareableList(pauses)
        for pulser_id, dev in enumerate(self.audio_devs):
            process = Process(
                target=self.pulse_runner,
                args=(
                    pulser_id,
                    time_sync,
                    dev,
                    shareable_tempos,
                    shareable_steps,
                    shareable_stops,
                    shareable_pauses,
                ),
            )
            processes.append(process)
        for process in processes:
            process.start()
        self.processes += processes
        self.shareable_steps = shareable_steps
        self.shareable_tempos = shareable_tempos
        self.shareable_stops = shareable_stops
        self.shareable_pauses = shareable_pauses
        ui = PulserApp(
            audio_devs=self.audio_devs,
            current_tempo_getters=self.create_tempo_getters(),
            current_step_getters=self.create_step_getters(),
            current_tempo_setters=self.create_tempo_setters(),
            current_step_setters=self.create_step_setters(),
        )
        ui.run()

    def create_tempo_setters(self) -> List[Callable]:
        tempo_setters = list()
        for i in range(len(self.shareable_tempos)):

            def tempo_setter(x):
                self.shareable_tempos[i] = x

            tempo_setters.append(tempo_setter)
        return tempo_setters

    def create_step_setters(self) -> List[Callable]:
        step_setters = list()
        for i in range(len(self.shareable_steps)):

            def step_setter(x):
                self.shareable_steps[i] = x

            step_setters.append(step_setter)
        return step_setters

    def create_tempo_getters(self) -> List[Callable]:
        tempo_getters = list()
        for i in range(len(self.shareable_tempos)):
            tempo_getters.append(lambda: self.shareable_tempos[i])
        return tempo_getters

    def create_step_getters(self) -> List[Callable]:
        step_getters = list()
        for i in range(len(self.shareable_steps)):
            step_getters.append(lambda: self.shareable_steps[i])
        return step_getters

    def finish(self):
        for process in self.processes:
            process.kill()
        self.shareable_tempos.shm.close()
        self.shareable_steps.shm.close()
        self.shareable_stops.shm.close()
        self.shareable_pauses.shm.close()
        self.shareable_tempos.shm.unlink()
        self.shareable_steps.shm.unlink()
        self.shareable_stops.shm.unlink()
        self.shareable_pauses.shm.unlink()
