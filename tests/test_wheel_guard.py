import os
import unittest

try:
    import PySide6  # noqa: F401
    HAVE_QT = True
except ImportError:  # CI's unit-test job installs only the standard library
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class WheelGuardTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        from frontend.components import wheel_guard
        cls.app = QApplication.instance() or QApplication([])
        cls.guard = wheel_guard.install(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.app.removeEventFilter(cls.guard)

    def wheel(self, widget, steps=-1):
        from PySide6.QtCore import QPoint, QPointF, Qt
        from PySide6.QtGui import QWheelEvent
        from PySide6.QtWidgets import QApplication

        pos = QPointF(widget.width() / 2, widget.height() / 2)
        event = QWheelEvent(
            pos, widget.mapToGlobal(pos), QPoint(0, 0), QPoint(0, 120 * steps),
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase, False,
        )
        QApplication.sendEvent(widget, event)
        self.app.processEvents()

    def build_page(self):
        from PySide6.QtWidgets import QComboBox, QScrollArea, QSlider, QVBoxLayout, QWidget

        area = QScrollArea()
        area.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        combo = QComboBox()
        combo.addItems(["one", "two", "three"])
        slider = QSlider()
        slider.setRange(0, 100)
        slider.setValue(50)
        layout.addWidget(combo)
        layout.addWidget(slider)
        layout.addSpacing(2000)          # tall page, so it can scroll
        area.setWidget(content)
        area.resize(300, 300)
        area.show()
        self.app.processEvents()
        self.addCleanup(area.deleteLater)
        return area, combo, slider

    def test_wheel_does_not_change_dropdown_or_slider(self):
        area, combo, slider = self.build_page()
        self.wheel(combo)
        self.wheel(slider)
        self.assertEqual(combo.currentText(), "one")
        self.assertEqual(slider.value(), 50)

    def test_wheel_over_dropdown_scrolls_the_page(self):
        area, combo, _ = self.build_page()
        self.assertEqual(area.verticalScrollBar().value(), 0)
        self.wheel(combo, steps=-1)
        self.assertGreater(area.verticalScrollBar().value(), 0)

    def test_clicking_still_works(self):
        _, combo, _ = self.build_page()
        combo.setCurrentIndex(2)      # what choosing from the popup does
        self.assertEqual(combo.currentText(), "three")


if __name__ == "__main__":
    unittest.main()
