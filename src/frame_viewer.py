from tkinter import PanedWindow , Button , Frame


class FrameViewer:
    def __init__(self, root , cameras_amount):
        self.root = root
        self.cameras_amount = cameras_amount

        self.main_window = PanedWindow(self.root , orient="horizontal")

        self.right_panel = Frame(self.main_window , bg="#f0f0f0")
        self.frame_panel = Frame(self.main_window , )
        self.right_panel.pack(side="right")
        self.frame_panel.pack(side="left")
        self.main_window.add(self.right_panel , stretch = "never")
        self.main_window.add(self.frame_panel, stretch = "always")

        button_frame = self.__init_button_frame()

        button_frame.pack(padx=10 , pady=10)


    def __init_button_frame(self):
        button_frame = Frame(self.right_panel)
        self.previous_button = Button(button_frame , text="◄" , bg="green" , font=("arial" , 16) , justify="center")
        self.next_button = Button(button_frame , text="►" , bg="green" , font=("arial" , 16), justify="center")

        self.previous_button.grid(row=0 , column=0, padx=5 , pady=5)
        self.next_button.grid(row=0 , column=1, padx=5 , pady=5)

        self.video_backward_button = Button(button_frame, text="◄◄" , bg="green" , font=("arial" , 16) , justify="center")
        self.video_forward_button = Button(button_frame, text="►►" , bg="green" , font=("arial" , 16), justify="center" )

        self.video_backward_button.grid(row=1 , column=0, padx=5 , pady=5)
        self.video_forward_button.grid(row=1 , column=1 , padx=5 , pady=5)

        return button_frame
        