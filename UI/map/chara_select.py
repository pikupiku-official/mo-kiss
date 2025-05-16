import tkinter as tk

class CharaSelect:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent, bg="#D8D8D8")
        self.frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Create character selection squares
        self.create_squares()
        
    def create_squares(self):
        # Create 6 character selection squares
        for i in range(6):
            square = tk.Frame(self.frame, width=100, height=100, bg="white")
            square.grid(row=0, column=i, padx=10, pady=10)
            
            # Add character number
            label = tk.Label(square, text=f"Character {i+1}", bg="white")
            label.place(relx=0.5, rely=0.5, anchor="center")
            
            # Add click event
            square.bind("<Button-1>", lambda e, num=i+1: self.select_character(num))
    
    def select_character(self, number):
        print(f"Selected character {number}")
        # Add character selection logic here
    
    def show(self):
        self.frame.lift()
        
    def hide(self):
        self.frame.lower() 