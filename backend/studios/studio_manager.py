import json

from backend.paths import user_config_path


class StudioManager:

    def __init__(self):
        with open(
        user_config_path("studios.json"),
        "r",
        encoding="utf-8"
        ) as f:
            self.studios = json.load(f)

        

    def get_studios(self):

        with open(
            user_config_path("studios.json"),
            encoding="utf-8"
        ) as f:
            self.studios = json.load(f)

        return self.studios

    def get_studio(self, studio_id):

        for studio in self.studios:

            if studio["id"] == studio_id:
                return studio

        return None

    def save(self):
        with open(
            user_config_path("studios.json"),
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.studios,
                f,
                indent=4,
                ensure_ascii=False
            )
    
    def add_studio(self, name, description, icon):

        studio_id = name.lower().replace(" ", "_")
        for studio in self.studios:
            if studio["id"] == studio_id:
                print("❌ Studio already exists.")
                return

        studio = {
            "id": studio_id,
            "name": name,
            "description": description,
            "icon": icon,
            "flow": studio_id + "_flow",
            "last_used": "Never",
            "theme":"midnight"
        }

        self.studios.append(studio)


        self.save()

    def delete_studio(self, studio_id):
        self.studios = [
            studio
            for studio in self.studios
            if studio["id"] != studio_id
        ]


        self.save()

        print("✅ Studio deleted!")
    
    def update_studio(self, studio_id, name, description, icon, theme):
        print("Saving theme:", theme)
        for studio in self.studios:
            if studio["id"] == studio_id:
                studio["name"] = name
                studio["description"] = description
                studio["icon"] = icon
                studio["theme"] = theme
                break
        self.save()

    

    def get_studio_theme(self, studio_id):
        studio = self.get_studio(studio_id)
        if studio:
            return studio.get("theme", "dark")
        return "dark"
    
    def get_studio_accent(self, studio_id):
        studio = self.get_studio(studio_id)
        if studio:
            return studio.get("accent", "blue")
        return "blue"

    def get_gesture_profile(self, studio_id):
        studio = self.get_studio(studio_id)
        if studio:
            return studio.get("gesture_profile")
        return None


if __name__ == "__main__":
    manager = StudioManager()
    manager.add_studio(
        "Video Editing",
        "Everything ready for editing",
        "🎬"
    )
    manager.delete_studio("video_editing")
