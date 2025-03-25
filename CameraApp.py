from tkinter import Tk
from src.gui import GUI

class CameraApp:
    def __init__(self):
        self.root = Tk()
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}")
        self.root.title("Camera Control App")
        
        self.gui = GUI(root=self.root)
        
        self.root.bind('<Escape>' , lambda e: self.on_closing())
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.on_closing())
        
    def on_closing(self):
        self.gui.on_closing()
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    camera_app = CameraApp()
    camera_app.run()
    