from tkinter import Tk
from src.gui import GUI



class CameraApp:
    def __init__(self):
        self.root = Tk()
        self.root.geometry(f"{int(self.root.winfo_screenwidth()/2)}x{int(self.root.winfo_screenheight()/2)}")
        self.root.title("Camera Control App")   
        self.gui = GUI(root=self.root)
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)
        
    def run(self):
        self.root.mainloop()
    
    def destroy(self):
        self.gui.camera.close()
        self.root.destroy()
        
if __name__ == "__main__":
    camera_app = CameraApp()

    camera_app.run()
    