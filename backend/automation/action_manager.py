
import subprocess
import platform
import time
from backend.automation.flow_manager import FlowManager

class ActionManager:

    def __init__(self):
        self.active = False
        self.current_studio = None
        self.last_action = ""
        self.last_action_time = 0
        self.cooldown = 0.8
        self.flow_manager = FlowManager()   # seconds

    def execute(self, gesture, action):

        # Activation
        if action == "ACTIVATE":
            if not self.active:
                self.active = True
                print("✅ LensFlow Activated")
            return

        # Deactivation
        if action == "DEACTIVATE":
            if self.active:
                self.active = False
                print("🛑 LensFlow Deactivated")
            return

        # Ignore gestures while inactive
        if not self.active and not action.startswith("presentation"):
            return

        if action == "RUN_CURRENT_STUDIO":
            self.flow_manager.run_current_studio()
            return

        current_time = time.time()

        if (
            action == self.last_action and
            current_time - self.last_action_time < self.cooldown
        ):
            return

        print(f"Executing action: {action}")

        self.last_action = action
        self.last_action_time = current_time
        
        
        # Launch applicationsq
        # Execute Flow
        self.flow_manager.execute_flow(action)

    def launch(self, app):

        system = platform.system()

        try:

            if system == "Windows":
                subprocess.Popen(app, shell=True)

            elif system == "Darwin":
                subprocess.Popen(["open", "-a", app])

            elif system == "Linux":
                subprocess.Popen([app])

        except Exception as e:
            print(f"❌ Could not launch {app}: {e}")

    def set_current_studio(self, studio):
        self.current_studio = studio