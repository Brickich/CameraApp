from tkinter import Tk
from src.gui import GUI



class CameraApp:
    def __init__(self):
        self.root = Tk()
        self.root.geometry(f"{self.root.winfo_screenwidth()-400}x{self.root.winfo_screenheight()-600}")
        self.root.title("Camera Control App")   
        self.gui = GUI(root=self.root)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    camera_app = CameraApp()
    camera_app.run()
    