import tkinter as tk
from datetime import datetime

class Calendar:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent, bg="#D8D8D8")
        self.frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Create calendar grid
        self.create_grid()
        
    def create_grid(self):
        # Create 7x6 grid for calendar
        for i in range(7):
            for j in range(6):
                cell = tk.Frame(self.frame, width=100, height=100, bg="white")
                cell.grid(row=j, column=i, padx=2, pady=2)
                
                # Add day number
                day_num = j * 7 + i + 1
                if day_num <= 31:  # Only show valid days
                    label = tk.Label(cell, text=str(day_num), bg="white")
                    label.place(relx=0.5, rely=0.5, anchor="center")
    
    def show(self):
        self.frame.lift()
        
    def hide(self):
        self.frame.lower() 