import time
import win32com.client


class PowerPointController:

    def __init__(self):
        self.app = None
        self.presentation = None
        self.slideshow = None

    def connect(self):
        try:
            self.app = win32com.client.GetActiveObject(
                "PowerPoint.Application"
            )

            print("PowerPoint Connected!")
            print(
                "Presentations:",
                self.app.Presentations.Count
            )

            if self.app.Presentations.Count == 0:
                print("❌ No presentation open.")
                return False

            self.presentation = self.app.ActivePresentation

            self._refresh_slideshow()

            return True

        except Exception as e:
            print("❌ PowerPoint connection error:", e)
            return False

    def _refresh_slideshow(self):
        """Get the currently running slideshow window."""

        try:
            if self.app.SlideShowWindows.Count > 0:
                self.slideshow = (
                    self.app.SlideShowWindows(1).View
                )

                print("🎬 Slideshow connected.")

                return True

            self.slideshow = None

            return False

        except Exception as e:
            print("❌ Could not get slideshow:", e)

            self.slideshow = None

            return False

    def start_presentation(self):

        if not self.connect():
            return

        print(
            "Presentation:",
            self.presentation.Name
        )

        print(
            "SlideShowWindows:",
            self.app.SlideShowWindows.Count
        )

        try:
            self.presentation.SlideShowSettings.Run()

            # Give PowerPoint a moment to create
            # the slideshow window.
            time.sleep(0.5)

            self._refresh_slideshow()

            if self.slideshow:
                print("▶ Presentation Started")
            else:
                print("❌ Presentation started, but slideshow window not found.")

        except Exception as e:
            print("❌ Could not start presentation:", e)

    def end_presentation(self):

        if not self.connect():
            return

        # Refresh in case the slideshow was created
        # after the initial connection.
        if not self._refresh_slideshow():
            print("⚠ No active slideshow to end.")
            return

        try:
            self.slideshow.Exit()

            self.slideshow = None

            print("⏹ Presentation Ended")

        except Exception as e:
            print("❌ Could not end presentation:", e)

    def next_slide(self):

        if not self.connect():
            return

        # IMPORTANT:
        # Get the current slideshow every time.
        if not self._refresh_slideshow():
            print("⚠ No active slideshow.")
            return

        try:
            current = self.slideshow.CurrentShowPosition

            print(
                f"➡ Moving from slide {current} "
                f"to {current + 1}"
            )

            self.slideshow.GotoSlide(
                current + 1
            )

            print("➡ Next Slide")

        except Exception as e:
            print("❌ Could not move to next slide:", e)

    def previous_slide(self):

        if not self.connect():
            return

        if not self._refresh_slideshow():
            print("⚠ No active slideshow.")
            return

        try:
            current = self.slideshow.CurrentShowPosition

            if current <= 1:
                print("⚠ Already on the first slide.")
                return

            print(
                f"⬅ Moving from slide {current} "
                f"to {current - 1}"
            )

            self.slideshow.GotoSlide(
                current - 1
            )

            print("⬅ Previous Slide")

        except Exception as e:
            print(
                "❌ Could not move to previous slide:",
                e
            )
        
