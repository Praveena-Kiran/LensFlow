import json
import os
import subprocess
import platform

from .actions.launch_action import LaunchAction
from .actions.wait_action import WaitAction
from .actions.website_action import WebsiteAction
from .actions.hotkey_action import HotkeyAction
from .actions.powerpoint_action import PowerPointAction


class FlowManager:

    def __init__(self):
        self.current_studio = None

        config_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "config"
        )

        self.actions = {
            "launch": LaunchAction(),
            "wait": WaitAction(),
            "website": WebsiteAction(),
            "hotkey": HotkeyAction(),
            "powerpoint": PowerPointAction(),
        }

        with open(
            os.path.join(config_dir, "apps.json"),
            "r",
            encoding="utf-8"
        ) as f:
            self.apps = json.load(f)

        with open(
            os.path.join(config_dir, "flows.json"),
            "r",
            encoding="utf-8"
        ) as f:
            self.flows = json.load(f)

    # =========================================================
    # OLD FLOW SYSTEM
    # =========================================================

    def execute_flow(self, flow_name):

        flow = self.flows.get(flow_name)

        if not flow:
            print(f"❌ Flow '{flow_name}' not found.")
            return

        print(f"🚀 Executing Flow: {flow['name']}")

        for step in flow["actions"]:

            action_type = step.get("type")
            action = self.actions.get(action_type)

            if action:
                action.execute(step, self.apps)

            else:
                print(
                    f"❌ Unknown action type: {action_type}"
                )

    # =========================================================
    # CUSTOM STUDIO EVENTS
    # =========================================================

    def execute_custom_event(self, event):

        if not event:
            print("⚠ No event supplied.")
            return

        action = event.get("action", "")
        value = event.get("value", "")

        print(
            f"🚀 Custom Event: "
            f"{event.get('name', 'Unnamed Event')}"
        )

        print(f"   Action: {action}")
        print(f"   Value: {value}")

        # -----------------------------------------------------
        # OPEN FILE
        # -----------------------------------------------------

        if action == "Open File":

            if not value:
                print("❌ No file selected.")
                return

            self.open_file(value)
            return

        # -----------------------------------------------------
        # OPEN WEBSITE
        # -----------------------------------------------------

        if action == "Open Website":

            if not value:
                print("❌ No website specified.")
                return

            self.open_website(value)
            return

        # -----------------------------------------------------
        # LAUNCH APPLICATION
        # -----------------------------------------------------

        if action in ("Launch Application", "Open Application"):

            if not value:
                print("❌ No application specified.")
                return

            self.launch_app(value)
            return

        # -----------------------------------------------------
        # WAIT
        # -----------------------------------------------------

        if action == "Wait":

            try:
                seconds = float(value)
                print(f"⏳ Waiting {seconds} seconds...")
                import time
                time.sleep(seconds)

            except ValueError:
                print(
                    f"❌ Invalid wait value: {value}"
                )

            return

        print(
            f"⚠ Unknown custom action: {action}"
        )

    # =========================================================
    # FILE HANDLING
    # =========================================================

    def open_file(self, file_path):

        if not file_path:
            print("❌ File path is empty.")
            return

        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):

            print(
                f"❌ File does not exist:\n"
                f"{file_path}"
            )

            return

        try:

            system = platform.system()

            if system == "Windows":

                os.startfile(file_path)

            elif system == "Darwin":

                subprocess.Popen(
                    ["open", file_path]
                )

            elif system == "Linux":

                subprocess.Popen(
                    ["xdg-open", file_path]
                )

            else:

                print(
                    f"❌ Unsupported operating system: "
                    f"{system}"
                )

                return

            print(
                f"✅ Opened file:\n"
                f"{file_path}"
            )

        except Exception as e:

            print(
                f"❌ Could not open file:\n"
                f"{file_path}"
            )

            print(f"   Error: {e}")

    # =========================================================
    # WEBSITE HANDLING
    # =========================================================

    def open_website(self, url):

        if not url:
            print("❌ Website URL is empty.")
            return

        try:

            import webbrowser

            webbrowser.open(url)

            print(
                f"✅ Opened website: {url}"
            )

        except Exception as e:

            print(
                f"❌ Could not open website: "
                f"{e}"
            )

    # =========================================================
    # APP LAUNCHING
    # =========================================================

    def launch_app(self, app):

        system = platform.system()

        try:

            if system == "Windows":

                subprocess.Popen(
                    app,
                    shell=True
                )

            elif system == "Darwin":

                subprocess.Popen(
                    ["open", "-a", app]
                )

            elif system == "Linux":

                subprocess.Popen(
                    [app]
                )

            print(
                f"✅ Launched {app}"
            )

        except Exception as e:

            print(
                f"❌ Could not launch {app}: {e}"
            )

    # =========================================================
    # DASHBOARD HELPERS
    # =========================================================

    def get_apps_for_flow(self, flow_name):

        flow = self.flows.get(flow_name)

        if not flow:
            return []

        items = []

        for step in flow["actions"]:

            if step["type"] == "launch":

                app = step.get("target")

                if app:
                    items.append(
                        app.title()
                    )

            elif step["type"] == "website":

                url = step.get(
                    "url",
                    ""
                ).lower()

                if "github" in url:
                    items.append("🌐 GitHub")

                elif "chatgpt" in url:
                    items.append("🌐 ChatGPT")

                elif "stackoverflow" in url:
                    items.append(
                        "🌐 Stack Overflow"
                    )

                else:
                    items.append(
                        "🌐 Website"
                    )

        return items

    # =========================================================
    # STUDIO MANAGEMENT
    # =========================================================

    def set_current_studio(self, studio):

        self.current_studio = studio

    def run_current_studio(self):

        if not self.current_studio:

            print(
                "⚠ No studio selected."
            )

            return

        # Custom Studio
        if self.current_studio.get(
            "type"
        ) == "custom":

            events = self.current_studio.get(
                "events",
                []
            )

            print(
                f"🚀 Running Custom Studio: "
                f"{self.current_studio.get('name')}"
            )

            for event in events:

                self.execute_custom_event(
                    event
                )

            return

        # Old flow-based studio
        flow_name = self.current_studio.get(
            "flow"
        )

        if flow_name:

            self.execute_flow(
                flow_name
            )


if __name__ == "__main__":

    fm = FlowManager()

    fm.execute_flow(
        "presentation_flow"
    )