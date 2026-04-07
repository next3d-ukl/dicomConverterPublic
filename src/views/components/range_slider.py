from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QPalette
from PyQt5.QtCore import Qt, pyqtSignal, QRect

class RangeSlider(QWidget):
    valuesChanged = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(30)
        self._minimum = -2000
        self._maximum = 4000
        self._low = -100
        self._high = 200
        self.active_handle = None

    def setMinimum(self, val):
        self._minimum = val
        self.update()

    def setMaximum(self, val):
        self._maximum = val
        self.update()

    def setLow(self, val):
        self._low = max(self._minimum, min(val, self._high))
        self.update()

    def setHigh(self, val):
        self._high = max(self._low, min(val, self._maximum))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Track line
        track_rect = QRect(10, height//2 - 2, width - 20, 4)
        painter.setBrush(QColor(200, 200, 200))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, 2, 2)
        
        range_span = self._maximum - self._minimum
        if range_span == 0:
            return

        low_x = 10 + int((self._low - self._minimum) / range_span * (width - 20))
        high_x = 10 + int((self._high - self._minimum) / range_span * (width - 20))
        
        # Highlighted track
        highlight_rect = QRect(low_x, height//2 - 2, high_x - low_x, 4)
        painter.setBrush(self.palette().color(QPalette.Highlight))
        painter.drawRoundedRect(highlight_rect, 2, 2)
        
        # Handles
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        
        painter.drawEllipse(low_x - 6, height//2 - 6, 12, 12)
        painter.drawEllipse(high_x - 6, height//2 - 6, 12, 12)

    def mousePressEvent(self, event):
        pos = event.pos().x()
        width = self.width()
        range_span = self._maximum - self._minimum
        
        low_x = 10 + int((self._low - self._minimum) / range_span * (width - 20))
        high_x = 10 + int((self._high - self._minimum) / range_span * (width - 20))
        
        if abs(pos - low_x) < abs(pos - high_x):
            self.active_handle = 'low'
        else:
            self.active_handle = 'high'
            
        self.update_value(pos)

    def mouseMoveEvent(self, event):
        if self.active_handle:
            self.update_value(event.pos().x())

    def mouseReleaseEvent(self, event):
        self.active_handle = None

    def update_value(self, pos):
        width = self.width()
        range_span = self._maximum - self._minimum
        
        val = self._minimum + (pos - 10) / (width - 20) * range_span
        val = max(self._minimum, min(self._maximum, int(val)))
        
        changed = False
        if self.active_handle == 'low':
            if val <= self._high and val != self._low:
                self._low = val
                changed = True
        elif self.active_handle == 'high':
            if val >= self._low and val != self._high:
                self._high = val
                changed = True
                
        self.update()
        if changed:
            self.valuesChanged.emit(self._low, self._high)
