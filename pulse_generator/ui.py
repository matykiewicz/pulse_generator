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
    stopped = reactive(False)

    def __init__(
        self,
        dev_name: str,
        tempos_init: int,
        tempo_init: int,
        steps_init: int,
        waits_init: int,
        pulser: Pulser,
        pause_button: Button,
        stop_button: Button,
    ):
        super().__init__()
        self.internal_config = InternalConfig()
        self.pause_button = pause_button
        self.stop_button = stop_button
        self.dev_name = dev_name
        self.tempos_val = tempos_init
        self.tempo_val = tempo_init
        self.steps_val = steps_init
        self.step_val = steps_init
        self.waits_val = waits_init
        self.wait_val = waits_init
        self.commands: List[str] = list()
        self.pulser = pulser
        self.interval_sec: float = 0.0
        self.reset_interval_and_tempo()
        self.next_schedule = self.pulser.next_schedule
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
            self.run_pause_start_stop_command()
        step_val = self.step_val
        step_val = step_val % self.steps_val
        step_val += 1
        self.step_val = step_val
        if self.step_val == 1:
            self.run_tempo_out_command()
        self.next_schedule += self.interval_sec
        self.set_timer(
            delay=self.next_schedule - time.time() - self.internal_config.time_drift,
            callback=self.run_schedule,
        )

    def run_wait_command(self):
        if self.pulser.pause_in_queue.empty() and self.wait_val < self.waits_val:
            wait_val = self.wait_val
            wait_val += 1
            if wait_val == self.waits_val:
                self.pause_button.disabled = False
                self.stop_button.disabled = False
                if not self.pulser.pause_in_queue.empty():
                    self.pulser.pause_in_queue.get()
            self.wait_val = wait_val

    def run_pause_start_stop_command(self):
        if len(self.commands) > 0:
            command = self.commands.pop()
            if command == "pause":
                self.wait_val = 0
            elif command == "stop":
                self.stopped = True
            elif command == "start":
                self.stopped = False
        if self.stopped and self.pulser.pause_in_queue.empty():
            self.pulser.pause_in_queue.put("pause")

    def run_tempo_out_command(self):
        if not self.pulser.tempo_out_queue.empty():
            self.tempo_val = self.pulser.tempo_out_queue.get()
            self.reset_interval_and_tempo()

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

    def step(self) -> bool:
        self.pulser.play_sound()
        return True

    def tempo_up(self, up: int) -> bool:
        tempos_val = self.tempos_val
        tempos_val += up
        self.tempos_val = tempos_val
        if self.pulser.tempo_in_queue.empty():
            self.pulser.tempo_in_queue.put(self.tempos_val)
            return True
        else:
            return False

    def tempo_down(self, down: int) -> bool:
        tempos_val = self.tempos_val
        tempos_val -= down
        self.tempos_val = tempos_val
        if self.pulser.tempo_in_queue.empty():
            self.pulser.tempo_in_queue.put(self.tempos_val)
            return True
        else:
            return False

    def wait_up(self, up: int) -> bool:
        if self.waits_val == self.wait_val:
            waits_val = self.waits_val
            waits_val += up
            self.waits_val = waits_val
            self.wait_val = waits_val
            return True
        else:
            return False

    def wait_down(self, down: int) -> bool:
        if self.waits_val == self.wait_val:
            waits_val = self.waits_val
            if waits_val >= 2:
                waits_val -= down
            self.waits_val = waits_val
            self.wait_val = waits_val
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
    ):
        super().__init__()
        self.pulser = pulser
        self.dev_name = pulser.device_name
        self.tempos_init = tempos_init
        self.tempo_init = tempo_init
        self.steps_init = steps_init
        self.waits_init = waits_init
        self.pause_button = Button("Pause", id="pause")
        self.stop_button = Button("Stop", id="stop", variant="error")
        self.pulser_display = PulserDisplay(
            dev_name=self.dev_name,
            tempos_init=self.tempos_init,
            steps_init=self.steps_init,
            tempo_init=self.tempo_init,
            waits_init=self.waits_init,
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
        ("a", "toggle_ss_1", "SS1"),
        ("b", "toggle_ss_2", "SS2"),
        ("c", "toggle_ss_3", "SS3"),
        ("d", "toggle_ss_4", "SS4"),
        ("i", "toggle_ps_1", "PS1"),
        ("j", "toggle_ps_2", "PS2"),
        ("k", "toggle_ps_3", "PS3"),
        ("l", "toggle_ps_4", "PS4"),
        ("9", "tempo_up", "T+"),
        ("7", "tempo_down", "T-"),
        ("6", "wait_up", "W+"),
        ("4", "wait_down", "W-"),
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
        self.pulser_uis: List[PulserUI] = list()

    def compose(self) -> ComposeResult:
        for pulser in self.pulser_devs:
            pulser_ui = PulserUI(
                pulser=pulser,
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

    def action_wait_up(self) -> None:
        for pulser_ui in self.pulser_uis:
            pulser_ui.pulser_display.wait_up(1)

    def action_wait_down(self) -> None:
        for pulser_ui in self.pulser_uis:
            pulser_ui.pulser_display.wait_down(1)

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

    def action_toggle_ps_2(self) -> None:
        if len(self.pulser_uis) > 1:
            if self.pulser_uis[1].pulser_display.stopped:
                self.pulser_uis[1].pulser_display.step()
            else:
                self.pulser_uis[1].pulser_display.pause()

    def action_toggle_ps_3(self) -> None:
        if len(self.pulser_uis) > 2:
            if self.pulser_uis[2].pulser_display.stopped:
                self.pulser_uis[2].pulser_display.step()
            else:
                self.pulser_uis[2].pulser_display.pause()

    def action_toggle_ps_4(self) -> None:
        if len(self.pulser_uis) > 3:
            if self.pulser_uis[3].pulser_display.stopped:
                self.pulser_uis[3].pulser_display.step()
            else:
                self.pulser_uis[3].pulser_display.pause()
