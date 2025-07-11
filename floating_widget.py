from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect, QApplication, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QPushButton, QSizePolicy, QFileIconProvider
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QFileInfo
from PyQt6.QtGui import QColor, QPixmap
import os
import json
from floating_widget_painter import FloatingWidgetPainter
from ui_sub_widgets.hide_button import HideButton
from ui_sub_widgets.splitter import StyledSplitter
from ui_sub_widgets.list_base import ListBase
from ui_sub_widgets.settings_tile import SettingsTile
from ui_sub_widgets.program_item import ProgramItem

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
        layout_top = QHBoxLayout(self)
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

        # Programs
        self.programs_area = ListBase(self, label="Programs", sz=74)
        self.programs_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'programs.json')
        self._load_programs()
        self._add_plus_button()
        # Settings
        settings_area = ListBase(self, self.main_radius - (self.splitter_height*2.4), label="Auto Settings", sz=92)
        settings_area.sz = 120
        tile_wifi = SettingsTile(0, "\uE1D8", "\uE1DA", ["On", "Off"], 2, "WiFi", settings_area.list_widget) #WiFi
        tile_bt = SettingsTile(0, "\uE1A7", "\uE1A9", ["On", "Off"], 2, "Bluetooth", settings_area.list_widget) #BT
        tile_brightness = SettingsTile(1, "\uE1AC", "\uE1AD", [], 0, "Brightness", settings_area.list_widget) #Brightness
        tile_volume = SettingsTile(1, "\uE050", "\uE04F", [], 0, "Volume", settings_area.list_widget) #Volume
        tile_performance = SettingsTile(0, "\uE322", "\uE4FF",  ["Performance", "Off", "idk"], 3, "Performance Mode", settings_area.list_widget) #Performance Mode
        tile_nightlight = SettingsTile(0, "\uF34F", "\uEB76", ["On", "Off"], 2, "Night Light", settings_area.list_widget) #Night light
        tile_airplane = SettingsTile(0, "\uE195", "\uE194", ["On", "Off"], 2, "Airplane Mode", settings_area.list_widget)
        tile_notifications = SettingsTile(0, "\uE7F7", "\uE7F6", ["On", "Off"], 2, "Notifications", settings_area.list_widget)
        tile_hotspot = SettingsTile(0, "\uE1E2", "\uE0CE", ["On", "Off"], 2, "Hotspot", settings_area.list_widget)
        tile_systemcolor = SettingsTile(0, "\uEB37", "\uEC72", ["Light", "Dark"], 2, "System Color", settings_area.list_widget)
        tile_wifi5 = SettingsTile(0, "\uE1D8", "\uE1DA", ["On", "Off"], 2, "WiFi", settings_area.list_widget)
        tile_wifi6 = SettingsTile(0, "\uE1D8", "\uE1DA", ["On", "Off"], 2, "WiFi", settings_area.list_widget)
        
        ## Splitter ##
        splitter = StyledSplitter(Qt.Orientation.Vertical, self)
        splitter.setHandleWidth(self.splitter_height)
        splitter.addWidget(self.programs_area)
        splitter.addWidget(settings_area)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([(self.WIDGET_HEIGHT-self.splitter_height-self.notch_height)//2, (self.WIDGET_HEIGHT-self.splitter_height-self.notch_height)//2])
        splitter.setContentsMargins(int(self.splitter_height*1.5), int(self.splitter_height*1.5), 0, int(self.splitter_height*1.5))

        ## Add splitter to main layout ##
        layout.addWidget(splitter)
        layout.setStretch(0, self.notch_height)
        layout.setStretch(1, self.WIDGET_HEIGHT-self.splitter_height-self.notch_height)
        self.setLayout(layout)

    def _add_plus_button(self):
        from PyQt6.QtWidgets import QListWidgetItem
        plus_item = QListWidgetItem()
        plus_button = QPushButton("+")
        #plus_button.setFixedSize(48, 48)
        plus_button.setStyleSheet('''QPushButton {font-size: 18px; color: #aaa; background: transparent;}
                                  QPushButton:pressed, QPushButton:checked, QPushButton:hover, QPushButton:focus {background: transparent; border: none; outline: none;}''')
        plus_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        plus_button.clicked.connect(self._on_add_program)
        lw = self.programs_area.list_widget
        lw.addItem(plus_item)
        lw.setItemWidget(plus_item, plus_button)
        self.plus_item = plus_item

    def _on_add_program(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Executables (*.exe)")
        if file_dialog.exec():
            exe_path = file_dialog.selectedFiles()[0]
            exe_name = os.path.splitext(os.path.basename(exe_path))[0]
            icon_provider = QFileIconProvider()
            icon = icon_provider.icon(QFileInfo(exe_path))
            prog_item = ProgramItem(
                name=exe_name,
                path=exe_path,
                priority=-1,
                icon=icon
            )
            # Insert before the plus button
            lw = self.programs_area.list_widget
            lw.insertItem(lw.count()-1, prog_item)
            self._save_programs()

    def _load_programs(self):
        if os.path.exists(self.programs_json_path):
            with open(self.programs_json_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []
            icon_provider = QFileIconProvider()
            for entry in data:
                icon = icon_provider.icon(QFileInfo(entry['path'])) if os.path.exists(entry['path']) else None
                prog_item = ProgramItem(
                    name=entry['name'],
                    path=entry['path'],
                    priority=entry.get('priority', -1),
                    icon=icon
                )
                self.programs_area.add_item(prog_item)

    def _save_programs(self):
        lw = self.programs_area.list_widget
        programs = []
        for i in range(lw.count()):
            item = lw.item(i)
            # Skip the plus button
            if lw.itemWidget(item):
                continue
            if hasattr(item, 'name') and hasattr(item, 'path'):
                programs.append({
                    'name': item.name,
                    'path': item.path,
                    'priority': item.priority
                })
        with open(self.programs_json_path, 'w', encoding='utf-8') as f:
            json.dump(programs, f, indent=2)

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