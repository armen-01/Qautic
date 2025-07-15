from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QBrush, QPainterPath, QLinearGradient, QColor
from math import atan2, sin
import ui_colors

class FloatingWidgetPainter:
    def __init__(self, widget: QWidget, radius_corner:int = 1, radius_fillet:int = 1):
        self.widget = widget
        self.corner_radius = radius_corner
        self.fillet_radius = radius_fillet

    def paint(self, event):
        painter = QPainter(self.widget)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.widget.rect().adjusted(
            self.widget.SHADOW_PADDING, 
            self.widget.SHADOW_PADDING, 
            -self.widget.SHADOW_PADDING, 
            -self.widget.SHADOW_PADDING
        )
        
        # Draw background rectangle first
        bg_rect_path = QPainterPath()
        bg_rect_path.moveTo(rect.left() + self.corner_radius, rect.top())
        bg_rect_path.lineTo(rect.right() - self.widget.notch_width + (self.fillet_radius*2), rect.top())
        bg_rect_path.lineTo(rect.right() - self.widget.notch_width + (self.fillet_radius*2), rect.top() + self.widget.notch_height + self.fillet_radius)
        bg_rect_path.lineTo(rect.left(), rect.top() + self.widget.notch_height + self.fillet_radius)
        bg_rect_path.lineTo(rect.left(), rect.top() + self.corner_radius)
        bg_rect_path.quadTo(rect.left(), rect.top(), rect.left() + self.corner_radius, rect.top())
        bg_gradient = QLinearGradient(rect.right() - self.widget.notch_width, rect.top(), rect.left(), rect.top())
        bg_gradient.setColorAt(0, QColor(ui_colors.BASE_BACK_DARK))
        bg_gradient.setColorAt(1, QColor(ui_colors.BASE_BG))
        painter.fillPath(bg_rect_path, QBrush(bg_gradient))

        # Main shape gradient
        gradient = QLinearGradient(rect.right(), rect.top(), rect.right(), rect.top() + self.widget.notch_height)
        gradient.setColorAt(0, QColor(ui_colors.MAIN_BG))
        gradient.setColorAt(1, QColor(ui_colors.BASE_BG))
        brush = QBrush(gradient)
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)

        # Calculate key points
        p1 = (rect.right(), rect.top())  # Top right
        p2 = (rect.right() - self.widget.notch_width, rect.top())  # Top notch
        p3 = (rect.right() - self.widget.notch_width - self.widget.notch_slide, rect.top() + self.widget.notch_height)  # Angled point
        p4 = (rect.left(), rect.top() + self.widget.notch_height)  # Left point

        # Start path
        path = QPainterPath()
        path.moveTo(*p1)
        
        # First fillet (top to angle)
        t1, t2, cp = self._get_fillet_points(p1, p2, p3, self.fillet_radius)
        path.lineTo(*t1)
        path.quadTo(*cp, *t2)
        
        # Second fillet (angle to horizontal)
        t3, t4, cp2 = self._get_fillet_points(p2, p3, p4, self.fillet_radius)
        path.lineTo(*t3)
        path.quadTo(*cp2, *t4)
        
        # Third fillet (horizontal to vertical)
        t5, t6, cp3 = self._get_fillet_points(p3, p4, (p4[0], p4[1] + self.fillet_radius), self.fillet_radius)
        path.lineTo(*t5)
        path.quadTo(*cp3, *t6)
        
        # Continue with bottom part
        path.lineTo(rect.left(), rect.bottom() - self.corner_radius)
        path.quadTo(rect.left(), rect.bottom(), rect.left() + self.corner_radius, rect.bottom())
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(*p1)
        
        painter.drawPath(path)
        
        # Draw border line
        border_path = QPainterPath()
        border_path.moveTo(rect.right(), rect.top())
        border_path.lineTo(rect.left() + self.corner_radius, rect.top())
        border_path.quadTo(rect.left(), rect.top(), rect.left(), rect.top() + self.corner_radius)
        border_path.lineTo(rect.left(), rect.bottom() - self.corner_radius)
        border_path.quadTo(rect.left(), rect.bottom(), rect.left() + self.corner_radius, rect.bottom())
        border_path.lineTo(rect.right(), rect.bottom())
        
        painter.setPen(QColor(ui_colors.ELEMENT_LIGHT))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen = painter.pen()
        pen.setWidthF(1)
        painter.setPen(pen)
        painter.drawPath(border_path)

    def _get_fillet_points(self, p_prev, p_corner, p_next, radius):
        # Get vectors for the two lines
        v1x, v1y = p_corner[0] - p_prev[0], p_corner[1] - p_prev[1]
        v2x, v2y = p_next[0] - p_corner[0], p_next[1] - p_corner[1]
        
        # Normalize vectors
        len1 = (v1x**2 + v1y**2)**0.5
        len2 = (v2x**2 + v2y**2)**0.5
        v1x, v1y = v1x/len1, v1y/len1
        v2x, v2y = v2x/len2, v2y/len2
        
        # Calculate angle between vectors
        angle = atan2(v2y, v2x) - atan2(v1y, v1x)
        
        # Calculate tangent points
        tan_dist = radius / abs(sin(angle/2))
        
        # Calculate fillet points
        p1 = (p_corner[0] - v1x * tan_dist, p_corner[1] - v1y * tan_dist)
        p2 = (p_corner[0] + v2x * tan_dist, p_corner[1] + v2y * tan_dist)
        
        return p1, p2, p_corner