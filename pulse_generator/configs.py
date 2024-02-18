from attrs import define


@define
class ArgsConfig:
    bpm_init: int
    frequency: float
    amplitude: float


@define
class StaticConfig:
    audio_dev_match: str = "USB Audio"
    steps_init: int = 16
    first_start_delay: float = 2.0


@define
class DynamicConfig:
    bpm: int = 60
    steps: int = 16
    wait: int = 1
    step: int = 0
    stop: bool = False
    part: int = 0
    pause: int = 0
