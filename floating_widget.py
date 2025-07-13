from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect, QApplication, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QColor, QPixmap
import os
from floating_widget_painter import FloatingWidgetPainter
from ui_sub_widgets.hide_button import HideButton
from floating_widget_menu_main import FloatingWidgetMenuMain

class FloatingWidget(QWidget):
    WIDGET_WIDTH:int
    WIDGET_HEIGHT:int
    SHADOW_PADDING = 35

    def __init__(self, target_x:int, target_y:int, width:int, height:int, parent=None):
        super().__init__(parent)
        self.WIDGET_WIDTH = width
        self.WIDGET_HEIGHT = height
        self.setFixedSize(self.WIDGET_WIDTH + 2 * self.SHADOW_PADDING, self.WIDGET_HEIGHT + 2 * self.SHADOW_PADDING)
        self.target_x = target_x
        self.target_y = target_y
        self._is_animating = False

        self.notch_height = 87
        self.notch_width = 115
        self.notch_slide = 50
        self.splitter_height = 8
        self.main_radius = 80

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        #self._add_shadow()
        self.move(self.target_x, self.target_y)
        self._init_layout()
        self.painter = FloatingWidgetPainter(self, self.main_radius, 10)

    def _add_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(self.SHADOW_PADDING)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def _init_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.SHADOW_PADDING, self.SHADOW_PADDING, self.SHADOW_PADDING, self.SHADOW_PADDING)
        layout.setSpacing(0)
        layout_top = QHBoxLayout()
        layout_top.setSpacing(0)
        layout.insertLayout(0, layout_top)
        
        ## Widgets ##
        # Logo
        logo_main = QLabel("logo", self)
        logo_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'graphics', 'logo_qautic.png')
        logo_picture = QPixmap(image_path)
        logo_main.setPixmap(logo_picture.scaledToHeight(self.notch_height - 30, Qt.TransformationMode.SmoothTransformation))
        logo_main.setContentsMargins(5, 0, 0, 0)
        logo_main.setFixedHeight(self.notch_height)
        # Hide button
        hide_button = HideButton(self)
        hide_button.setContentsMargins(10, 5, 0, 0)
        hide_button.setFixedHeight(self.notch_height)
        
        ## Top layout ##
        layout_top.addWidget(logo_main)
        layout_top.addWidget(hide_button)
        top_midpoint = (self.notch_width + self.notch_slide//2)
        layout_top.setStretch(0, self.WIDGET_WIDTH - top_midpoint)
        layout_top.setStretch(1, top_midpoint)

        ## Set menu here ##
        main_menu = FloatingWidgetMenuMain(self)
        
        ## Add splitter to main layout ##
        layout.addWidget(main_menu)
        layout.setStretch(0, self.notch_height)
        layout.setStretch(1, self.WIDGET_HEIGHT-self.splitter_height-self.notch_height)
        
        self.setLayout(layout)

    def paintEvent(self, event):
        self.painter.paint(event)

    def slide_in(self):
        if self._is_animating or self.isVisible():
            return
        self._is_animating = True
        self.show()
        self.raise_()
        start_x = QApplication.primaryScreen().availableGeometry().right()
        end_x = self.target_x - self.SHADOW_PADDING
        y = self.target_y - self.SHADOW_PADDING
        anim = QPropertyAnimation(self, b'pos', self)
        anim.setDuration(700)
        anim.setStartValue(QPoint(start_x, y))
        anim.setEndValue(QPoint(end_x, y))
        anim.setEasingCurve(QEasingCurve.Type.OutExpo)
        anim.finished.connect(self._on_slide_in_finished)
        anim.start()
        self.anim = anim

    def _on_slide_in_finished(self):
        self._is_animating = False

    def slide_out(self):
        if self._is_animating or not self.isVisible():
            return
        self._is_animating = True
        start_x = self.target_x - self.SHADOW_PADDING
        end_x = QApplication.primaryScreen().availableGeometry().right()
        y = self.target_y - self.SHADOW_PADDING
        anim = QPropertyAnimation(self, b'pos', self)
        anim.setDuration(900)
        anim.setStartValue(QPoint(start_x, y))
        anim.setEndValue(QPoint(end_x, y))
        anim.setEasingCurve(QEasingCurve.Type.OutExpo)
        anim.finished.connect(self._on_slide_out_finished)
        anim.start()
        self.anim = anim

    def _on_slide_out_finished(self):
        self._is_animating = False
        self.hide()