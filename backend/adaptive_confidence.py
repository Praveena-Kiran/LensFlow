from mediapipe.python.solutions import selfie_segmentation
import json
import os

DEFAULT_THRESHOLD = 0.70
THRESHOLD_MARGIN = 0.05


class AdaptiveConfidence:

    def __init__(self):

        self.stats = {}

        self.profile_name = None

        self.profile_dir = os.path.join(
            os.path.dirname(__file__),
            "config",
            "confidence_profiles"
        )

    def load(self, profile_name):
        self.profile_name = profile_name
        path = os.path.join(
            self.profile_dir,
            f"{profile_name}.json"
        )
        if os.path.exists(path):

            with open(path, "r") as f:
                self.stats = json.load(f)
        else:

            self.stats = {}


    def save(self):
        os.makedirs(
        self.profile_dir,
        exist_ok=True
    )
        path = os.path.join(
            self.profile_dir,
            f"{self.profile_name}.json"
        )
        with open(path, "w", encoding="utf-8") as f:

            json.dump(
                self.stats,
                f,
                indent=4
            )
        path = os.path.join(
            self.profile_dir,
            f"{self.profile_name}.json"
        )
        with open(path, "w") as f:
            json.dump(self.stats, f, indent=4)

        

    def update(self, gesture, confidence):
        if gesture not in self.stats:
            self.stats[gesture] = {
                "average": confidence,
                "variance": 0.0,
                "samples": 1
            }
            return confidence
        stats = self.stats[gesture]
        average = stats["average"]
        variance = stats["variance"]
        samples = stats["samples"]
        samples += 1
        new_average = average + (confidence - average) / samples
        stats["average"] = new_average
        stats["samples"] = samples
        stats["variance"] = variance #update suing Welfords algo
        


    def get_threshold(self, gesture):
        if gesture not in self.stats:
            return DEFAULT_THRESHOLD

        average = self.stats[gesture]["average"]

        return average - THRESHOLD_MARGIN