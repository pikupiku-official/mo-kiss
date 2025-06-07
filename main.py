import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from text import TextWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ウィンドウの設定
        self.setWindowTitle("Main Window")
        self.setFixedSize(1920, 1080)
        
        # 背景画像の設定（最背面）
        background_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     "images", "test_1.png")
        background_label = QLabel(self)
        background_pixmap = QPixmap(background_path)
        # アスペクト比を維持しながら1920x1080にスケーリング
        scaled_pixmap = background_pixmap.scaled(1920, 1080, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        background_label.setPixmap(scaled_pixmap)
        background_label.setGeometry(0, 0, 1920, 1080)
        background_label.lower()  # 最背面に配置
        
        # テキストボックス画像の設定（中間層）
        text_box_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   "images", "ui.text-box.png")
        text_box_label = QLabel(self)
        text_box_pixmap = QPixmap(text_box_path)
        text_box_label.setPixmap(text_box_pixmap)
        # テキストボックスの位置を設定（画面下部中央）
        text_box_width = text_box_pixmap.width()
        text_box_height = text_box_pixmap.height()
        x_pos = (1920 - text_box_width) // 2
        y_pos = 1080 - text_box_height - 96  # 96px上に配置
        text_box_label.setGeometry(x_pos, y_pos, text_box_width, text_box_height)
        
        # テキストウィンドウの設定（テキストボックスの上）
        self.text_window = TextWindow()
        self.text_window.setParent(self)
        self.text_window.show()
        
        # AUTOボタンの設定（最前面）
        auto_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "images", "ui.auto.png")
        self.auto_button = QPushButton(self)
        auto_pixmap = QPixmap(auto_path)
        self.auto_button.setIcon(QIcon(auto_pixmap))
        self.auto_button.setIconSize(auto_pixmap.size())
        # AUTOボタンの位置を設定（テキストボックスの右端から20px左、100px上）
        auto_width = auto_pixmap.width()
        auto_height = auto_pixmap.height()
        auto_x = x_pos + text_box_width - 200 - 58 -5  # 20px左に移動
        auto_y = y_pos + (text_box_height - auto_height) // 2 - 138 # 100px上に移動
        self.auto_button.setGeometry(auto_x, auto_y, auto_width, auto_height)
        # ボタンのスタイル設定
        self.auto_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px;
                opacity: 0.01;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.auto_button.clicked.connect(self.toggle_auto)
        
        # SKIPボタンの設定（最前面）
        skip_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "images", "ui.skip.png")
        self.skip_button = QPushButton(self)
        skip_pixmap = QPixmap(skip_path)
        self.skip_button.setIcon(QIcon(skip_pixmap))
        self.skip_button.setIconSize(skip_pixmap.size())
        # SKIPボタンの位置を設定（AUTOボタンの右隣、100px上）
        skip_width = skip_pixmap.width()
        skip_height = skip_pixmap.height()
        skip_x = auto_x + 138 + 4
        skip_y = auto_y  # AUTOボタンと同じ高さ
        self.skip_button.setGeometry(skip_x, skip_y, skip_width, skip_height)
        # ボタンのスタイル設定
        self.skip_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px;
                opacity: 0.01;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.skip_button.clicked.connect(self.toggle_skip)
        
        # 表示順序の設定
        # 1. 背景画像（最背面）
        background_label.lower()
        
        # 2. テキストボックス（中間層）
        text_box_label.raise_()
        
        # 3. テキストウィンドウ（テキストボックスの上）
        self.text_window.raise_()
        
        # 4. AUTOボタンとSKIPボタン（最前面）
        self.auto_button.raise_()
        self.skip_button.raise_()
        
        # ウィンドウを画面中央に配置
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2,
                 (screen.height() - self.height()) // 2)
    
    def toggle_auto(self):
        """AUTOモードの切り替え"""
        self.text_window.toggle_auto()
    
    def toggle_skip(self):
        """SKIPモードの切り替え"""
        self.text_window.toggle_skip()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

