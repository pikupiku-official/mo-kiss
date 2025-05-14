import tkinter as tk
from chara_select import CharaSelect
from title import Title
from date import Date
from calendar import Calendar
from time_squares import TimeSquares

# メインウィンドウの作成
root = tk.Tk()
root.title("Calendar App")

# ウィンドウのサイズを設定      
window_width = 1920
window_height = 1080
root.geometry(f"{window_width}x{window_height}")

# 背景色を設定
root.configure(bg="#D8D8D8")  # さらに濃いグレー

# 各要素の作成
date = Date(root)
calendar = Calendar(root)
time_squares = TimeSquares(root)
title = Title(root)
chara_select = CharaSelect(root)

# タイトル画面を表示
title.show()

# メインループの開始
root.mainloop()
