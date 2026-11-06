try:
    import pyautogui
except Exception:  # not installed, or no display available
    pyautogui = None


class HotkeyAction:

    def execute(self, step, apps=None):

        keys = step.get("keys", [])

        if not keys:
            print("❌ No hotkeys provided.")
            return

        if pyautogui is None:
            print("❌ Hotkeys need the pyautogui package.")
            return

        print(f"⌨️ Pressing {' + '.join(keys)}")

        pyautogui.hotkey(*keys)
