from PyQt6.QtWidgets import QWidget, QListWidget, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy, QListWidgetItem, QApplication, QStyle
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QFontDatabase, QIcon
import os

class SnapListWidget(QListWidget):
    def wheelEvent(self, event):
        # Scroll exactly one item per wheel step
        num_degrees = event.angleDelta().y() / 8
        num_steps = int(num_degrees / 15)
        if num_steps != 0:
            current = self.verticalScrollBar().value()
            grid_sz = self.parent().sz
            direction = -1 if num_steps > 0 else 1
            new_val = current + direction * grid_sz
            self.verticalScrollBar().setValue(new_val)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if hasattr(item, 'handle_mouse_event'):
            item.handle_mouse_event(event)
        super().mousePressEvent(event)

class ListBase(QWidget):
    _instances = []
    def __init__(self, parent=None, bottom_radius:int = 10, label:str = "Label", sz:int = 74):
        super().__init__(parent)
        self.sz = sz
        ListBase.sz = sz
        ListBase._instances.append(self)

        color_border = "#4a4a4a"
        color_bg = "#363636"
        color_font = "#eee"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Static Header Label
        self.header_label = QLabel(label, self)
        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts', 'MuseoModerno-VariableFont_wght.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        font = QFont(font_families[0])
        font.setPointSizeF(12.5)
        self.header_label.setFont(font)
        self.header_label.setObjectName("base_list_header")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setStyleSheet(f"""
            #base_list_header {{
            background-color: {color_bg};
            border-left: 1px solid {color_border};
            border-top: 1px solid {color_border};
            color: {color_font};
            border-top-left-radius: 10px;
            border-bottom: 1px solid;
            border-bottom-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:.05 {color_bg}, stop:0.5 {color_font}, stop:.95 {color_bg});
            }}
        """)

        # List Widget
        self.list_widget = SnapListWidget(self)
        self.list_widget.setObjectName("base_list")
        # Common stylesheet for the list widget (except ::item selector)
        common_style = f"""
            #base_list {{
            outline: 0;
            background-color: {color_bg};
            border-left: 1px solid {color_border};
            border-bottom: 1px solid {color_border};
            border-bottom-left-radius: {bottom_radius}px;
            padding-right: 5px;
            padding-left: 15px;
            padding-top: 5px;
            padding-bottom: 0px;
            }}
            QScrollBar:vertical {{
            background: transparent;
            width: 5px;
            }}
            QScrollBar::handle:vertical {{
            background: {color_border};
            min-height: 20px;
            border-radius: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
            background: #666;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            }}
        """

        # Conditional item styling
        if label == "Programs":
            item_style = f"""
            #base_list::item {{
            margin: 2.5px;
            padding-top: 10px;
            padding-bottom: 10px;
            padding-left: 5px;
            padding-right: 5px;
            border-radius: 15px;
            border: 1px solid {color_border};
            color: {color_font};
            min-width: {self.sz}px;
            min-height: {self.sz}px;
            max-width: {self.sz}px;
            max-height: {self.sz}px;
            }}
            #base_list::item:selected {{
            background-color: #555;
            }}
            """
        else:
            item_style = f"""
            #base_list::item {{
            margin: 0px;
            padding-top: 0px;
            padding-bottom: 0px;
            border: 0px solid {color_border};
            color: {color_font};
            min-width: {self.sz}px;
            min-height: {self.sz}px;
            max-width: {self.sz}px;
            max-height: {self.sz}px;
            }}
            #base_list::item:selected {{
            background-color: {color_bg};
            }}
            """

        # Apply the combined stylesheet
        self.list_widget.setStyleSheet(common_style + item_style)
        
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerItem)
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setUniformItemSizes(True)
        grid_sz = self.sz
        self.list_widget.setGridSize(QSize(grid_sz, grid_sz))
        #icon_sz = int(grid_sz * 0.6)
        #self.list_widget.setIconSize(QSize(icon_sz, icon_sz))
        item_font = QFont(font_families[5])
        self.list_widget.setFont(item_font)
        layout.addWidget(self.header_label)
        layout.addWidget(self.list_widget)

        self.setLayout(layout)

    @classmethod
    def update_grid_size(cls, value):
        cls.sz = value
        if len(cls._instances) > 1:
            inst = cls._instances[0]
            inst.list_widget.setGridSize(QSize(value, value))

    def add_item(self, item):
        self.list_widget.addItem(item)

    def clear(self):
        self.list_widget.clear()