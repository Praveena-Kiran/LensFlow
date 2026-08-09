import win32com.client


class PowerPointController:

    def __init__(self):
        self.app = None
        self.presentation = None
        self.slideshow = None

    def connect(self):
        try:
            self.app = win32com.client.GetActiveObject("PowerPoint.Application")

            print("PowerPoint Connected!")
            print("Presentations:", self.app.Presentations.Count)

            if self.app.Presentations.Count == 0:
                print("❌ No presentation open.")
                return False

            self.presentation = self.app.ActivePresentation

            if self.app.SlideShowWindows.Count > 0:
                self.slideshow = self.app.SlideShowWindows(1).View
            else:
                self.slideshow = None

            return True

        except Exception as e:
            print("❌", e)
            return False

    def start_presentation(self):
        if self.connect():

            print("Presentation:", self.presentation.Name)
            print("SlideShowWindows:", self.app.SlideShowWindows.Count)

            self.presentation.SlideShowSettings.Run()

            print("▶ Presentation Started")

    def end_presentation(self):
        if self.connect() and self.slideshow:
            self.slideshow.Exit()
            print("⏹ Presentation Ended")

    def next_slide(self):
        if self.connect() and self.slideshow:
            current = self.slideshow.CurrentShowPosition
            self.slideshow.GotoSlide(current + 1)
            print("➡ Next Slide")

    def previous_slide(self):
        if self.connect() and self.slideshow:
            current = self.slideshow.CurrentShowPosition
            self.slideshow.GotoSlide(current - 1)
            print("⬅ Previous Slide")