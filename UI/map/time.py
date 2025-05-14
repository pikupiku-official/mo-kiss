import tkinter as tk
from datetime import datetime

class Time:
    def __init__(self, parent):
        self.parent = parent
        self.label = tk.Label(parent, text="", font=("Arial", 24), bg="#D8D8D8")
        self.label.place(relx=0.8, rely=0.1, anchor="center")
        
        # Update time display
        self.update_time()
        
    def update_time(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.label.config(text=current_time)
        # Update every second
        self.parent.after(1000, self.update_time)
        
    def show(self):
        self.label.lift()
        
    def hide(self):
        self.label.lower() 