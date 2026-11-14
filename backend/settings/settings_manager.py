import json
import os

from backend.paths import user_config_path


class SettingsManager:

    def __init__(self):

        self.settings_file = user_config_path("settings.json")

        with open(
            self.settings_file,
            encoding="utf-8"
        ) as f:

            self.settings = json.load(f)

    def get_setting(self, key):
        return self.settings.get(key)

    def get_theme(self):
        return self.get_setting("theme")

    def set_theme(self, theme):
        self.set_setting("theme", theme)

    def get_accent(self):
        return self.get_setting("accent")


    def set_accent(self, accent):
        self.set_setting("accent", accent)

    def set_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def save_settings(self):
        with open(
            self.settings_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.settings,
                f,
                indent=4
            )

if __name__ == "__main__":
    settings = SettingsManager()
    print(settings.get_setting("theme"))
    settings.set_setting("theme", "light")