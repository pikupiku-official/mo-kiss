import tkinter as tk
from datetime import datetime

class Date:
    def __init__(self, parent):
        self.parent = parent
        self.label = tk.Label(parent, text="", font=("Arial", 24), bg="#D8D8D8")
        self.label.place(relx=0.5, rely=0.1, anchor="center")
        
        # Update date display
        self.update_date()
        
    def update_date(self):
        current_date = datetime.now().strftime("%Y年%m月%d日")
        self.label.config(text=current_date)
        
    def show(self):
        self.label.lift()
        
    def hide(self):
        self.label.lower() 