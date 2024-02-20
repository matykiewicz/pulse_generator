import time
from typing import Any, Callable, Dict, List

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Button, Footer, Header, Static


class TempoStepDisplay(Static):
    """A widget to display elapsed time."""

    tempo = reactive(0)
    stepped = reactive(0)
    stopped = reactive(False)
    tempo_step_updater: Timer

    def __init__(
        self,
        current_tempo_getter: Callable,
        current_step_getter: Callable,
        current_tempo_setter: Callable,
        current_step_setter: Callable,
        dev_name: str,
    ):
        super().__init__()
        self.current_tempo_getter = current_tempo_getter
        self.current_step_getter = current_step_getter
        self.current_tempo_setter = current_tempo_setter
        self.current_step_setter = current_step_setter
        self.dev_name = dev_name

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.tempo = self.current_tempo_getter()
        self.stepped = self.current_step_getter()
        self.tempo_step_updater = self.set_interval(
            1 / 60, self.update_tempo_step, pause=False
        )

    def update_tempo_step(self) -> None:
        """Method to update time to current."""
        self.tempo = self.current_tempo_getter()
        self.stepped = self.current_step_getter()

    def watch_stepped(self) -> None:
        self.update(f"N: {self.dev_name}; T: {self.tempo}; S: {self.stepped}")

    def watch_tempo(self) -> None:
        self.update(f"N: {self.dev_name}; T: {self.tempo}; S: {self.stepped}")

    def start(self) -> None:
        pass
        #self.tempo_step_updater.resume()

    def stop(self) -> None:
        pass
        #self.tempo_step_updater.stop()

    def step(self) -> None:
        stepped = self.stepped
        stepped += 1
        self.stepped = stepped
        self.current_step_setter(self.stepped)


class Tempo(Static):

    def __init__(
        self,
        current_tempo_getter: Callable,
        current_step_getter: Callable,
        current_tempo_setter: Callable,
        current_step_setter: Callable,
        dev_name: str,
    ):
        super().__init__()
        self.dev_name = dev_name
        self.current_tempo_getter = current_tempo_getter
        self.current_step_getter = current_step_getter
        self.current_tempo_setter = current_tempo_setter
        self.current_step_setter = current_step_setter

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        tempo_step_display = self.query_one(TempoStepDisplay)
        if button_id == "start":
            tempo_step_display.start()
            self.add_class("started")
        elif button_id == "stop":
            tempo_step_display.stop()
            self.remove_class("started")
        elif button_id == "step":
            tempo_step_display.step()

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Step", id="step")
        yield TempoStepDisplay(
            dev_name=self.dev_name,
            current_tempo_getter=self.current_tempo_getter,
            current_step_getter=self.current_step_getter,
            current_tempo_setter=self.current_tempo_setter,
            current_step_setter=self.current_step_setter,
        )


class PulserApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = "ui.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def __init__(
        self,
        audio_devs: List[Dict[str, Any]],
        current_tempo_getters: List[Callable],
        current_step_getters: List[Callable],
        current_tempo_setters: List[Callable],
        current_step_setters: List[Callable],
    ):
        super().__init__()
        self.audio_devs = audio_devs
        self.current_tempo_getters = current_tempo_getters
        self.current_step_getters = current_step_getters
        self.current_tempo_setters = current_tempo_setters
        self.current_step_setters = current_step_setters

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        tempos = list()
        for i, dev in enumerate(self.audio_devs):
            tempos.append(
                Tempo(
                    dev_name=self.audio_devs[i]["name"],
                    current_tempo_getter=self.current_tempo_getters[i],
                    current_step_getter=self.current_step_getters[i],
                    current_tempo_setter=self.current_tempo_setters[i],
                    current_step_setter=self.current_step_setters[i],
                )
            )
        for tempo in tempos:
            tempo.add_class("started")
        yield Header()
        yield Footer()
        yield ScrollableContainer(*tempos)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    app = PulserApp(
        [{"name": "test"}],
        current_tempo_getters=[lambda: 99],
        current_step_getters=[lambda: 99],
        current_tempo_setters=[lambda x: None],
        current_step_setters=[lambda x: None],
    )
    app.run()
