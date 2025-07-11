from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QSplitterHandle
from PyQt6.QtGui import QPainter, QColor

class StyledSplitter(QSplitter):
    def createHandle(self):
        return StyledSplitterHandle(self.orientation(), self)

class StyledSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.setCursor(Qt.CursorShape.SizeVerCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        width = 40
        x = (rect.width() - width) // 2
        y = rect.height() // 2
        painter.setPen(QColor("#3e3e3e"))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen = painter.pen()
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(x, y, rect.width() - x, y)