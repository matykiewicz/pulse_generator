import sched
import time
from typing import Callable, List, Optional

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Button, Footer, Static

from .configs import ExternalConfig, InternalConfig
from .pulser import Pulser

MASTER_NAME = "MASTER"


class PulserDisplay(Static):
    tempos_val = reactive(0)
    tempo_val = reactive(0)
    steps_val = reactive(0)
    step_val = reactive(0)
    waits_val = reactive(0)
    wait_val = reactive(0)
    tempo_step_wait_updater: Timer

    def __init__(
        self,
        dev_name: str,
        get_time_sync: Callable,
        tempos_init: int,
        steps_init: int,
        waits_init: int,
        many_schedules: List[Callable],
        pulser: Optional[Pulser],
    ):
        super().__init__()
        self.dev_name = dev_name
        self.get_time_sync = get_time_sync
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.tempos_val = tempos_init
        self.tempo_val = tempos_init
        self.steps_val = steps_init
        self.step_val = 1
        self.waits_val = waits_init
        self.wait_val = waits_init
        self.many_schedules = many_schedules
        self.commands: List[str] = list()
        self.pulser = pulser
        self.stopped = False

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.scheduler.enterabs(
            self.get_time_sync(), priority=1, action=self.set_interval_on_time
        )
        self.scheduler.run(blocking=True)

    def set_interval_on_time(self):
        if self.dev_name == MASTER_NAME:
            interval = 1 / (self.tempo_val / 60)
            self.tempo_step_wait_updater = self.set_interval(
                interval, self.run_many_schedules, pause=False
            )

    def run_many_schedules(self):
        self.run_single_schedule()
        for schedule in self.many_schedules:
            schedule()

    def run_single_schedule(self) -> None:
        if self.pulser is not None:
            self.pulser.make_sound()
        step_val = self.step_val
        step_val = step_val % self.steps_val
        step_val += 1
        if self.wait_val < self.waits_val and step_val == 16:
            wait_val = self.wait_val
            wait_val += 1
            self.wait_val = wait_val
            if self.wait_val == self.waits_val:
                self.pulser.stop_skipping()
        if self.pulser and step_val == 16 and len(self.commands) > 0:
            command = self.commands.pop()
            if command == "stop":
                self.pulser.start_skipping()
                self.stopped = True
            elif command == "start":
                self.pulser.stop_skipping()
                self.stopped = False
            elif command == "pause":
                self.wait_val = 0
                self.pulser.start_skipping()
            else:
                self.commands.append(command)
        if (
            self.pulser
            and self.pulser.skip
            and len(self.commands) > 0
            and self.commands[0] == "step"
        ):
            command = self.commands.pop()
            self.pulser.play()
        self.step_val = step_val

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


class PulserUI(Static):

    def __init__(
        self,
        pulser: Pulser,
        get_time_sync: Callable,
        tempos_init: int,
        steps_init: int,
        waits_init: int,
    ):
        super().__init__()
        self.pulser = pulser
        self.dev_name = pulser.device_name
        self.get_time_sync = get_time_sync
        self.tempos_init = tempos_init
        self.steps_init = steps_init
        self.waits_init = waits_init
        self.pulser_display = PulserDisplay(
            dev_name=self.dev_name,
            get_time_sync=self.get_time_sync,
            tempos_init=self.tempos_init,
            steps_init=self.steps_init,
            waits_init=self.waits_init,
            many_schedules=[],
            pulser=self.pulser,
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

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Step", id="step")
        yield Button("Pause", id="pause")
        yield self.pulser_display


class MasterUI(Static):

    def __init__(
        self,
        pulser_devs: List[Pulser],
        external_config: ExternalConfig,
        internal_config: InternalConfig,
    ):
        super().__init__()
        self.pulser_devs = pulser_devs
        self.external_config = external_config
        self.time_sync = round(time.time() + internal_config.first_start_delay)
        pulser_uis: List[PulserUI] = list()
        many_schedules: List[Callable] = list()
        for pulser in self.pulser_devs:
            pulser_ui = PulserUI(
                pulser=pulser,
                get_time_sync=self.get_time_sync,
                tempos_init=self.external_config.tempos_init,
                steps_init=self.external_config.steps_init,
                waits_init=self.external_config.waits_init,
            )
            many_schedules.append(pulser_ui.pulser_display.run_single_schedule)
            pulser_ui.add_class("started")
            pulser_uis.append(pulser_ui)
        self.pulser_uis = pulser_uis
        self.many_schedules = many_schedules

    def get_time_sync(self):
        return self.time_sync

    def get_all_uis(self) -> List[Static]:
        return [self] + self.pulser_uis

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        pulser_display = self.query_one(PulserDisplay)
        if button_id == "start":
            if pulser_display.start():
                self.add_class("started")
        elif button_id == "stop":
            if pulser_display.stop():
                self.remove_class("started")
        elif button_id == "step":
            pulser_display.step()
        elif button_id == "pause":
            pulser_display.pause()

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Step", id="step")
        yield Button("Pause", id="pause")
        yield PulserDisplay(
            dev_name=MASTER_NAME,
            get_time_sync=self.get_time_sync,
            tempos_init=self.external_config.tempos_init,
            steps_init=self.external_config.steps_init,
            waits_init=self.external_config.waits_init,
            many_schedules=self.many_schedules,
            pulser=None,
        )


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
        self.master_ui: Optional[MasterUI] = None

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        self.master_ui = MasterUI(
            pulser_devs=self.pulser_devs,
            external_config=self.external_config,
            internal_config=self.internal_config,
        )
        self.master_ui.add_class("started")
        all_uis = self.master_ui.get_all_uis()
        yield Footer()
        yield ScrollableContainer(*all_uis)

    def action_toggle_ss_1(self) -> None:
        if self.master_ui is not None:
            if len(self.master_ui.pulser_uis) > 0:
                if self.master_ui.pulser_uis[0].pulser_display.stopped:
                    self.master_ui.pulser_uis[0].pulser_display.start()
                    self.master_ui.pulser_uis[0].add_class("started")
                else:
                    self.master_ui.pulser_uis[0].pulser_display.stop()
                    self.master_ui.pulser_uis[0].remove_class("started")

    def action_toggle_ss_2(self) -> None:
        if self.master_ui is not None:
            if len(self.master_ui.pulser_uis) > 1:
                if self.master_ui.pulser_uis[1].pulser_display.stopped:
                    self.master_ui.pulser_uis[1].pulser_display.start()
                    self.master_ui.pulser_uis[1].add_class("started")
                else:
                    self.master_ui.pulser_uis[1].pulser_display.stop()
                    self.master_ui.pulser_uis[1].remove_class("started")

    def action_toggle_ss_3(self) -> None:
        if self.master_ui is not None:
            if len(self.master_ui.pulser_uis) > 2:
                if self.master_ui.pulser_uis[2].pulser_display.stopped:
                    self.master_ui.pulser_uis[2].pulser_display.start()
                    self.master_ui.pulser_uis[2].add_class()
                    self.master_ui.pulser_uis[2].add_class("started")
                else:
                    self.master_ui.pulser_uis[2].pulser_display.stop()
                    self.master_ui.pulser_uis[2].remove_class("started")

    def action_toggle_ss_4(self) -> None:
        if self.master_ui is not None:
            if len(self.master_ui.pulser_uis) > 3:
                if self.master_ui.pulser_uis[3].pulser_display.stopped:
                    self.master_ui.pulser_uis[3].pulser_display.start()
                    self.master_ui.pulser_uis[3].add_class()
                    self.master_ui.pulser_uis[3].add_class("started")
                else:
                    self.master_ui.pulser_uis[3].pulser_display.stop()
                    self.master_ui.pulser_uis[3].remove_class("started")

    def action_toggle_ps_1(self) -> None:
        if self.master_ui is not None:
            if len(self.master_ui.pulser_uis) > 0:
                if self.master_ui.pulser_uis[0].pulser_display.stopped:
                    self.master_ui.pulser_uis[0].pulser_display.step()
                else:
                    self.master_ui.pulser_uis[0].pulser_display.pause()

    def action_toggle_ps_2(self) -> None:
        if self.master_ui is not None:
            if len(self.master_ui.pulser_uis) > 1:
                if self.master_ui.pulser_uis[1].pulser_display.stopped:
                    self.master_ui.pulser_uis[1].pulser_display.step()
                else:
                    self.master_ui.pulser_uis[1].pulser_display.pause()

    def action_toggle_ps_3(self) -> None:
        if self.master_ui is not None:
            if len(self.master_ui.pulser_uis) > 2:
                if self.master_ui.pulser_uis[2].pulser_display.stopped:
                    self.master_ui.pulser_uis[2].pulser_display.step()
                else:
                    self.master_ui.pulser_uis[2].pulser_display.pause()

    def action_toggle_ps_4(self) -> None:
        if self.master_ui is not None:
            if len(self.master_ui.pulser_uis) > 3:
                if self.master_ui.pulser_uis[3].pulser_display.stopped:
                    self.master_ui.pulser_uis[3].pulser_display.step()
                else:
                    self.master_ui.pulser_uis[3].pulser_display.pause()
