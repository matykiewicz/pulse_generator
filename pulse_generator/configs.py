from attrs import define


@define
class ExternalConfig:
    frequency: float
    amplitude: float
    audio_dev_match: str
    tempos_init: int
    steps_init: int
    waits_init: int


@define
class InternalConfig:
    first_start_delay: float = 2.0
    speed_diff: int = 5
    time_drift: float = 0.005
    sd_latency: float = 0.001
