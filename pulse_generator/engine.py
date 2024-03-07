import logging
import math
import os
import time
from argparse import Namespace
from typing import List

import sounddevice as sd

from .configs import ExternalConfig, InternalConfig
from .pulser import Pulser
from .ui import UI


class Engine:

    def __init__(self, external_config: ExternalConfig):
        self.external_config = external_config
        self.internal_config = InternalConfig()
        self.audio_devs = self.get_audio_devs()
        self.pulser_devs = self.get_pulser_devs()
        self.ui = self.get_ui()
        if getattr(os, "sched_setaffinity", None) and self.internal_config.set_cpu_aff:
            pid = os.getpid()
            os.sched_setaffinity(pid, {0})  # type: ignore

    @classmethod
    def run(cls, args: Namespace, blocking: bool) -> "Engine":
        external_config = ExternalConfig(
            frequency=args.frequency,
            amplitude=args.amplitude,
            audio_dev_match=args.device_match,
            tempos_init=args.tempos_init,
            steps_init=args.steps_init,
            waits_init=args.waits_init,
            rands_init=args.rands_init,
            rands_mag=args.rands_magnitude,
        )
        engine = cls(external_config=external_config)
        if blocking:
            engine.ui.run()
        return engine

    def get_pulser_devs(self) -> List[Pulser]:
        pulser_devs: List[Pulser] = list()
        time_sync = math.ceil(time.time() + self.internal_config.first_start_delay)
        for pulser_id, audio_dev in enumerate(self.audio_devs):
            pulser = Pulser(
                pulser_id=pulser_id,
                external_config=self.external_config,
                audio_dev=audio_dev,
                time_sync=float(time_sync),
            )
            pulser.detach_pulser()
            pulser_devs.append(pulser)
        return pulser_devs

    def get_ui(self) -> UI:
        ui = UI(
            pulser_devs=self.pulser_devs,
            external_config=self.external_config,
        )
        return ui

    def get_audio_devs(self) -> List:
        all_devs = sd.query_devices()
        some_devs = list()
        for dev in all_devs:
            if (
                self.external_config.audio_dev_match in dev["name"]
                and dev["max_output_channels"] > 0
            ):
                some_devs.append(dev)
        logging.info(f"Found {len(some_devs)} audio devices")
        return some_devs

    def finish(self) -> "Engine":
        for pulser in self.ui.pulser_devs:
            pulser.process.kill()
        return self
