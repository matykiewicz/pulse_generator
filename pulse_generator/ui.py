import random
import time
from typing import List

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Button, Footer, Static

from .configs import ExternalConfig, InternalConfig
from .pulser import Pulser


class PulserDisplay(Static):
    tempos_val = reactive(0)
    tempo_val = reactive(0)
    steps_val = reactive(0)
    step_val = reactive(0)
    waits_val = reactive(0)
    wait_val = reactive(0)
    rands_val = reactive(0)
    rand_val = reactive(0)
    shuffle_val = reactive(0)
    stopped = reactive(False)

    def __init__(
        self,
        dev_name: str,
        tempos_init: int,
        tempo_init: int,
        steps_init: int,
        waits_init: int,
        rands_init: int,
        pulser: Pulser,
        pause_button: Button,
        stop_button: Button,
    ):
        super().__init__()
        self.internal_config = InternalConfig()
        self.pause_button = pause_button
        self.stop_button = stop_button
        self.dev_name = dev_name.replace(" ", "_").replace("-", "_").replace("__", "_")
        self.tempos_val = tempos_init
        self.tempo_val = tempo_init
        self.steps_val = steps_init
        self.step_val = steps_init
        self.waits_val = waits_init
        self.wait_val = waits_init
        self.rands_val = rands_init
        self.rand_val = rands_init
        self.shuffle_val = self.internal_config.shuffle_programs.index(
            self.internal_config.shuffle_program
        )
        self.commands: List[str] = list()
        self.pulser = pulser
        self.interval_sec: float = 0.0
        self.reset_interval_and_tempo()
        self.next_schedule = self.pulser.next_schedule
        self.randoms = [0.0] * (self.steps_val // 2)
        self.set_timer(
            delay=self.next_schedule - time.time() - self.internal_config.time_drift,
            callback=self.run_schedule,
        )

    def reset_interval_and_tempo(self):
        self.interval_sec = round(1 / (self.tempo_val / 60), 3)
        self.tempos_val = round(1 / (self.interval_sec / 60))

    def run_schedule(self) -> None:
        if self.step_val == self.steps_val:
            self.run_wait_command()
            self.run_rand_command()
            self.run_pause_start_stop_rand_command()
        step_val = self.step_val
        step_val = step_val % self.steps_val
        step_val += 2
        self.step_val = step_val
        if self.step_val == 2:
            self.run_tempo_out_command()
        self.next_schedule += self.interval_sec
        self.set_timer(
            delay=self.next_schedule - time.time() - self.internal_config.time_drift,
            callback=self.run_schedule,
        )

    def run_wait_command(self):
        if self.wait_val < self.waits_val:
            wait_val = self.wait_val
            wait_val += 1
            if wait_val == self.waits_val:
                self.pause_button.disabled = False
                self.stop_button.disabled = False
            self.wait_val = wait_val

    def run_rand_command(self):
        if self.rand_val < self.rands_val:
            rand_val = self.rand_val
            rand_val += 1
            if rand_val == self.rands_val:
                self.pause_button.disabled = False
                self.stop_button.disabled = False
            self.rand_val = rand_val

    def run_pause_start_stop_rand_command(self):
        if len(self.commands) > 0:
            command = self.commands.pop()
            if command == "pause":
                self.wait_val = 0
            elif command == "stop":
                self.stopped = True
            elif command == "start":
                self.stopped = False
            elif command == "rand":
                self.rand_val = 0
        if self.stopped and self.pulser.pause_in_queue.empty():
            self.pulser.pause_in_queue.put("pause")

    def run_tempo_out_command(self):
        if not self.pulser.tempo_out_queue.empty():
            self.tempo_val = self.pulser.tempo_out_queue.get()
            self.reset_interval_and_tempo()

    def update_all(self):
        self.update(
            f"D:{self.dev_name} T: {self.tempo_val:03}/{self.tempos_val:03} "
            f"S:{self.step_val:02}/{self.steps_val:02} "
            f"W:{self.wait_val:02}/{self.waits_val:02} "
            f"R:{self.rand_val:02}/{self.rands_val:02} P:{self.shuffle_val}"
        )

    def watch_step_val(self) -> None:
        self.update_all()

    def watch_tempo_val(self) -> None:
        self.update_all()

    def watch_wait_val(self) -> None:
        self.update_all()

    def watch_rand_val(self) -> None:
        self.update_all()

    def watch_steps_val(self) -> None:
        self.update_all()

    def watch_tempos_val(self) -> None:
        self.update_all()

    def watch_waits_val(self) -> None:
        self.update_all()

    def watch_rands_val(self) -> None:
        self.update_all()

    def watch_shuffle_val(self) -> None:
        self.update_all()

    def start(self) -> bool:
        if len(self.commands) == 0:
            self.commands.append("start")
            if not self.pulser.pause_in_queue.empty():
                self.pulser.pause_in_queue.get()
            return True
        else:
            return False

    def stop(self) -> bool:
        if len(self.commands) == 0 and self.pulser.pause_in_queue.empty():
            self.commands.append("stop")
            self.pulser.pause_in_queue.put("pause")
            return True
        else:
            return False

    def pause(self) -> bool:
        if len(self.commands) == 0 and self.pulser.pause_in_queue.empty():
            self.commands.append("pause")
            self.pause_button.disabled = True
            self.stop_button.disabled = True
            for i in range(self.waits_val):
                self.pulser.pause_in_queue.put("pause")
            return True
        else:
            return False

    def rand(self) -> bool:
        if len(self.commands) == 0 and self.pulser.rand_in_queue.empty():
            self.commands.append("rand")
            self.pause_button.disabled = True
            self.stop_button.disabled = True
            shuffle_prog = self.internal_config.shuffle_programs[self.shuffle_val]
            for i in range(self.rands_val):
                j = i % 2
                for _rand_ in self.randoms:
                    if shuffle_prog[2:3] == "+":
                        self.pulser.rand_in_queue.put(_rand_)
                    elif j == 1:
                        self.pulser.rand_in_queue.put(-_rand_)
            return True
        else:
            return False

    def step(self) -> bool:
        self.pulser.play_sound()
        return True

    def tempos_up(self, up: int) -> bool:
        tempos_val = self.tempos_val
        tempos_val += up
        self.tempos_val = tempos_val
        if self.pulser.tempo_in_queue.empty():
            self.pulser.tempo_in_queue.put(self.tempos_val)
            return True
        else:
            return False

    def tempos_down(self, down: int) -> bool:
        if self.tempos_val >= down * 2:
            tempos_val = self.tempos_val
            tempos_val -= down
            self.tempos_val = tempos_val
            if self.pulser.tempo_in_queue.empty():
                self.pulser.tempo_in_queue.put(self.tempos_val)
                return True
            else:
                return False
        else:
            return False

    def waits_up(self, up: int) -> bool:
        if self.waits_val == self.wait_val:
            waits_val = self.waits_val
            waits_val += up
            self.waits_val = waits_val
            self.wait_val = waits_val
            return True
        else:
            return False

    def waits_down(self, down: int) -> bool:
        if self.waits_val == self.wait_val:
            waits_val = self.waits_val
            if waits_val >= 2:
                waits_val -= down
            self.waits_val = waits_val
            self.wait_val = waits_val
            return True
        else:
            return False

    def rands_up(self, up: int) -> bool:
        if self.rands_val == self.rand_val:
            rands_val = self.rands_val
            rands_val += up
            if rands_val > self.waits_val:
                rands_val = 1
            self.rands_val = rands_val
            self.rand_val = rands_val
            return True
        else:
            return False

    def rands_down(self, down: int) -> bool:
        if self.rands_val == self.rand_val:
            rands_val = self.rands_val
            if rands_val >= 2:
                rands_val -= down
            self.rands_val = rands_val
            self.rand_val = rands_val
            return True
        else:
            return False

    def copy_randoms(self, randoms: List[float]) -> bool:
        if not self.pause_button.disabled:
            for i, random_float in enumerate(randoms):
                self.randoms[i] = random_float
            return True
        else:
            return False

    def shuffle_program(self, shuffle_prog: int) -> bool:
        if not self.pause_button.disabled:
            self.shuffle_val = shuffle_prog
            return True
        else:
            return False


class PulserUI(Static):

    def __init__(
        self,
        pulser: Pulser,
        tempos_init: int,
        tempo_init: int,
        steps_init: int,
        waits_init: int,
        rands_init: int,
    ):
        super().__init__()
        self.pulser = pulser
        self.dev_name = pulser.device_name
        self.tempos_init = tempos_init
        self.tempo_init = tempo_init
        self.steps_init = steps_init
        self.waits_init = waits_init
        self.rands_init = rands_init
        self.pause_button = Button("Pause", id="pause")
        self.stop_button = Button("Stop", id="stop", variant="error")
        self.pulser_display = PulserDisplay(
            dev_name=self.dev_name,
            tempos_init=self.tempos_init,
            steps_init=self.steps_init,
            tempo_init=self.tempo_init,
            waits_init=self.waits_init,
            rands_init=self.rands_init,
            pulser=self.pulser,
            pause_button=self.pause_button,
            stop_button=self.stop_button,
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        pulser_display = self.pulser_display
        if button_id == "start":
            pulser_display.start()
            self.add_class("started")
        elif button_id == "stop":
            pulser_display.stop()
            self.remove_class("started")
        elif button_id == "step":
            pulser_display.step()
        elif button_id == "pause":
            pulser_display.pause()

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Start", id="start", variant="success")
        yield Button("Step", id="step")
        yield self.stop_button
        yield self.pause_button
        yield self.pulser_display


class UI(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = "ui.tcss"
    BINDINGS = [
        ("a", "toggle_ss_1", "S1"),
        ("b", "toggle_ss_2", "S2"),
        ("c", "toggle_ss_3", "S3"),
        ("d", "toggle_ss_4", "S4"),
        ("e", "rand_1", "R1"),
        ("f", "rand_2", "R2"),
        ("g", "rand_3", "R3"),
        ("h", "rand_4", "R4"),
        ("i", "toggle_ps_1", "P1"),
        ("j", "toggle_ps_2", "P2"),
        ("k", "toggle_ps_3", "P3"),
        ("l", "toggle_ps_4", "P4"),
        ("9", "tempo_up", "T+"),
        ("7", "tempo_down", "T-"),
        ("6", "wait_up", "W+"),
        ("4", "wait_down", "W-"),
        ("8", "shuffle", "S"),
        ("5", "random_up", "R"),
    ]

    def __init__(
        self,
        pulser_devs: List[Pulser],
        external_config: ExternalConfig,
    ):
        super().__init__()
        self.pulser_devs = pulser_devs
        self.external_config = external_config
        self.internal_config = InternalConfig()
        self.randoms = [0.0] * (external_config.steps_init // 2)
        self.shuffle_prod = self.internal_config.shuffle_program
        self.pulser_uis: List[PulserUI] = list()
        self.randomize()

    def randomize(self):
        shuffle_prog = self.shuffle_prod
        for i in range(len(self.randoms)):
            val = random.uniform(
                -self.external_config.rands_mag, self.external_config.rands_mag
            )
            val = (
                round(val * self.internal_config.rand_quants)
                / self.internal_config.rand_quants
            )
            self.randoms[i] = val
        self.randoms[0] = 0
        self.randoms[len(self.randoms) - 1] = 0
        half = len(self.randoms) // 2
        for i in range(half, half * 2):
            if shuffle_prog[0:2] == "0-":
                self.randoms[i] = -self.randoms[(2 * half) - i - 1]
            elif shuffle_prog[0:2] == "0+":
                self.randoms[i] = self.randoms[(2 * half) - i - 1]
            elif shuffle_prog[0:2] == "++":
                self.randoms[(2 * half) - i - 1] = abs(self.randoms[(2 * half) - i - 1])
                self.randoms[i] = self.randoms[(2 * half) - i - 1]
            elif shuffle_prog[0:2] == "--":
                self.randoms[(2 * half) - i - 1] = -abs(
                    self.randoms[(2 * half) - i - 1]
                )
                self.randoms[i] = self.randoms[(2 * half) - i - 1]
            elif shuffle_prog[0:2] == "-+":
                self.randoms[(2 * half) - i - 1] = -abs(
                    self.randoms[(2 * half) - i - 1]
                )
                self.randoms[i] = -self.randoms[(2 * half) - i - 1]
            elif shuffle_prog[0:2] == "+-":
                self.randoms[(2 * half) - i - 1] = abs(self.randoms[(2 * half) - i - 1])
                self.randoms[i] = -self.randoms[(2 * half) - i - 1]

    def compose(self) -> ComposeResult:
        for pulser in self.pulser_devs:
            pulser_ui = PulserUI(
                pulser=pulser,
                tempos_init=self.external_config.tempos_init,
                tempo_init=pulser.tempo_bpm,
                steps_init=self.external_config.steps_init,
                waits_init=self.external_config.waits_init,
                rands_init=self.external_config.rands_init,
            )
            pulser_ui.add_class("started")
            pulser_ui.pulser_display.copy_randoms(self.randoms)
            self.pulser_uis.append(pulser_ui)
        yield Footer()
        yield ScrollableContainer(*self.pulser_uis)

    def action_tempo_up(self) -> None:
        for pulser_ui in self.pulser_uis:
            pulser_ui.pulser_display.tempos_up(self.internal_config.speed_diff)

    def action_tempo_down(self) -> None:
        for pulser_ui in self.pulser_uis:
            pulser_ui.pulser_display.tempos_down(self.internal_config.speed_diff)

    def action_wait_up(self) -> None:
        for pulser_ui in self.pulser_uis:
            pulser_ui.pulser_display.waits_up(1)

    def action_wait_down(self) -> None:
        for pulser_ui in self.pulser_uis:
            pulser_ui.pulser_display.waits_down(1)

    def action_random_up(self) -> None:
        for pulser_ui in self.pulser_uis:
            pulser_ui.pulser_display.rands_up(1)

    def action_random_down(self) -> None:
        for pulser_ui in self.pulser_uis:
            pulser_ui.pulser_display.rands_down(1)

    def action_shuffle(self) -> None:
        current_prog = self.internal_config.shuffle_programs.index(self.shuffle_prod)
        new_prog = current_prog + 1
        if new_prog == len(self.internal_config.shuffle_programs):
            new_prog = 0
        self.randomize()
        changed = 0
        for pulser_ui in self.pulser_uis:
            changed += int(pulser_ui.pulser_display.copy_randoms(self.randoms))
            changed += int(
                pulser_ui.pulser_display.shuffle_program(shuffle_prog=new_prog)
            )
        if changed > 0:
            self.shuffle_prod = self.internal_config.shuffle_programs[new_prog]

    def action_toggle_ss_1(self) -> None:
        if len(self.pulser_uis) > 0:
            if self.pulser_uis[0].pulser_display.stopped:
                self.pulser_uis[0].pulser_display.start()
                self.pulser_uis[0].add_class("started")
            elif not self.pulser_uis[0].stop_button.disabled:
                self.pulser_uis[0].pulser_display.stop()
                self.pulser_uis[0].remove_class("started")

    def action_toggle_ss_2(self) -> None:
        if len(self.pulser_uis) > 1:
            if self.pulser_uis[1].pulser_display.stopped:
                self.pulser_uis[1].pulser_display.start()
                self.pulser_uis[1].add_class("started")
            elif not self.pulser_uis[1].stop_button.disabled:
                self.pulser_uis[1].pulser_display.stop()
                self.pulser_uis[1].remove_class("started")

    def action_toggle_ss_3(self) -> None:
        if len(self.pulser_uis) > 2:
            if self.pulser_uis[2].pulser_display.stopped:
                self.pulser_uis[2].pulser_display.start()
                self.pulser_uis[2].add_class()
                self.pulser_uis[2].add_class("started")
            elif not self.pulser_uis[2].stop_button.disabled:
                self.pulser_uis[2].pulser_display.stop()
                self.pulser_uis[2].remove_class("started")

    def action_toggle_ss_4(self) -> None:
        if len(self.pulser_uis) > 3:
            if self.pulser_uis[3].pulser_display.stopped:
                self.pulser_uis[3].pulser_display.start()
                self.pulser_uis[3].add_class()
                self.pulser_uis[3].add_class("started")
            elif not self.pulser_uis[3].stop_button.disabled:
                self.pulser_uis[3].pulser_display.stop()
                self.pulser_uis[3].remove_class("started")

    def action_toggle_ps_1(self) -> None:
        if len(self.pulser_uis) > 0:
            if self.pulser_uis[0].pulser_display.stopped:
                self.pulser_uis[0].pulser_display.step()
            elif not self.pulser_uis[0].pause_button.disabled:
                self.pulser_uis[0].pulser_display.pause()

    def action_toggle_ps_2(self) -> None:
        if len(self.pulser_uis) > 1:
            if self.pulser_uis[1].pulser_display.stopped:
                self.pulser_uis[1].pulser_display.step()
            elif not self.pulser_uis[1].pause_button.disabled:
                self.pulser_uis[1].pulser_display.pause()

    def action_toggle_ps_3(self) -> None:
        if len(self.pulser_uis) > 2:
            if self.pulser_uis[2].pulser_display.stopped:
                self.pulser_uis[2].pulser_display.step()
            elif not self.pulser_uis[2].pause_button.disabled:
                self.pulser_uis[2].pulser_display.pause()

    def action_toggle_ps_4(self) -> None:
        if len(self.pulser_uis) > 3:
            if self.pulser_uis[3].pulser_display.stopped:
                self.pulser_uis[3].pulser_display.step()
            elif not self.pulser_uis[3].pause_button.disabled:
                self.pulser_uis[3].pulser_display.pause()

    def action_rand_1(self) -> None:
        if len(self.pulser_uis) > 0:
            if (
                not self.pulser_uis[0].pulser_display.stopped
                and not self.pulser_uis[0].pause_button.disabled
            ):
                self.pulser_uis[0].pulser_display.rand()

    def action_rand_2(self) -> None:
        if len(self.pulser_uis) > 1:
            if (
                not self.pulser_uis[1].pulser_display.stopped
                and not self.pulser_uis[1].pause_button.disabled
            ):
                self.pulser_uis[1].pulser_display.rand()

    def action_rand_3(self) -> None:
        if len(self.pulser_uis) > 2:
            if (
                not self.pulser_uis[2].pulser_display.stopped
                and not self.pulser_uis[2].pause_button.disabled
            ):
                self.pulser_uis[2].pulser_display.rand()

    def action_rand_4(self) -> None:
        if len(self.pulser_uis) > 3:
            if (
                not self.pulser_uis[3].pulser_display.stopped
                and not self.pulser_uis[3].pause_button.disabled
            ):
                self.pulser_uis[3].pulser_display.rand()
