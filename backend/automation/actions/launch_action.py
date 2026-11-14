from backend.automation.app_launcher import launch_app


class LaunchAction:
    """Flow step {"type": "launch", "target": "<app name or path>"}."""

    def execute(self, step, apps):

        target = step.get("target")

        # Same resolution as studio events (apps.json, install folders,
        # Windows App Paths); raises AppLaunchError if it can't be found.
        launched = launch_app(target, apps)

        print(f"✅ Launched {target} ({launched})")
