from backend.automation.controllers.powerpoint_controller import PowerPointController


COMMANDS = (
    "next_slide",
    "previous_slide",
    "start_presentation",
    "end_presentation",
)


class PowerPointAction:

    def __init__(self):
        self.controller = PowerPointController()

    def execute(self, step, apps=None):
        """Run a PowerPoint command; raises with a readable message on failure."""

        command = step.get("command")

        if command not in COMMANDS:
            raise ValueError(f"Unknown PowerPoint command: {command}")

        if not self.controller.connect():
            raise RuntimeError(
                "Couldn't reach PowerPoint. Open your presentation in "
                "PowerPoint first."
            )

        getattr(self.controller, command)()
