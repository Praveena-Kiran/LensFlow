from backend.automation.controllers.powerpoint_controller import PowerPointController


class PowerPointAction:

    def __init__(self):
        self.controller = PowerPointController()

    def execute(self, step, apps):

        command = step.get("command")

        try:

            if command == "next_slide":
                self.controller.next_slide()

            elif command == "previous_slide":
                self.controller.previous_slide()

            elif command == "start_presentation":
                self.controller.start_presentation()

            elif command == "end_presentation":
                self.controller.end_presentation()

            else:
                print(f"❌ Unknown PowerPoint command: {command}")

        except Exception as e:
            print(f"❌ PowerPoint Action Error: {e}")