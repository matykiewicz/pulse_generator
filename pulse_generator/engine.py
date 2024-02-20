from argparse import Namespace

from .configs import ArgsConfig
from .parts import Scheduler


class Engine:

    def __init__(self, args_config: ArgsConfig):
        self.scheduler = Scheduler(args_config=args_config)

    @classmethod
    def start(cls, args: Namespace) -> "Engine":
        args_config = ArgsConfig(
            frequency=args.frequency,
            bpm_init=args.bpm_init,
            amplitude=args.amplitude,
            audio_dev_match=args.device_match,
        )
        engine = cls(args_config=args_config)
        engine.scheduler.start()
        return engine

    def finish(self) -> "Engine":
        self.scheduler.finish()
        return self
