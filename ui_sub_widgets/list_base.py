from PyQt6.QtWidgets import QWidget, QListWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QFontDatabase
import os
import ui_colors

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
    def __init__(self, parent=None, bottom_radius:int = 10, label:str = "Label", sz:int = 74, accept_drops:bool = False, drop_callback=None):
        super().__init__(parent)
        self.sz = sz
        self.label = label
        self.bottom_radius = bottom_radius
        self.drop_callback = drop_callback
        ListBase._instances.append(self)
        
        self.setAcceptDrops(accept_drops)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Static Header Label
        self.header_label = QLabel(label, self)
        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts', 'MuseoModerno-VariableFont_wght.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        self.font = QFont(font_families[0])
        self.font.setPointSizeF(12.5)
        self.header_label.setFont(self.font)
        self.header_label.setObjectName("base_list_header")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Static Header Label + Optional Button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        # Use a container widget for header background
        self.header_container = QWidget(self)
        self.header_container.setObjectName("header_container")
        header_inner_layout = QHBoxLayout(self.header_container)
        header_inner_layout.setContentsMargins(0, 0, 0, 0)
        header_inner_layout.setSpacing(0)

        self.autosettings_spacing = 28 # Button size
        spacer = QSpacerItem(self.autosettings_spacing, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        header_inner_layout.addItem(spacer)
        
        header_inner_layout.addStretch(1)
        header_inner_layout.addWidget(self.header_label, stretch=0)

        font_path_icon = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts', 'MaterialSymbolsRounded-VariableFont_FILL,GRAD,opsz,wght.ttf')
        font_id_icon = QFontDatabase.addApplicationFont(font_path_icon)
        font_families_icon = QFontDatabase.applicationFontFamilies(font_id_icon)
        icon_font = QFont(font_families_icon[0])
        icon_font.setPointSize(self.autosettings_spacing//2)
        self.btn = QPushButton("\uE161" if label=="Auto Settings" else "\uE5CD", self)
        self.btn.setToolTip("Save Settings" if label=="Auto Settings" else "Clear Programs")
        self.btn.setFont(icon_font)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setFixedHeight(self.header_label.sizeHint().height())
        header_inner_layout.addStretch(1)
        header_inner_layout.addWidget(self.btn, stretch=0)

        header_layout.addWidget(self.header_container)
        layout.addLayout(header_layout)

        # List Widget
        self.list_widget = SnapListWidget(self)
        self.list_widget.setObjectName("base_list")
        
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerItem)
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setUniformItemSizes(True)
        grid_sz = self.sz
        self.list_widget.setGridSize(QSize(grid_sz, grid_sz))
        item_font = QFont(font_families[5])
        self.list_widget.setFont(item_font)
        
        layout.addWidget(self.list_widget)

        self.setLayout(layout)
        self.update_style()

    def dragEnterEvent(self, event):
        if self.drop_callback and event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if self.drop_callback and event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if self.drop_callback and event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.acceptProposedAction()
            for url in event.mimeData().urls():
                self.drop_callback(url.toLocalFile())
        else:
            super().dropEvent(event)

    def update_style(self):
        self.header_label.setStyleSheet(f"""
            #base_list_header {{
                background: none;
                border: none;
                color: {ui_colors.FONT};
            }}
        """)
        self.header_container.setStyleSheet(f"""
            QWidget#header_container {{
                background-color: {ui_colors.MAIN_BG};
                border-left: 1px solid {ui_colors.ELEMENT_LIGHT};
                border-top: 1px solid {ui_colors.ELEMENT_LIGHT};
                color: {ui_colors.FONT};
                border-top-left-radius: 10px;
                border-bottom: 1px solid;
                border-bottom-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:.05 {ui_colors.MAIN_BG}, stop:0.5 {ui_colors.FONT}, stop:.95 {ui_colors.MAIN_BG});
            }}
        """)
        self.btn.setStyleSheet(f"QPushButton {{ background: transparent; border: none; color: {ui_colors.LIST_BTN}; padding: 0 8px; }} QPushButton:pressed {{ background: transparent; }}")
        
        common_style = f"""
            #base_list {{
            outline: 0;
            background-color: {ui_colors.MAIN_BG};
            border-left: 1px solid {ui_colors.ELEMENT_LIGHT};
            border-bottom: 1px solid {ui_colors.ELEMENT_LIGHT};
            border-bottom-left-radius: {self.bottom_radius}px;
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
            background: {ui_colors.ELEMENT_LIGHT};
            min-height: 20px;
            border-radius: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
            background: {ui_colors.SLIDER_BAR};
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            }}
        """

        if self.label == "Programs":
            item_style = f"""
            #base_list::item {{
            margin: 2.5px;
            padding-top: 10px;
            padding-bottom: 10px;
            padding-left: 5px;
            padding-right: 5px;
            border-radius: 15px;
            background-color: {ui_colors.MAIN_BG};
            border: 1px solid {ui_colors.ELEMENT_LIGHT};
            color: {ui_colors.FONT};
            min-width: {self.sz}px;
            min-height: {self.sz}px;
            max-width: {self.sz}px;
            max-height: {self.sz}px;
            }}
            #base_list::item:selected {{
            background-color: {ui_colors.ITEM_SELECTED_BG};
            }}
            """
        else:
            item_style = f"""
            #base_list::item {{
            margin: 0px;
            padding-top: 0px;
            padding-bottom: 0px;
            border: 0px solid {ui_colors.ELEMENT_LIGHT};
            color: {ui_colors.FONT};
            min-width: {self.sz}px;
            min-height: {self.sz}px;
            max-width: {self.sz}px;
            max-height: {self.sz}px;
            }}
            #base_list::item:selected {{
            background-color: {ui_colors.MAIN_BG};
            }}
            """
        self.list_widget.setStyleSheet(common_style + item_style)

    def add_item(self, item):
        self.list_widget.addItem(item)

    def clear(self):
        self.list_widget.clear()
