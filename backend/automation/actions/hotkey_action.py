try:
    import pyautogui
except Exception:  # not installed, or no display available
    pyautogui = None


class HotkeyAction:

    def execute(self, step, apps=None):

        keys = step.get("keys", [])

        if not keys:
            raise ValueError("No hotkeys provided.")

        if pyautogui is None:
            raise RuntimeError("Hotkeys need the pyautogui package.")

        print(f"⌨️ Pressing {' + '.join(keys)}")

        pyautogui.hotkey(*keys)
