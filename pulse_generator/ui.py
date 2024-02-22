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

    def __init__(
        self,
        dev_name: str,
        next_schedule: float,
        tempos_init: int,
        tempo_init: int,
        steps_init: int,
        waits_init: int,
        pulser: Pulser,
        pause_button: Button,
    ):
        super().__init__()
        self.pause_button = pause_button
        self.dev_name = dev_name
        self.next_schedule = next_schedule
        self.tempos_val = tempos_init
        self.tempo_val = tempo_init
        self.steps_val = steps_init
        self.step_val = 1
        self.waits_val = waits_init
        self.wait_val = waits_init
        self.commands: List[str] = list()
        self.pulser = pulser
        self.stopped = False
        self.interval_sec = 0
        self.total_time_for_steps = 0
        self.reset_interval_and_tempo()
        self.set_timer(delay=self.next_schedule - time.time() - 0.002, callback=self.run_schedule)
        self.f = open("yyy.txt", "w")

    def reset_interval_and_tempo(self):
        self.interval_sec = round(1 / (self.tempo_val / 60), 3)
        self.total_time_for_steps = self.steps_val * self.interval_sec

    def run_schedule(self) -> None:
        self.f.write(f"{self.next_schedule} {self.step_val} {self.wait_val} {self.next_schedule - time.time()}\n")
        self.f.flush()
        self.next_schedule += self.interval_sec

        if self.step_val == self.steps_val:
            self.execute_wait()
            self.execute_command()

        step_val = self.step_val
        step_val = step_val % self.steps_val
        step_val += 1
        self.step_val = step_val
        self.set_timer(delay=self.next_schedule - time.time() - 0.002, callback=self.run_schedule)

    def execute_wait(self):
        if self.wait_val < self.waits_val:
            wait_val = self.wait_val
            wait_val += 1
            self.wait_val = wait_val
            if wait_val == self.waits_val:
                self.pause_button.disabled = False

    def execute_command(self):
        if len(self.commands) > 0:
            command = self.commands.pop()
            if command == "pause":
                self.wait_val = 0
                if self.pulser.pause_queue.empty():
                    for i in range(self.waits_val):
                        self.pulser.pause_queue.put("pause")
            elif command == "stop":
                pass
            elif command == "start":
                pass

    def update_all(self):
        self.update(
            f"D: {self.dev_name}; T: {self.tempo_val}/{self.tempos_val}; "
            f"S: {self.step_val}/{self.steps_val}; "
            f"W: {self.wait_val}/{self.waits_val}"
        )

    def watch_step_val(self) -> None:
        self.update_all()

    def watch_tempo_val(self) -> None:
        self.update_all()

    def watch_wait_val(self) -> None:
        self.update_all()

    def watch_steps_val(self) -> None:
        self.update_all()

    def watch_tempos_val(self) -> None:
        self.update_all()

    def watch_waits_val(self) -> None:
        self.update_all()

    def start(self) -> bool:

        if len(self.commands) == 0:
            self.commands.append("start")
            return True
        else:
            return False

    def stop(self) -> bool:
        if len(self.commands) == 0:
            self.commands.append("stop")
            return True
        else:
            return False

    def pause(self) -> bool:
        if len(self.commands) == 0:
            self.commands.append("pause")
            return True
        else:
            return False

    def step(self) -> bool:
        if len(self.commands) == 0:
            self.commands.append("step")
            return True
        else:
            return False

    def tempo_up(self, up: int) -> bool:
        tempos_val = self.tempos_val
        tempos_val += up
        self.tempos_val = tempos_val
        return True

    def tempo_down(self, down: int) -> bool:
        tempos_val = self.tempos_val
        tempos_val -= down
        self.tempos_val = tempos_val
        return True


class PulserUI(Static):

    def __init__(
        self,
        pulser: Pulser,
        next_schedule: float,
        tempos_init: int,
        tempo_init: int,
        steps_init: int,
        waits_init: int,
    ):
        super().__init__()
        self.pulser = pulser
        self.dev_name = pulser.device_name
        self.next_schedule = next_schedule
        self.tempos_init = tempos_init
        self.tempo_init = tempo_init
        self.steps_init = steps_init
        self.waits_init = waits_init
        self.pause_button = Button("Pause", id="pause")
        self.pulser_display = PulserDisplay(
            dev_name=self.dev_name,
            next_schedule=self.next_schedule,
            tempos_init=self.tempos_init,
            steps_init=self.steps_init,
            tempo_init=self.tempo_init,
            waits_init=self.waits_init,
            pulser=self.pulser,
            pause_button=self.pause_button,
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        pulser_display = self.query_one(PulserDisplay)
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
            self.pause_button.disabled = True

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Step", id="step")
        yield self.pause_button
        yield self.pulser_display


class UI(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = "ui.tcss"
    BINDINGS = [
        ("a", "toggle_ss_1", "S/S D1"),
        ("b", "toggle_ss_2", "S/S D2"),
        ("c", "toggle_ss_3", "S/S D3"),
        ("2", "toggle_ss_4", "S/S D4"),
        ("g", "toggle_ps_1", "P/S D1"),
        ("h", "toggle_ps_2", "P/S D2"),
        ("i", "toggle_ps_3", "P/S D3"),
        ("5", "toggle_ps_4", "P/S D4"),
        ("9", "tempo_up", "T UP"),
        ("7", "tempo_down", "T DO"),
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
        self.pulser_uis = list()

    def compose(self) -> ComposeResult:
        for pulser in self.pulser_devs:
            pulser_ui = PulserUI(
                pulser=pulser,
                next_schedule=pulser.next_schedule,
                tempos_init=self.external_config.tempos_init,
                tempo_init=pulser.tempo_bpm,
                steps_init=self.external_config.steps_init,
                waits_init=self.external_config.waits_init,
            )
            pulser_ui.add_class("started")
            self.pulser_uis.append(pulser_ui)
        yield Footer()
        yield ScrollableContainer(*self.pulser_uis)

    def action_tempo_up(self) -> None:
        for pulser_ui in self.pulser_uis:
            pulser_ui.pulser_display.tempo_up(self.internal_config.speed_diff)

    def action_tempo_down(self) -> None:
        for pulser_ui in self.pulser_uis:
            pulser_ui.pulser_display.tempo_down(self.internal_config.speed_diff)

    def action_toggle_ss_1(self) -> None:
        if len(self.pulser_uis) > 0:
            if self.pulser_uis[0].pulser_display.stopped:
                self.pulser_uis[0].pulser_display.start()
                self.pulser_uis[0].add_class("started")
            else:
                self.pulser_uis[0].pulser_display.stop()
                self.pulser_uis[0].remove_class("started")

    def action_toggle_ss_2(self) -> None:
        if len(self.pulser_uis) > 1:
            if self.pulser_uis[1].pulser_display.stopped:
                self.pulser_uis[1].pulser_display.start()
                self.pulser_uis[1].add_class("started")
            else:
                self.pulser_uis[1].pulser_display.stop()
                self.pulser_uis[1].remove_class("started")

    def action_toggle_ss_3(self) -> None:
        if len(self.pulser_uis) > 2:
            if self.pulser_uis[2].pulser_display.stopped:
                self.pulser_uis[2].pulser_display.start()
                self.pulser_uis[2].add_class()
                self.pulser_uis[2].add_class("started")
            else:
                self.pulser_uis[2].pulser_display.stop()
                self.pulser_uis[2].remove_class("started")

    def action_toggle_ss_4(self) -> None:
        if len(self.pulser_uis) > 3:
            if self.pulser_uis[3].pulser_display.stopped:
                self.pulser_uis[3].pulser_display.start()
                self.pulser_uis[3].add_class()
                self.pulser_uis[3].add_class("started")
            else:
                self.pulser_uis[3].pulser_display.stop()
                self.pulser_uis[3].remove_class("started")

    def action_toggle_ps_1(self) -> None:
        if len(self.pulser_uis) > 0:
            if self.pulser_uis[0].pulser_display.stopped:
                self.pulser_uis[0].pulser_display.step()
            else:
                self.pulser_uis[0].pulser_display.pause()
                self.pulser_uis[0].pause_button.disabled = True

    def action_toggle_ps_2(self) -> None:
        if len(self.pulser_uis) > 1:
            if self.pulser_uis[1].pulser_display.stopped:
                self.pulser_uis[1].pulser_display.step()
            else:
                self.pulser_uis[1].pulser_display.pause()
                self.pulser_uis[1].pause_button.disabled = True

    def action_toggle_ps_3(self) -> None:
        if len(self.pulser_uis) > 2:
            if self.pulser_uis[2].pulser_display.stopped:
                self.pulser_uis[2].pulser_display.step()
            else:
                self.pulser_uis[2].pulser_display.pause()
                self.pulser_uis[2].pause_button.disabled = True

    def action_toggle_ps_4(self) -> None:
        if len(self.pulser_uis) > 3:
            if self.pulser_uis[3].pulser_display.stopped:
                self.pulser_uis[3].pulser_display.step()
            else:
                self.pulser_uis[3].pulser_display.pause()
                self.pulser_uis[2].pause_button.disabled = True
