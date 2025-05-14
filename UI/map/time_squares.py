import tkinter as tk

class TimeSquares:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent, bg="#D8D8D8")
        self.frame.place(relx=0.8, rely=0.5, anchor="center")
        
        # Create time squares
        self.create_squares()
        
    def create_squares(self):
        # Create 6 squares for time display
        for i in range(6):
            square = tk.Frame(self.frame, width=80, height=80, bg="white")
            square.grid(row=i, column=0, padx=5, pady=5)
            
            # Add time label
            time = f"{i+1}:00"
            label = tk.Label(square, text=time, bg="white")
            label.place(relx=0.5, rely=0.5, anchor="center")
    
    def show(self):
        self.frame.lift()
        
    def hide(self):
        self.frame.lower() 