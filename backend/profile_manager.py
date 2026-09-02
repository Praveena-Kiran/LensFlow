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
        self.current_profile_name = None

    def load(self, profile_name):

        path = os.path.join(
            self.profile_dir,
            f"{profile_name}.json"
        )

        with open(path, encoding="utf-8") as f:
            self.current_profile = json.load(f)

        self.current_profile_name = profile_name

        print(
            f"[OK] Loaded profile: "
            f"{self.current_profile['name']}"
        )

    def get_profile_name(self):

        if not self.current_profile:
            return None

        return self.current_profile["name"]

    def get_gesture_map(self):

        if not self.current_profile:
            return {}

        return self.current_profile["gesture_map"]

    def update_gesture(self, gesture, action):

        if not self.current_profile:
            return

        self.current_profile["gesture_map"][gesture] = action

        self.save_profile()

    def remove_gesture(self, gesture):

        if not self.current_profile:
            return

        if gesture in self.current_profile["gesture_map"]:
            del self.current_profile["gesture_map"][gesture]

        self.save_profile()

    def save_profile(self):

        if not self.current_profile:
            return

        profile_name = self.current_profile_name

        path = os.path.join(
            self.profile_dir,
            f"{profile_name}.json"
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.current_profile,
                f,
                indent=4,
                ensure_ascii=False
            )

        print(
            f"[OK] Saved profile: {profile_name}"
        )


if __name__ == "__main__":

    pm = ProfileManager()

    pm.load("coding")

    print(
        pm.get_gesture_map()
    )