from PIL.Image import item
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QSizePolicy


class FlowLayout(QLayout):

    def __init__(self, parent=None, margin=0, spacing=16):
        super().__init__(parent)

        self._items = []

        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()

        size += QSize(
            margins.left() + margins.right(),
            margins.top() + margins.bottom(),
        )

        return size

    def _do_layout(self, rect, test_only):
        print("LAYOUT WIDTH:", rect.width())
        x = rect.x()
        y = rect.y()

        line_height = 0

        for item in self._items:

            space = self.spacing()

            next_x = x + item.sizeHint().width() + space

            if next_x - space > rect.right() and line_height > 0:

                x = rect.x()
                y += line_height + space
                print("CARD SIZE:", item.sizeHint().width(), item.sizeHint().height())
                next_x = x + item.sizeHint().width() + space

                line_height = 0

            if not test_only:
                item.setGeometry(
                    QRect(
                        QPoint(x, y),
                        item.sizeHint(),
                    )
                )

            x = next_x

            line_height = max(
                line_height,
                item.sizeHint().height(),
            )

        return y + line_height - rect.y()