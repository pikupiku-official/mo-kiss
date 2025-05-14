import tkinter as tk

class Title:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent, bg="#D8D8D8")
        self.frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Create title
        self.title_label = tk.Label(
            self.frame,
            text="Calendar App",
            font=("Arial", 36, "bold"),
            bg="#D8D8D8"
        )
        self.title_label.pack(pady=20)
        
        # Create start button
        self.start_button = tk.Button(
            self.frame,
            text="Start",
            font=("Arial", 24),
            command=self.start_app
        )
        self.start_button.pack(pady=20)
        
    def start_app(self):
        self.hide()
        # Add logic to show main app screen
        
    def show(self):
        self.frame.lift()
        
    def hide(self):
        self.frame.lower() 