import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

class TextWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("text_UI")
        self.setFixedSize(1920, 1080)
        
        # 性別情報の読み込み
        gender_file_path = os.path.join(os.path.dirname(__file__), "character_gender.json")
        try:
            with open(gender_file_path, 'r', encoding='utf-8') as f:
                self.gender_data = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load gender data: {e}")
            self.gender_data = {}
        
        # フォントの設定
        bold_font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "fonts", "MPLUSRounded1c-Bold.ttf")
        medium_font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "fonts", "MPLUSRounded1c-Regular.ttf")
        
        # Boldフォントの読み込み
        bold_font_id = QFontDatabase.addApplicationFont(bold_font_path)
        # Mediumフォントの読み込み
        medium_font_id = QFontDatabase.addApplicationFont(medium_font_path)
        
        if bold_font_id != -1 and medium_font_id != -1:
            bold_font_family = QFontDatabase.applicationFontFamilies(bold_font_id)[0]
            medium_font_family = QFontDatabase.applicationFontFamilies(medium_font_id)[0]
            
            # 人物名用のフォント（Bold）
            self.name_font = QFont(bold_font_family, 48)
            
            # セリフ用のフォント（Medium）
            self.speech_font = QFont(medium_font_family, 48)
        else:
            print("Warning: Rounded Mplus font not found, using system font")
            # 人物名用のフォント（Bold）
            self.name_font = QFont("Arial", 48)
            self.name_font.setWeight(700)  # Bold
            
            # セリフ用のフォント（Medium）
            self.speech_font = QFont("Arial", 48)
            self.speech_font.setWeight(500)  # Medium
        
        # テキストエディタの位置とサイズを設定
        # text-box.pngのサイズに合わせて設定（1632x352）
        text_box_width = 1632
        text_box_height = 352
        
        # 人物名用のテキストボックス幅（全角4文字分）
        name_box_width = 48 * 4
        # セリフ用のテキストボックス幅（全角28文字分）
        speech_box_width = 48 * 28
        
        x_pos = (1920 - text_box_width) // 2 + 48  # 48px右に移動
        
        # 1つ目の人物名テキストエディタの設定
        self.name_edit1 = QTextEdit(self)
        self.name_edit1.setFont(self.name_font)
        self.name_edit1.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0);
                color: #FFFFFF;
                border: none;
                padding: 20px;
                white-space: nowrap;
                font-weight: 700;
            }
        """)
        self.name_edit1.setReadOnly(True)
        self.name_edit1.setLineWrapMode(QTextEdit.NoWrap)  # 改行を無効化
        
        # 1つ目のセリフテキストエディタの設定
        self.speech_edit1 = QTextEdit(self)
        self.speech_edit1.setFont(self.speech_font)
        self.speech_edit1.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0);
                color: #FFFFFF;
                border: none;
                padding: 20px;
                line-height: 1.5;
                font-weight: 500;
            }
        """)
        self.speech_edit1.setReadOnly(True)
        
        # 2つ目の人物名テキストエディタの設定
        self.name_edit2 = QTextEdit(self)
        self.name_edit2.setFont(self.name_font)
        self.name_edit2.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0);
                color: #FFFFFF;
                border: none;
                padding: 20px;
                white-space: nowrap;
                font-weight: 700;
            }
        """)
        self.name_edit2.setReadOnly(True)
        self.name_edit2.setLineWrapMode(QTextEdit.NoWrap)  # 改行を無効化
        
        # 2つ目のセリフテキストエディタの設定
        self.speech_edit2 = QTextEdit(self)
        self.speech_edit2.setFont(self.speech_font)
        self.speech_edit2.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0);
                color: #FFFFFF;
                border: none;
                padding: 20px;
                line-height: 1.5;
                font-weight: 500;
            }
        """)
        self.speech_edit2.setReadOnly(True)
        
        # 1つ目のテキストエディタの位置
        y_pos1 = 1080 - text_box_height - 96 + 62  # 48px下に移動
    
        self.name_edit1.setGeometry(x_pos, y_pos1, name_box_width, text_box_height)
        # セリフのテキストボックスを人物名の右端から24px右に配置
        self.speech_edit1.setGeometry(x_pos + name_box_width, y_pos1, speech_box_width, text_box_height)
        
        # 2つ目のテキストエディタの位置（1つ目の56px下）
        y_pos2 = y_pos1 + 80
        self.name_edit2.setGeometry(x_pos, y_pos2, name_box_width, text_box_height)
        # セリフのテキストボックスを人物名の右端から24px右に配置
        self.speech_edit2.setGeometry(x_pos + name_box_width, y_pos2, speech_box_width, text_box_height)
        
        # テキストエディタを最前面に表示
        self.name_edit1.raise_()
        self.speech_edit1.raise_()
        self.name_edit2.raise_()
        self.speech_edit2.raise_()
        
        # ウィンドウを画面中央に配置
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2,
                 (screen.height() - self.height()) // 2)
        
        # テスト用のテキストを表示
        self.set_name1("桃　子")
        self.set_speech1("「春はあけぼの。」")
        self.set_name2("ますた")
        self.set_speech2("「やうやう白くなりゆく、山ぎは少し明りて、紫だちたる雲の細くたなびきたる。」")
    
    def set_name1(self, text):
        """1つ目の人物名を設定するメソッド"""
        self.name_edit1.setText(text)
        self.name_edit1.raise_()
        self._update_text_color(1, text)
    
    def set_speech1(self, text):
        """1つ目のセリフを設定するメソッド"""
        # 27文字ごとに改行を挿入
        formatted_text = self._format_speech(text)
        self.speech_edit1.setText(formatted_text)
        self.speech_edit1.raise_()
    
    def set_name2(self, text):
        """2つ目の人物名を設定するメソッド"""
        self.name_edit2.setText(text)
        self.name_edit2.raise_()
        self._update_text_color(2, text)
    
    def set_speech2(self, text):
        """2つ目のセリフを設定するメソッド"""
        # 27文字ごとに改行を挿入
        formatted_text = self._format_speech(text)
        self.speech_edit2.setText(formatted_text)
        self.speech_edit2.raise_()
    
    def _update_text_color(self, index, name):
        """性別に応じてテキストの色を更新するメソッド"""
        color = "#FFAFE3" if self.gender_data.get(name) == "female" else "#FFFFFF"
        if index == 1:
            self.name_edit1.setStyleSheet(f"""
                QTextEdit {{
                    background-color: rgba(0, 0, 0, 0);
                    color: {color};
                    border: none;
                    padding: 20px;
                    white-space: nowrap;
                    font-weight: 700;
                }}
            """)
            self.speech_edit1.setStyleSheet(f"""
                QTextEdit {{
                    background-color: rgba(0, 0, 0, 0);
                    color: {color};
                    border: none;
                    padding: 20px;
                    line-height: 1.5;
                    font-weight: 500;
                }}
            """)
        else:
            self.name_edit2.setStyleSheet(f"""
                QTextEdit {{
                    background-color: rgba(0, 0, 0, 0);
                    color: {color};
                    border: none;
                    padding: 20px;
                    white-space: nowrap;
                    font-weight: 700;
                }}
            """)
            self.speech_edit2.setStyleSheet(f"""
                QTextEdit {{
                    background-color: rgba(0, 0, 0, 0);
                    color: {color};
                    border: none;
                    padding: 20px;
                    line-height: 1.5;
                    font-weight: 500;
                }}
            """)
    
    def _format_speech(self, text):
        """セリフを27文字ごとに改行するメソッド"""
        # 全角文字を1文字、半角文字を0.5文字としてカウント
        result = []
        current_line = ""
        char_count = 0
        
        for char in text:
            # 全角文字かどうかを判定（簡易的な判定）
            is_full_width = ord(char) > 0x7F
            char_width = 1 if is_full_width else 0.5
            
            if char_count + char_width > 27:
                result.append(current_line)
                current_line = "　" + char  # 改行後の行頭に全角空白を追加
                char_count = char_width + 1  # 全角空白分もカウント
            else:
                current_line += char
                char_count += char_width
        
        if current_line:
            result.append(current_line)
        
        return "\n".join(result)
    
    def append_speech1(self, text):
        """1つ目のセリフを追加するメソッド"""
        formatted_text = self._format_speech(text)
        self.speech_edit1.append(formatted_text)
        self.speech_edit1.raise_()
        print(f"1つ目のセリフを追加: {text}")
    
    def append_speech2(self, text):
        """2つ目のセリフを追加するメソッド"""
        formatted_text = self._format_speech(text)
        self.speech_edit2.append(formatted_text)
        self.speech_edit2.raise_()
        print(f"2つ目のセリフを追加: {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextWindow()
    window.show()
    sys.exit(app.exec_())
