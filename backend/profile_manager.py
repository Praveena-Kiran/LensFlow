import json
import os


class ProfileManager:

    def __init__(self):

        self.profile_dir = os.path.join(
            os.path.dirname(__file__),
            "config",
            "profiles"
        )

        self.current_profile = None

    def load(self, profile_name):

        path = os.path.join(
            self.profile_dir,
            f"{profile_name}.json"
        )

        with open(path, encoding="utf-8") as f:
            self.current_profile = json.load(f)

        print(f"[OK] Loaded profile: {self.current_profile['name']}")

    def get_gesture_map(self):

        return self.current_profile["gesture_map"]


if __name__ == "__main__":
    pm = ProfileManager()
    pm.load("coding")
    print(pm.get_gesture_map())