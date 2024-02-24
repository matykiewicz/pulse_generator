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
    first_start_delay: float = 4.0
    speed_diff: int = 10
    time_drift: float = 0.005
    sd_latency: float = 0.001
    min_wave_val: float = 0.0005
    main_python_sleep_s: float = 2.0
    main_sd_sleep_ms: float = 1
    set_cpu_aff: bool = False
