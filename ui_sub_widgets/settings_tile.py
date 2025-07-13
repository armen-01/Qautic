from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSlider, QListWidgetItem, QPushButton, QSizePolicy, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase
import os

class SettingsTileWidget(QWidget):
    def __init__(self, type_: int, symbol_on: str, symbol_off: str, options: list[str], options_count: int, tooltip: str, parent=None):
        super().__init__(parent)
        self.type_ = type_
        self.symbol_on = symbol_on
        self.symbol_off = symbol_off
        self.options = options
        self.options_count = options_count
        self.tile_value = 0
        self.is_unchanged = True  # True = unchanged, False = normal/cycling
        self.ttip = tooltip
        self._setup_fonts()
        self._init_ui()

    def _setup_fonts(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_font_path = os.path.join(base_dir, 'assets', 'fonts', 'MaterialSymbolsRounded-VariableFont_FILL,GRAD,opsz,wght.ttf')
        text_font_path = os.path.join(base_dir, 'assets', 'fonts', 'MuseoModerno-VariableFont_wght.ttf')
        self.icon_font_id = QFontDatabase.addApplicationFont(icon_font_path)
        self.text_font_id = QFontDatabase.addApplicationFont(text_font_path)
        self.icon_font_family = QFontDatabase.applicationFontFamilies(self.icon_font_id)[0]
        self.text_font_family = QFontDatabase.applicationFontFamilies(self.text_font_id)[0]

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 5)
        layout.setSpacing(0)
        # Icon label
        self.icon_label = QLabel(self.symbol_on, self)
        self.icon_label.setToolTip(self.ttip)
        icon_font = QFont(self.icon_font_family)
        icon_font.setPointSize(20)
        self.icon_label.setFont(icon_font)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_icon_color()
        layout.addWidget(self.icon_label)
        # Incremental type
        if self.type_ == 0:
            initial_text = "-" if self.is_unchanged else (self.options[0] if self.options else "")
            self.value_button = QPushButton(initial_text, self)
            text_font = QFont(self.text_font_family)
            text_font.setPointSize(11)
            self.value_button.setFont(text_font)
            self.value_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.value_button.setFlat(True)
            self.value_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.set_button_color()
            self.value_button.clicked.connect(self.cycle_option)
            layout.addWidget(self.value_button, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        # Slider type
        elif self.type_ == 1:
            layout.setSpacing(10)
            self.slider = QSlider(Qt.Orientation.Horizontal, self)
            self.slider.valueChanged.connect(self._slider_value_changed)
            self.slider.setRange(0, 100)
            self.slider.setValue(0)
            self.slider.setStyleSheet('''
                QSlider {
                    min-height: 18px;
                    max-height: 18px;
                    padding-bottom: 10px;
                    padding-left: 10px;
                    padding-right: 10px;
                }
                QSlider::groove:horizontal {
                    border: none;
                    height: 18px;
                    border-radius: 0px;
                    background: #4a4a4a;
                }
                QSlider::sub-page:horizontal {
                    background: #777;
                    border-radius: 0px;
                }
                QSlider::add-page:horizontal {
                    background: #4a4a4a;
                    border-radius: 9px;
                }
                QSlider::handle:horizontal {
                    background: #ccc;
                    border: none;
                    width: 10px;
                    margin: 0;
                }
            ''')
            layout.addWidget(self.slider)
            self.slider.sliderPressed.connect(self.enable_slider)
        # Text field type (type_ == 2)
        elif self.type_ == 2:
            self.text_field = QLineEdit("0", self)
            text_font = QFont(self.text_font_family)
            text_font.setPointSize(12)
            self.text_field.setFont(text_font)
            self._set_text_field_style(enabled=not self.is_unchanged)
            self.text_field.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.text_field.textChanged.connect(self._on_text_field_changed)
            layout.addWidget(self.text_field, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.setLayout(layout)

    def _set_text_field_style(self, enabled=True):
        color = "#eee" if enabled else "#666"
        self.text_field.setStyleSheet(f'''
            background: #363636;
            border: 1px solid #4a4a4a;
            color: {color};
            border-radius: 10px;
            padding: 6px 10px;
        ''')

    def _on_text_field_changed(self, value):
        self.tile_value = value
        if self.is_unchanged:
            self.is_unchanged = False
            self.set_icon_color()
            self._set_text_field_style(enabled=True)

    def _slider_value_changed(self, value):
        self.tile_value = value
        self.slider.setToolTip(f"{value}%")

    def set_icon_color(self):
        # Set icon color based on current_index and options_count
        if self.type_ == 0 and self.options_count == 2:
            color = self._get_toggle_color()
        elif (self.type_ == 0 and self.is_unchanged) or (self.type_ == 1 and self.is_unchanged) or (self.type_ == 2 and self.is_unchanged):
            self.icon_label.setText(self.symbol_off)
            color = "#666"
        else:
            color = "#eee"
            self.icon_label.setText(self.symbol_on)
        self.icon_label.setStyleSheet(f"color: {color};")

    def set_button_color(self):
        # Set button color based on current_index and options_count
        if self.type_ == 0 and self.options_count == 2:
            color = self._get_toggle_color()
        elif self.type_ == 0 and self.is_unchanged:
            color = "#666"
        else:
            color = "#eee"
        self.value_button.setStyleSheet(f'''
            QPushButton {{
                background: transparent;
                border: none;
                outline: none;
                color: {color}; }}
            QPushButton:pressed, QPushButton:checked, QPushButton:hover, QPushButton:focus {{
                background: transparent;
                border: none;
                outline: none;
                color: {color}; }}
            ''')

    def _get_toggle_color(self):
        # Helper for 2-option toggle color
        if self.is_unchanged:
            self.icon_label.setText(self.symbol_off)
            return "#666"
        elif self.tile_value == 0:
            self.icon_label.setText(self.symbol_on)
            return "#eee"
        else:
            return "#666"

    def enable_slider(self):
        if self.is_unchanged:
            self.is_unchanged = False
            self.set_icon_color()

    def cycle_option(self):
        if self.type_ == 0 and self.options_count > 0 and not self.is_unchanged:
            self.tile_value = (self.tile_value + 1) % self.options_count
            self.value_button.setText(str(self.options[self.tile_value]))
            self.set_button_color()
            self.set_icon_color()
            self.value_button.repaint()
            self.repaint()

    def mousePressEvent(self, event):
        if self.type_ == 0:
            if event.button() == Qt.MouseButton.RightButton:
                self.is_unchanged = True
                self.value_button.setText("-")
                self.set_button_color()
                self.set_icon_color()
                self.value_button.repaint()
                self.repaint()
            elif event.button() == Qt.MouseButton.LeftButton:
                if self.is_unchanged:
                    self.is_unchanged = False
                    self.tile_value = 0
                    self.value_button.setText(str(self.options[self.tile_value]))
                    self.set_button_color()
                    self.set_icon_color()
                    self.value_button.repaint()
                    self.repaint()
                else:
                    self.cycle_option()
            else:
                super().mousePressEvent(event)
        elif self.type_ == 1:
            if event.button() == Qt.MouseButton.RightButton:
                self.is_unchanged = True
                self.set_icon_color()
            else:
                super().mousePressEvent(event)
        elif self.type_ == 2:
            if event.button() == Qt.MouseButton.RightButton:
                self.is_unchanged = True
                self.set_icon_color()
                self._set_text_field_style(enabled=False)
                self.text_field.repaint()
                self.repaint()
            elif event.button() == Qt.MouseButton.LeftButton:
                if self.is_unchanged:
                    self.is_unchanged = False
                    self.set_icon_color()
                    self._set_text_field_style(enabled=True)
                    self.text_field.repaint()
                    self.repaint()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

class SettingsTile(QListWidgetItem):
    def __init__(self, type_: int, symbol_on: str, symbol_off: str, options: list[str], options_count: int, tooltip: str, parent_list):
        super().__init__(parent_list)
        self.widget = SettingsTileWidget(type_, symbol_on, symbol_off, options, options_count, tooltip)
        parent_list.setItemWidget(self, self.widget)
