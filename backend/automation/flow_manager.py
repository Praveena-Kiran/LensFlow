import json
import os
import subprocess
import platform
import time

from backend.paths import DEFAULT_CONFIG_DIR, user_config_path
from backend.automation.app_launcher import launch_app
from backend.automation.events import parse_hotkey, powerpoint_command

from .actions.launch_action import LaunchAction
from .actions.wait_action import WaitAction
from .actions.website_action import WebsiteAction
from .actions.hotkey_action import HotkeyAction
from .actions.powerpoint_action import PowerPointAction


class FlowManager:

    def __init__(self):
        self.current_studio = None

        self.actions = {
            "launch": LaunchAction(),
            "wait": WaitAction(),
            "website": WebsiteAction(),
            "hotkey": HotkeyAction(),
            "powerpoint": PowerPointAction(),
        }

        with open(
            user_config_path("apps.json"),
            "r",
            encoding="utf-8"
        ) as f:
            self.apps = json.load(f)

        with open(
            user_config_path("flows.json"),
            "r",
            encoding="utf-8"
        ) as f:
            self.flows = json.load(f)

        self._upgrade_default_flows()

    # Older versions shipped a coding_flow that didn't match the Coding
    # Studio page (Chrome, a UI-freezing wait, File Explorer). If the user's
    # copy is still exactly that default, replace it; edited flows are kept.
    OLD_CODING_FLOW = [
        {"type": "launch", "target": "chrome"},
        {"type": "wait", "duration": 2},
        {"type": "website", "url": "https://github.com"},
        {"type": "hotkey", "keys": ["win", "e"]},
    ]

    def _upgrade_default_flows(self):

        current = self.flows.get("coding_flow", {})

        if current.get("actions") != self.OLD_CODING_FLOW:
            return

        try:
            with open(os.path.join(DEFAULT_CONFIG_DIR, "flows.json"), encoding="utf-8") as f:
                new = json.load(f).get("coding_flow")
        except (OSError, ValueError):
            return

        if not new:
            return

        self.flows["coding_flow"] = new

        try:
            with open(user_config_path("flows.json"), "w", encoding="utf-8") as f:
                json.dump(self.flows, f, indent=4, ensure_ascii=False)
            print("🔄 Updated coding_flow to the current default.")
        except OSError as e:
            print(f"⚠ Could not save updated flows: {e}")

    # =========================================================
    # OLD FLOW SYSTEM
    # =========================================================

    def execute_flow(self, flow_name):
        """
        Run every step of a flow. A step that fails doesn't stop the rest;
        afterwards a RuntimeError lists what didn't work.
        """

        flow = self.flows.get(flow_name)

        if not flow:
            raise ValueError(f'No flow called "{flow_name}".')

        print(f"🚀 Executing Flow: {flow['name']}")

        failures = []

        for step in flow["actions"]:

            action_type = step.get("type")
            action = self.actions.get(action_type)
            label = step.get("label") or step.get("target") or step.get("url") or action_type

            try:
                if action is None:
                    raise ValueError(f"unknown step type {action_type!r}")
                action.execute(step, self.apps)
            except Exception as e:
                print(f"❌ Flow step failed ({label}): {e}")
                failures.append(f"{label}: {e}")

        if failures:
            raise RuntimeError(
                f"{len(failures)} of {len(flow['actions'])} steps didn't work. "
                + " ".join(failures)
            )

    # =========================================================
    # EVENTS (custom studios and converted profiles)
    # =========================================================

    def execute_custom_event(self, event):
        """
        Run one event (see backend/automation/events.py).
        Raises an exception with a readable message if it fails.
        """

        if not event:
            raise ValueError("No event supplied.")

        action = event.get("action", "")
        value = str(event.get("value", "") or "").strip()

        print(
            f"🚀 Event: {event.get('name', 'Unnamed Event')} "
            f"[{action}: {value}]"
        )

        if action == "Open File":
            self.open_file(value)

        elif action == "Open Website":
            self.open_website(value)

        elif action in ("Launch Application", "Open Application"):
            self.launch_app(value)

        elif action == "Hotkey":
            self.actions["hotkey"].execute(
                {"keys": parse_hotkey(value)}
            )

        elif action == "PowerPoint":
            self.actions["powerpoint"].execute(
                {"command": powerpoint_command(value)},
                self.apps
            )

        elif action == "Run Flow":
            if value not in self.flows:
                raise ValueError(f'No flow called "{value}".')
            self.execute_flow(value)

        elif action == "Wait":
            try:
                seconds = float(value)
            except ValueError:
                raise ValueError(f'"{value}" is not a number of seconds.')
            time.sleep(seconds)

        elif action == "LensFlow":
            # Arm/disarm is handled by the gesture worker itself.
            pass

        else:
            raise ValueError(f'Unknown action "{action}".')

    # =========================================================
    # FILE HANDLING
    # =========================================================

    def open_file(self, file_path):

        if not file_path:
            raise ValueError("No file selected.")

        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        system = platform.system()

        if system == "Windows":
            os.startfile(file_path)
        elif system == "Darwin":
            subprocess.Popen(["open", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])

        print(f"✅ Opened file: {file_path}")

    # =========================================================
    # WEBSITE HANDLING
    # =========================================================

    def open_website(self, url):

        if not url:
            raise ValueError("No website given.")

        if "://" not in url:
            url = "https://" + url

        import webbrowser

        if not webbrowser.open(url):
            raise RuntimeError(f"Could not open {url}")

        print(f"✅ Opened website: {url}")

    # =========================================================
    # APP LAUNCHING
    # =========================================================

    def launch_app(self, app):
        """Launch an app; raises AppLaunchError if it can't be found."""

        target = launch_app(app, self.apps)

        print(
            f"✅ Launched {app} ({target})"
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