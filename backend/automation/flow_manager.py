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
    "powerpoint": PowerPointAction()
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
                print(f"❌ Unknown action type: {action_type}")

    def get_apps_for_flow(self, flow_name):

        flow = self.flows.get(flow_name)
        if not flow:
            return []

        items = []

        for step in flow["actions"]:
            if step["type"] == "launch":
                app = step.get("target")

                if app:
                    items.append(app.title())

            elif step["type"] == "website":
                url = step.get("url", "").lower()

                if "github" in url:
                    items.append("🌐 GitHub")

                elif "chatgpt" in url:
                    items.append("🌐 ChatGPT")

                elif "stackoverflow" in url:
                    items.append("🌐 Stack Overflow")

                else:
                    items.append("🌐 Website")

        return items

    
    def launch_app(self, app):
        system = platform.system()

        try:

            if system == "Windows":
                subprocess.Popen(app, shell=True)

            elif system == "Darwin":
                subprocess.Popen(["open", "-a", app])

            elif system == "Linux":
                subprocess.Popen([app])

            print(f"✅ Launched {app}")

        except Exception as e:
            print(f"❌ Could not launch {app}: {e}")

    def set_current_studio(self, studio):
        self.current_studio = studio


    def run_current_studio(self):
        if not self.current_studio:
            print("⚠ No studio selected.")
            return

        self.execute_flow(self.current_studio["flow"])    

if __name__ == "__main__":
    fm = FlowManager()
    fm.execute_flow("presentation_flow")

