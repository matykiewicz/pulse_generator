from typing import List

from attrs import define


@define
class ExternalConfig:
    frequency: float
    amplitude: float
    audio_dev_match: str
    tempos_init: int
    steps_init: int
    waits_init: int
    rands_init: int
    rands_mag: float


@define
class InternalConfig:
    first_start_delay: float = 5.0
    speed_diff: int = 20
    time_drift: float = 0.005
    sd_latency: float = 0.0005
    min_wave_val: float = 0.0005
    main_python_sleep_s: float = 10.0
    main_sd_sleep_ms: float = 1
    set_cpu_aff: bool = False
    rand_quants: int = 4
    shuffle_programs: List[str] = [
        "0-+",
        "0++",
        "+++",
        "+-+",
        "-++",
        "--+",
        "0--",
        "0+-",
        "++-",
        "+--",
        "-+-",
        "---",
    ]
    shuffle_program = "0-+"
