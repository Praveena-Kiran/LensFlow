import json

from backend.paths import user_config_path


class GestureProfileManager:

    def __init__(self):
        self.file_path = user_config_path("gesture_profiles.json")

        self.load()

    def load(self):
        with open(
            self.file_path,
            "r",
            encoding="utf-8"
        ) as f:
            self.profiles = json.load(f)

    def save(self):
        with open(
            self.file_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.profiles,
                f,
                indent=4,
                ensure_ascii=False
            )

    def get_profiles(self):
        return self.profiles

    def get_profile(self, profile_id):
        for profile in self.profiles:
            if profile["id"] == profile_id:
                return profile
        return None

    def add_profile(self, profile):
        self.profiles.append(profile)
        self.save()

    def update_profile(self, profile_id, updated_profile):
        for i, profile in enumerate(self.profiles):
            if profile["id"] == profile_id:
                self.profiles[i] = updated_profile
                self.save()
                return True
        return False

    def delete_profile(self, profile_id):
        self.profiles = [
            profile
            for profile in self.profiles
            if profile["id"] != profile_id
        ]
        self.save()