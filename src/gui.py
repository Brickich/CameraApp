import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
from .video_editor import VideoEditor
from .camera import Camera
from gxipy import GxTriggerSourceEntry


class ImageViewContainer:

    def __init__(
        self,
        root: tk.Tk,
        video_editor:VideoEditor,
        styles: dict,
        camera:Camera,
        position_and_size={
            "relx": 0.0,
            "rely": 0.1,
            "x": 0,
            "y": 0,
            "relwidth": 1.0,
            "relheight": 0.9,
        },
    ):
        self.root = root
        self.video_editor = video_editor
        self.camera = camera

        self.styles = styles
        self.position_and_size = position_and_size
        self.init_image_canvas()

    def init_image_canvas(self):
        self.image_frame = tk.Label(self.root , self.styles)
        self.image_frame.place(self.position_and_size)



        self.video_editor_image = ImageTk.PhotoImage(Image.open("assets/video_editor.png").resize((25,25)))
        self.video_editor_button = tk.Button(self.root , image=self.video_editor_image)

        self.video_editor_button.place(
            relx=1.0,
            rely=1.0,
            x=-self.video_editor_button.winfo_reqwidth() - 5,
            y=-self.video_editor_button.winfo_reqheight() - 5,
        )

        self.current_fps_label = tk.Label(self.root , text=f"Current FPS : {self.camera.CurrentFrameRate.get()}" , font=("Arial" , 10))
        self.current_fps_label.place(relx=0.5 , rely=1.0 , y=-self.current_fps_label.winfo_reqheight() , anchor="center")





class ControlPanelContainer():

    def __init__(
        self,
        root: tk.Tk,
        camera: Camera,
        styles: dict,
        image_view: ImageViewContainer,
        position_and_size={
            "relx": 0.0,
            "rely": 0.0,
            "x": 0,
            "y": 0,
            "relwidth": 1.0,
            "relheight": 0.1,
        },
    ):
        self.root = root
        self.camera = camera
        self.image_view = image_view
        self.styles = styles
        self.position_and_size = position_and_size

        self.button_size = self.styles.get("button_size" , (25,25))
        self.camera_settings_window_enabled = False
        self.play_pause_index =0

        self.SOFTWARE_trigger_enabled = True
        self.LINE0_trigger_enabled = False
        self.LINE2_trigger_enabled = False

        self.settings_buttons:list[tk.Button] = []

        self.init_control_panel()
        self.init_camera_settings_window()

    def init_control_panel(self):
        image_paths = {
            "play_pause": ["assets/play_button.png", "assets/pause_button.png"],
            "white_balance": "assets/white_balance.png",
            "crosshair": "assets/crosshair.png",
            "flip_h": "assets/flip_h.png",
            "flip_v": "assets/flip_v.png",
            "rotate_right": "assets/rotate_to_right.png",
            "rotate_left": "assets/rotate_to_left.png",
            "settings": "assets/settings.png",
        }
        self.play_pause_images = [
            ImageTk.PhotoImage(Image.open(img).resize(self.button_size))
            for img in image_paths["play_pause"]
        ]

        self.wbalance_image = ImageTk.PhotoImage(
            Image.open(image_paths["white_balance"]).resize(self.button_size)
        )
        self.crosshair_image = ImageTk.PhotoImage(
            Image.open(image_paths["crosshair"]).resize(self.button_size)
        )
        self.flip_h_image = ImageTk.PhotoImage(
            Image.open(image_paths["flip_h"]).resize(self.button_size)
        )
        self.flip_v_image = ImageTk.PhotoImage(
            Image.open(image_paths["flip_v"]).resize(self.button_size)
        )
        self.rotate_right_image = ImageTk.PhotoImage(
            Image.open(image_paths["rotate_right"]).resize(self.button_size)
        )
        self.rotate_left_image = ImageTk.PhotoImage(
            Image.open(image_paths["rotate_left"]).resize(self.button_size)
        )
        self.settings_image = ImageTk.PhotoImage(
            Image.open(image_paths["settings"]).resize(self.button_size)
        )

        self.control_panel_frame = tk.Frame(self.root)
        self.control_panel_frame.place(self.position_and_size)
        self.control_panel_placing = {"sticky": "ew", "pady": 10, "padx": 5}

        self.play_pause_button = tk.Button(
            self.control_panel_frame,
            image=self.play_pause_images[self.play_pause_index],)
        self.wbalance_button = tk.Button(
            self.control_panel_frame,
            image=self.wbalance_image,
            command=self.camera.switch_white_balance,
        )
        self.crosshair_button = tk.Button(
            self.control_panel_frame,
            image=self.crosshair_image,
            command=self.camera.switch_crosshair,
        )
        self.flip_h_button = tk.Button(
            self.control_panel_frame, image=self.flip_h_image, command=self.camera.flip_image_horizontally
        )
        self.flip_v_button = tk.Button(
            self.control_panel_frame, image=self.flip_v_image, command=self.camera.flip_image_vertically
        )
        self.rotate_right_button = tk.Button(
            self.control_panel_frame,
            image=self.rotate_right_image,
            command=self.camera.rotate_image_right,
        )
        self.rotate_left_button = tk.Button(
            self.control_panel_frame, image=self.rotate_left_image, command=self.camera.rotate_image_left
        )
        for i, widget in enumerate(
            [
                self.play_pause_button,
                self.wbalance_button,
                self.crosshair_button,
                self.flip_h_button,
                self.flip_v_button,
                self.rotate_right_button,
                self.rotate_left_button,
            ]
        ):
            widget.grid(row=0, column=i, **self.control_panel_placing)

        self.trigger_button = tk.Button(self.control_panel_frame, command=self.switch_trigger, text= "SOFT", font=("Arial" , 14))
        self.trigger_button.place(relx=0.5 , rely=0.5 , anchor="center")

        self.preview_button = tk.Button(self.control_panel_frame , command = self.switch_to_preview , font=("Arial" , 12), text="Preview")
        self.preview_button.place(relx=0.7 , rely=0.5 , anchor="center")
        self.settings_button = tk.Button(
            self.control_panel_frame,
            image=self.settings_image,
            font=("Arial", 12),
            command=self.switch_camera_settings_window,
        )

        self.settings_button.place(
            relx=1.0,
            rely=0.5,
            x=-self.settings_button.winfo_reqwidth() - 15,
            anchor="center",
        )

    def init_camera_settings_window(self):
        self.camera_settings_frame = tk.LabelFrame(
            self.root,
            bd=2,
            relief=tk.SOLID,
            bg="#88bdf2",
            padx=2.5,
            pady=2.5,
            font=("Arial", 10),
        )
        self.button_size = (30, 30)
        self.save_image = ImageTk.PhotoImage(
            Image.open("assets/save.png").resize(self.button_size)
        )

        self.SOFTWARE_trigger_button = tk.Button(
            self.camera_settings_frame,
            text="SOFTWARE",
            state="active",
            bg="green",
            activebackground="green",
            fg="white",
            activeforeground="white",
            command=lambda: self.switch_trigger_button(
                self.SOFTWARE_trigger_button, "SOFT"
            ),
            font=("Verdana", 12)
        )
        self.LINE0_trigger_button = tk.Button(
            self.camera_settings_frame,
            text="LINE0",
            state="normal",
            command=lambda: self.switch_trigger_button(
                self.LINE0_trigger_button, "LINE0"
            ),
            font=("Verdana", 12)
        )
        self.LINE2_trigger_button = tk.Button(
            self.camera_settings_frame,
            text="LINE2",
            state="normal",
            command=lambda: self.switch_trigger_button(
                self.LINE2_trigger_button, "LINE2"
            ),
            font=("Verdana", 12)
        )

        self.SOFTWARE_trigger_button.grid(row=0, column=0, sticky="ew")
        self.LINE0_trigger_button.grid(row=0, column=1,sticky="ew")
        self.LINE2_trigger_button.grid(row=0, column=2,sticky="ew")

        self.trigger_buttons = [
            self.SOFTWARE_trigger_button,
            self.LINE0_trigger_button,
            self.LINE2_trigger_button
        ]

        self.colored_button = tk.Button(
            self.camera_settings_frame,
            text="Colored",
            state="normal",
            command=lambda: self.switch_color("COLOR"),
            width=10,
            font=("Verdana" , 12)
        )
        self.mono_button = tk.Button(
            self.camera_settings_frame,
            text="Mono",
            state="normal",
            command=lambda: self.switch_color("MONO"),
            width=10,
            font=("Verdana" , 12)
        )
        if self.camera.isColored:
            self.colored_button.config(bg="green", activebackground="green", state="active", fg="white" , activeforeground="white")

            if not self.camera.SupportMonoFormat:
                self.mono_button.config(state="disabled")

        else:
            self.mono_button.config(bg="green", activebackground="green", state="active", fg="white" , activeforeground="white")

        self.colored_button.grid(row=1, column=0, columnspan=2)
        self.mono_button.grid(row=1, column=1, columnspan=2)
        self.init_sliders(self.camera_settings_frame)
        self.sliders_frame.grid(row=2, sticky="ew", column=0, columnspan=3)

        self.basename_entry = tk.Entry(self.camera_settings_frame , width=30)
        self.basename_entry.grid(row=3 , columnspan=2)
        self.apply_settings_button = tk.Button(
            self.camera_settings_frame,
            image=self.save_image,
            command=self.apply_settings_button_clicked,
        ).grid(row=3, column=2)
        self.camera_settings_frame.update_idletasks()
        self.camera_settings_frame.place_forget()

    def switch_trigger(self):
        basename = self.basename_entry.get()
        if self.SOFTWARE_trigger_enabled:
            self.camera.switch_trigger(self.trigger_button , GxTriggerSourceEntry.SOFTWARE , basename)
        elif self.LINE0_trigger_enabled:
            self.camera.switch_trigger(self.trigger_button , GxTriggerSourceEntry.LINE0 , basename)
        elif self.LINE2_trigger_enabled:
            self.camera.switch_trigger(self.trigger_button, GxTriggerSourceEntry.LINE2 , basename)

    def switch_trigger_button(self, button:tk.Button, command:str):
        for btn in self.trigger_buttons:
            btn.config(bg="SystemButtonFace", activebackground="SystemButtonFace", state="normal", fg="black", activeforeground="black") 

        button.config(bg="green",activebackground="green", state="active", fg="white", activeforeground="white")
        self.trigger_button.config(text=command.upper())
        command_states = {
            "soft": (True, False, False, False),
            "line0": (False, True, False, False),
            "line2": (False, False, True, False),
            "external": (False, False, False, True) 
        }
        command=command.lower()
        if command in command_states:
            s , l0 , l1 , ext = command_states[command]
            self.SOFTWARE_trigger_enabled = s
            self.LINE0_trigger_enabled = l0
            self.LINE2_trigger_enabled = l1

    def switch_to_preview(self):
        self.camera.preview_preset = self.camera.default_preset
        self.camera.preview_preset['exposure_time'] = float(40000)

        self.camera.apply_settings_clicked(preview_preset=True)

    def init_sliders(self, frame):
        self.sliders_frame = tk.LabelFrame(
            frame,
            bd=2,
            relief="ridge",
            font=("Segoe UI", 11, "bold"),
            foreground="#2E3440",
            background="#e3f0fc",
            highlightbackground="#8fa8c2",
            highlightthickness=1,
        )
        width_range = self.camera.Width.get_range()
        height_range = self.camera.Height.get_range()
        exposure_time_range = self.camera.ExposureTime.get_range()
        if self.camera.type == "MER2":
            exposure_time_range['min'] = 1.0
        exposure_time_range["inc"]=1.0
        fps_range = self.camera.FrameRate.get_range()
        fps_range['min'] = 1.0
        fps_range['inc'] = 1.0
        gain_range = self.camera.Gain.get_range()
        gain_range['inc'] = 0.1
        offsetX_range = self.camera.cam.OffsetX.get_range()
        offsetY_range = self.camera.cam.OffsetY.get_range()

        self.width_slider, self.width_entry= add_slider_with_entry(
            self.sliders_frame,
            label_text="Width",
            slider_range=width_range,
            row=1,
            initial_value=self.camera.Width.get(),
        )
        self.height_slider, self.height_entry= add_slider_with_entry(
            self.sliders_frame,
            "Height",
            slider_range=height_range,
            row=2,
            initial_value=self.camera.Height.get(),
        )
        self.exposure_time_slider, self.exposure_time_entry = add_slider_with_entry(
            self.sliders_frame,
            "Exposure Time, μs",
            slider_range=exposure_time_range,
            row=3,
            initial_value=self.camera.ExposureTime.get(),
        )
        self.fps_slider, self.fps_entry = add_slider_with_entry(
            self.sliders_frame,
            "FrameRate",
            slider_range=fps_range,
            row=4,
            initial_value=self.camera.FrameRate.get(),
        )
        self.gain_slider, self.gain_entry= add_slider_with_entry(
            self.sliders_frame,
            "Gain, dB",
            slider_range=gain_range,
            row=5,
            initial_value=self.camera.Gain.get(),
        )

        trigger_delay_range = self.camera.TriggerDelay.get_range()
        trigger_delay_range['inc'] = 0.01
        self.trigger_delay_slider,self.trigger_delay_entry = add_slider_with_entry(
            self.sliders_frame,
            "Trigger Delay, μs",
            slider_range=trigger_delay_range,
            row=6,
            initial_value=self.camera.TriggerDelay.get()
        )

        quantity_of_frames_range = {"min" :10 , "max" : 1000, "inc" : 1}
        self.quantity_of_frames_slider, self.quantity_of_frames_entry = (
            add_slider_with_entry(
                self.sliders_frame,
                "NumberOfFrames",
                slider_range=quantity_of_frames_range,
                row=8,
                initial_value=self.camera.quantity_of_frames,
            )
        )
        self.offsetX_slider , self.offsetX_entry= add_slider_with_entry(
            self.sliders_frame,
            "OffsetX",
            slider_range= offsetX_range,
            row= 9 , 
            initial_value= self.camera.cam.OffsetX.get(),
        )
        self.offsetY_slider , self.offsetY_entry = add_slider_with_entry(
            self.sliders_frame , 
            "OffsetY",
            slider_range= offsetY_range ,
            row = 10 ,
            initial_value=self.camera.cam.OffsetY.get()
        )

    def switch_camera_settings_window(self):
        self.camera_settings_window_enabled = not self.camera_settings_window_enabled
        if self.camera_settings_window_enabled:
            frame_width = self.camera_settings_frame.winfo_reqwidth()
            frame_height = self.camera_settings_frame.winfo_reqheight()
            self.camera_settings_frame.place(
                x=-frame_width - 5,
                relx=1.0,
                y=self.settings_button.winfo_y()
                + self.settings_button.winfo_reqheight()
                + 15,
            )
            self.camera_settings_frame.place(
                x=-frame_width - 5,
                relx=1.0,
                y=self.settings_button.winfo_y()
                + self.settings_button.winfo_reqheight()
                + 15,
            )
        else:
            self.camera_settings_frame.place_forget()

    def get_preset_from_sliders(self) -> dict[str, float | int]:
        preset = {
            "width": int(self.width_entry.get()),
            "height": int(self.height_entry.get()),
            "exposure_time": float(self.exposure_time_entry.get()),
            "fps": float(self.fps_entry.get()),
            "gain": float(self.gain_entry.get()),
            "trigger_delay" : float(self.trigger_delay_entry.get()),
            "quantity_of_frames" : int(self.quantity_of_frames_entry.get()),
            "offsetX" : int(self.offsetX_entry.get()),
            "offsetY" : int(self.offsetY_entry.get()),
        }
        return preset

    def apply_settings_button_clicked(self):
        if self.camera.is_triggered:
            messagebox.showinfo("Info" , "Can't change settings\nCamera in trigger mode")
            return
        preset = self.get_preset_from_sliders()
        default_preset = preset.copy()
        default_preset['fps'] = 24.0
        trigger_preset = preset

        self.camera.set_default_preset(default_preset)
        self.camera.set_trigger_preset(trigger_preset)
        self.camera.apply_settings_clicked()

    def play_pause_button_clicked(self):
        self.play_pause_index = 1 - self.play_pause_index
        self.play_pause_button.config(image=self.play_pause_images[self.play_pause_index])
        self.play_pause_button.image = self.play_pause_images[self.play_pause_index]



    def switch_color(self, command:str):
        if command == "COLOR":
            if self.camera.SupportMonoFormat:
                self.mono_button.config(
                    bg="SystemButtonFace",
                    activebackground="SystemButtonFace",
                    state="normal",
                    fg="black",
                    activeforeground="black",
                )

            self.colored_button.config(
                bg="green",
                activebackground="green",
                state="active",
                fg="white",
                activeforeground="white",
            )
            self.camera.isColored = True
        elif command == "MONO":
            if self.camera.SupportColorFormat:
                self.colored_button.config(
                    bg="SystemButtonFace",
                    activebackground="SystemButtonFace",
                    state="normal",
                    fg="black",
                    activeforeground="black",
                )
            self.mono_button.config(
                bg="green", 
                activebackground="green", 
                state="active",
                fg="white",
                activeforeground="white",
            )
            self.camera.isColored = False

class GUI:

    def __init__(self, root: tk.Tk = None):
        self.root = root
        self.video_editor = VideoEditor(self.root)
        self.camera = Camera(self.root,  self.video_editor)
        self.styles = {}
        self.image_view = ImageViewContainer(self.root, self.video_editor,self.styles ,self.camera)
        self.camera.load_image_view(self.image_view)

        self.control_panel = ControlPanelContainer(self.root, self.camera,  self.styles, self.image_view)

        self.configure_image_view()
        self.configure_control_panel()

        

        self.themes = {
            "RetroCream" : {
                "control_panel" : "#fff3e0",
                "trigger_panel" : "#f5e6d3",
                "image_frame" : "#faf4ed",
            },
            "Nature" : {
                "control_panel" : "#3a6351",
                "trigger_panel" : "#f2e8cf",
                "image_frame" : "#e4dccf"
            },
            "CyberPunk": {
                "control_panel" : "#1a1a1a",
                "trigger_panel" : "#2d2d2d",
                "image_frame" : "#0a0a0a"
            },
            "ProDark" : {
                "control_panel" : "#2b2b2b",
                "trigger_panel" : "#363636",
                "image_frame" : "#212121"
            }
        }
        self.apply_theme(self.themes['Nature'])


    def configure_control_panel(self):
        self.control_panel.play_pause_button.bind("<Button-1>" , lambda e : play_pause_button_clicked())

        def play_pause_button_clicked():
            self.control_panel.play_pause_button_clicked()
            self.camera.switch_capture()

    def configure_image_view(self):
        self.image_view.video_editor_button.configure(command= self.open_video_editor)
        self.image_view.image_frame.bind('<Button-1>' , lambda e : self.camera.switch_crosshair())

    def switch_crosshair(self):
        self.camera.switch_crosshair()

    def open_video_editor(self):
        self.video_editor.place(relx=0.5 , rely=0.5, anchor="center", relwidth=1, relheight=1)
        self.video_editor.lift()

    def apply_theme(self, theme):
        self.control_panel.control_panel_frame.config(bg=theme['control_panel'])
        self.image_view.image_frame.config(bg=theme['image_frame'])


def add_slider_with_entry(
    root: tk.Tk,
    label_text: str,
    slider_range: dict,
    row: int,
    initial_value=None,
    chkbutton: bool = False,
    chkbutton_command=None,
    chkbutton_initial:bool =False
):
    slider_label = tk.Label(
        root, text=label_text, font=("Segoe UI", 11), bg="#e3f0fc", fg="#3B4252"
    )

    min_val = slider_range["min"]
    max_val = slider_range["max"]
    inc = slider_range["inc"]

    slider = tk.Scale(
        root,
        from_=min_val,
        to=max_val,
        orient=tk.HORIZONTAL,
        resolution=inc,
        bg="#e3f0fc",
        troughcolor="#c7d9f0",
        activebackground="#aec5e0",
        sliderrelief="flat",
        width=12,
        length=150,
        font=("Segoe UI", 8),
    )

    if initial_value is not None:
        slider.set(initial_value)
    else:
        slider.set(min_val)

    entry = tk.Entry(
        root,
        width=10,
        font=("Segoe UI", 11),
        bg="white",
        highlightcolor="#8fa8c2",
        fg="#2E3440",
        relief="flat",
        highlightthickness=1,
        borderwidth=0,
    )
    entry.insert(0, slider.get())


    

    slider_label.grid(row=row, column=1, padx=5, pady=5, sticky="w")
    slider.grid(row=row, column=2)
    entry.grid(row=row, column=3, padx=5, pady=5)

    def update_entry(value=None):
        if value is None:
            value = slider.get()
        entry.delete(0, "end")
        entry.insert(0, str(value))

    def adjust_to_nearest_step(value, start, end, step):
        if value < start:
            return start
        if value > end:
            return end
        offset = value - start
        nearest_step = round(offset / step)
        adjusted_value = start + nearest_step * step
        return min(max(adjusted_value, start), end)

    def update_slider(event):
        try:
            value = float(entry.get())
            if min_val <= value <= max_val:
                adjusted = adjust_to_nearest_step(value, min_val, max_val, inc)
                slider.set(adjusted)
                update_entry(adjusted)
            else:
                messagebox.showerror("Ошибка", "Значение вне допустимого диапазона.")
                update_entry(slider.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите числовое значение.")
            update_entry(slider.get())

    slider.config(command=lambda val: update_entry())
    entry.bind("<Return>", update_slider)

    return slider, entry
