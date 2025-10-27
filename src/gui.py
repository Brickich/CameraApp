import tkinter as tk
from tkinter import messagebox, ttk
from src.camera import Camera
from src.frame_viewer import FrameViewer
from PIL import ImageTk, Image

class CustomStyles:
    def __init__(self):
        self.setup_styles()
    
    def setup_styles(self):
        style = ttk.Style()
        
        style.configure(
            'Active.TButton',
            background='green', 
            foreground='black',
            borderwidth=1,
            focuscolor='none',
            padding=(10, 5)
        )
        
        style.map('Active.TButton',
            background=[('active', 'green'),   
                       ('pressed', '#3d8b40'),   
                       ('disabled', '#cccccc')],  
            foreground=[('active', 'white'),
                       ('pressed', 'white'),
                       ('disabled', '#666666')]
        )
        
        style.configure(
            'Inactive.TButton',
            background='white',  
            foreground='black',   
            borderwidth=1,
            focuscolor='none',
            padding=(10, 5)
        )
        
        style.map('Inactive.TButton',
            background=[('active', '#707070'),  
                       ('pressed', '#606060'),   
                       ('disabled', '#cccccc')],  
            foreground=[('active', 'white'),
                       ('pressed', 'white'),
                       ('disabled', '#999999')]   
        )
        
        style.configure(
            'Trigger.TButton',
            background='white', 
            foreground='black',
            borderwidth=2,
            padding=(15, 8),
            font=('Segoe UI', 11, 'bold')
        )
        
        style.map('Trigger.TButton',
            background=[('active', 'red'),
                       ('pressed', 'red'),
                       ('!disabled', 'black')], 
            foreground=[('active', 'black'),
                       ('pressed', 'black'),
                       ('!disabled', 'black')]
        )



class CanvasManager(tk.Frame):
    def __init__(self, root, cameras_count: int ):
        super().__init__(root)
        self.root = root

        self.canvases: list[tk.Canvas] = []
        self.fps_labels: list[tk.Label] = []

        for i in range(cameras_count):
            canvas = tk.Canvas(self, bg="grey")
            title = ttk.Label(canvas, text=f"Camera {i + 1}", font=("Arial", 8), 
                            background="gray30", justify="center", foreground="white")
            fps = ttk.Label(canvas, text=f"FPS : 24.0", font=("Arial", 8), 
                          background="gray30", foreground="white")

            title.pack(side="top", anchor="center", pady=10)
            fps.pack(side="bottom", anchor="center", pady=10)
            canvas.pack(fill="both", expand=True, padx=10, pady=10)
            self.fps_labels.append(fps)
            self.canvases.append(canvas)
    
    def show_all_cameras(self):
        for canvas in self.canvases:
            canvas.pack_forget()
            canvas.pack(side="top", expand=True, fill="both")
    
    def show_single_camera(self, camera_index: int):
        for canvas in self.canvases:
            canvas.pack_forget()
        self.canvases[camera_index].pack(fill="both", expand=True)

class Sliders(ttk.Frame):
    def __init__(self, root, camera: Camera):
        super().__init__(root)
        self.root = root
        self.camera = camera
        self.sliders: dict[str, tk.Scale] = {}
        self.entries = {}

        self.__init_original_ranges()
        self.__init_sliders()
        
    def __init_original_ranges(self):
        self.original_ranges = {
            "Width": self.camera.Width.get_range(),
            "Height": self.camera.Height.get_range(),
            "OffsetX": self.camera.OffsetX.get_range(),
            "OffsetY": self.camera.OffsetY.get_range(),
        }

    def __init_sliders(self):
        self.slider_configs = self.__get_slider_configuration()
        for row, (param_name, config) in enumerate(self.slider_configs.items(), 1):
            self.__create_slider_with_entry(param_name, config, row)

    def __get_slider_configuration(self):
        config = {}
        config['Width'] = {
            "range": self.camera.Width.get_range(),
            "initial": self.camera.Width.get(),
            "data_type": int,
            "label": "Width",
        }

        config["Height"] = {
            "range": self.camera.Height.get_range(),
            "initial": self.camera.Height.get(),
            "data_type": int,
            "label": "Height"
        }
        
        exposure_range = self.camera.ExposureTime.get_range()
        if self.camera.type != "MER":
            exposure_range['min'] = 1.0
        exposure_range["inc"] = 1.0
        
        config["ExposureTime"] = {
            "range": exposure_range,
            "initial": self.camera.ExposureTime.get(),
            "data_type": float,
            "label": "Exposure Time, μs"
        }
        
        fps_range = self.camera.FrameRate.get_range()
        fps_range['min'] = 1.0
        fps_range['inc'] = 1.0
        
        config["FrameRate"] = {
            "range": fps_range,
            "initial": self.camera.FrameRate.get(),
            "data_type": float,
            "label": "FrameRate"
        }
        
        gain_range = self.camera.Gain.get_range()
        gain_range['inc'] = 0.1
        
        config["Gain"] = {
            "range": gain_range,
            "initial": self.camera.Gain.get(),
            "data_type": float,
            "label": "Gain, dB"
        }
        
        trigger_delay_range = self.camera.TriggerDelay.get_range()
        trigger_delay_range['inc'] = 0.01
        
        config["TriggerDelay"] = {
            "range": trigger_delay_range,
            "initial": self.camera.TriggerDelay.get(),
            "data_type": float,
            "label": "Trigger Delay, μs"
        }
        
        config["QuantityOfFrames"] = {
            "range": {"min": 10, "max": 1000, "inc": 1},
            "initial": getattr(self.camera, 'QuantityOfFrames', 100),
            "data_type": int,
            "label": "NumberOfFrames"
        }
        
        config["OffsetX"] = {
            "range": self.camera.OffsetX.get_range(),
            "initial": self.camera.OffsetX.get(),
            "data_type": int,
            "label": "OffsetX"
        }
        
        config["OffsetY"] = {
            "range": self.camera.OffsetY.get_range(),
            "initial": self.camera.OffsetY.get(),
            "data_type": int,
            "label": "OffsetY"
        }
        return config

    def __create_slider_with_entry(self, param_name, config, row):
        def __validate_input(value: str, data_type) -> bool:
            if value == "":
                return True
            try:
                if data_type == int:
                    int(value)
                elif data_type == float:
                    float(value)
                return True
            except ValueError:
                return False

        label_text = config["label"]
        range_config = config["range"]
        initial_value = config["initial"]
        data_type = config["data_type"]

        slider_label = ttk.Label(self, text=label_text, font=("Segoe UI", 9), 
                               background="#e3f0fc", foreground="#3B4252")
        min_val = range_config["min"]
        max_val = range_config["max"]
        inc = range_config["inc"]

        if data_type == int:
            var = tk.IntVar()
        else:
            var = tk.DoubleVar()

        slider = tk.Scale(
            self,
            from_=min_val,
            to=max_val,
            width=12,
            variable=var,
            resolution=inc,
            orient="horizontal"
        )
        var.set(initial_value)

        validation = self.register(__validate_input)
        entry = ttk.Entry(
            self,
            width=8,
            validate="key",
            validatecommand=(validation, '%P', data_type)
        )
        entry.insert(0, str(initial_value))

        slider_label.grid(row=row, column=0, padx=5, sticky="w")
        slider.grid(row=row, column=1, padx=5)
        entry.grid(row=row, column=2, padx=5)

        self.sliders[param_name] = slider
        self.entries[param_name] = entry

        slider.configure(command=lambda val, p=param_name: self.__on_slider_changed(p))
        entry.bind("<Return>", lambda e, p=param_name: self.__on_entry_changed(p))   
        entry.bind("<FocusOut>", lambda e, p=param_name: self.__on_entry_changed(p))


    def _update_slider_range(self, param_name: str, new_max: float):
        slider = self.sliders[param_name]
        entry = self.entries[param_name]
        
        current_value = slider.get()
        min_val = self.original_ranges[param_name]["min"]
        
        slider.config(from_=min_val, to=new_max)
        
        if current_value > new_max:
            new_value = new_max
            slider.set(new_value)
            entry.delete(0, tk.END)
            entry.insert(0, str(new_value))
        elif current_value < min_val:
            new_value = min_val
            slider.set(new_value)
            entry.delete(0, tk.END)
            entry.insert(0, str(new_value))

    def __on_slider_changed(self, param_name: str):
        slider = self.sliders[param_name]
        entry = self.entries[param_name]

        value = slider.get()
        entry.delete(0, "end")
        entry.insert(0, str(value))
        
        self.__adjust_offsets(param_name)

    def __on_entry_changed(self, param_name: str):
        entry = self.entries[param_name]
        slider = self.sliders[param_name]

        try:
            current_value = slider.get()
            if isinstance(current_value, int):
                data_type = int
            else:
                data_type = float

            value = data_type(entry.get())
            min_val = slider.cget("from")
            max_val = slider.cget("to")
            
            if min_val <= value <= max_val:
                inc = slider.cget("resolution")
                adjusted_value = self.__adjust_to_step(value, min_val, max_val, inc)
                slider.set(adjusted_value)
                entry.delete(0, tk.END)
                entry.insert(0, str(adjusted_value))
            else:
                messagebox.showerror("Ошибка", 
                                   f"Значение должно быть между {min_val} и {max_val}")
                entry.delete(0, tk.END)
                entry.insert(0, str(slider.get()))
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное числовое значение")
            entry.delete(0, tk.END)
            entry.insert(0, str(slider.get()))
        finally:
            self.__adjust_offsets(param_name)

    def __adjust_offsets(self, param_name):
        if param_name in ["Width", "Height", "OffsetX", "OffsetY"]:
            max_width = self.original_ranges["Width"]["max"]
            max_height = self.original_ranges["Height"]["max"]

            match param_name:
                case "Width":
                    current_width = self.sliders["Width"].get()
                    new_offsetx_max = max_width - current_width
                    self._update_slider_with_correction("OffsetX", new_offsetx_max)

                case "Height":
                    current_height = self.sliders["Height"].get()
                    new_offsety_max = max_height - current_height
                    self._update_slider_with_correction("OffsetY", new_offsety_max)

                case "OffsetX":
                    current_offset_x = self.sliders["OffsetX"].get()
                    new_width_max = max_width - current_offset_x
                    self._update_slider_with_correction("Width", new_width_max)

                case "OffsetY":
                    current_offset_y = self.sliders["OffsetY"].get()
                    new_height_max = max_height - current_offset_y
                    self._update_slider_with_correction("Height", new_height_max)

    def _update_slider_with_correction(self, param_name: str, new_max: float):
        slider = self.sliders[param_name]
        entry = self.entries[param_name]

        current_value = slider.get()
        min_val = self.original_ranges[param_name]["min"]

        slider.config(to=new_max)

        if current_value > new_max:
            new_value = new_max
            slider.set(new_value)
            entry.delete(0, tk.END)
            entry.insert(0, str(new_value))
        elif current_value < min_val:
            new_value = min_val
            slider.set(new_value)
            entry.delete(0, tk.END)
            entry.insert(0, str(new_value))

    def __adjust_to_step(self, value: float, min_val: float, max_val: float, step: float):
        if value < min_val:
            return min_val
        if value > max_val:
            return max_val
        
        steps = round((value - min_val) / step)
        adjusted_value = min_val + steps * step
        return min(max(adjusted_value, min_val), max_val)

    def get_preset(self):
        preset = {}
        for param_name, entry in self.entries.items():
            try:    
                data_type = self.slider_configs[param_name]["data_type"]
                value_str = entry.get()
                preset[param_name] = data_type(value_str)
            except (ValueError, tk.TclError):
                preset[param_name] = self.__get_value(param_name)
        return preset

    def __get_value(self, param_name):
        if param_name in self.sliders:
            return self.sliders[param_name].get()
        else:
            if hasattr(self.camera, param_name):
                return getattr(self.camera, param_name).get()
            return 0

    def set_values(self, preset: dict):
        for param_name, value in preset.items():
            if param_name in self.sliders and param_name in self.entries:
                self.sliders[param_name].set(value)
                self.entries[param_name].delete(0, tk.END)
                self.entries[param_name].insert(0, str(value))

class SettingsPane(ttk.Frame):
    def __init__(self, root, camera: Camera ):
        super().__init__(root)
        self.root = root
        self.camera = camera

        self.trigger_mode_enabled = False
        self.preview_mode_enabled = True
        self.colored_enabled = self.camera.colored
        self.mono_enabled = not self.colored_enabled

        self.button_size = (25, 25)
        self.__launch__()

    def on_trigger_switch(self):
        self.trigger_mode_enabled = True
        self.preview_mode_enabled = False
        self.trigger_mode_button.configure(style='Active.TButton')
        self.preview_mode_button.configure(style='Inactive.TButton')

    def on_preview_switch(self):
        self.preview_mode_enabled = True
        self.trigger_mode_enabled = False
        self.preview_mode_button.configure(style='Active.TButton')
        self.trigger_mode_button.configure(style='Inactive.TButton')

    def __launch__(self):
        def on_trigger_change(event):
            trigger_mode = self.trigger_modes.get()
            self.selected_trigger_source = trigger_mode
            self.trigger_source = trigger_mode

        self.trigger_button = ttk.Button(self, text="Start trigger", style="Inactive.TButton")
        self.trigger_button.pack(anchor="center", pady=(5, 0))
        
        self.__init_buttons()
        self.control_button_frame.pack(fill="x")

        ttk.Separator(self).pack(fill="x", pady=5, padx=5)
        
        trigger_sources = self.camera.TriggerSource.get_range()
        trigger_values = [value["symbolic"] for value in trigger_sources]

        self.selected_trigger_source = tk.StringVar()
        self.trigger_source = trigger_values[0]

        self.acquisition_control_frame = ttk.Frame(self)
        
        self.trigger_mode_button = ttk.Button(
            self.acquisition_control_frame, 
            text="Trigger Mode", 
            style="Inactive.TButton" 
        )
        self.trigger_mode_button.pack(side="right", fill="x", padx=10)
        
        self.preview_mode_button = ttk.Button(
            self.acquisition_control_frame, 
            text="Preview Mode", 
            style="Active.TButton"  
        )
        self.preview_mode_button.pack(side="left", fill="x", padx=10)

        self.acquisition_control_frame.pack(fill="x")

        self.trigger_source_frame = ttk.Frame(self)
        self.trigger_source_label = ttk.Label(
            self.trigger_source_frame, 
            font=("Verdana", 10), 
            text="Trigger Source", 
            background="white"
        )
        
        self.trigger_modes = ttk.Combobox(
            self.trigger_source_frame, 
            font=("Verdana", 10), 
            values=trigger_values, 
            textvariable=self.selected_trigger_source,
            state="readonly", 
            width=10, 
            justify="center"
        )
        self.trigger_modes.set(trigger_values[0])
        self.trigger_modes.bind("<<ComboboxSelected>>", on_trigger_change)

        self.trigger_source_label.pack(side="left", padx=(10, 0))
        self.trigger_modes.pack(side="right", fill="x", padx=(0, 10))
        self.trigger_source_frame.pack(side="top", fill="x")

        self.color_mode_frame = ttk.Frame(self)
        
        color_supported = self.camera.SupportColorFormat
        mono_supported = self.camera.SupportMonoFormat
        
        colored_style = 'Active.TButton' if self.camera.colored and color_supported else 'Inactive.TButton'
        mono_style = 'Active.TButton' if not self.camera.colored and mono_supported else 'Inactive.TButton'
        
        self.colored_button = ttk.Button(
            self.color_mode_frame, 
            text="Colored",
            width=10,  
            command=lambda: self.switch_color("color"),
            style=colored_style,
            state="normal" if color_supported else "disabled"
        )
        self.colored_button.pack(side="left", anchor="center")

        self.mono_button = ttk.Button(
            self.color_mode_frame, 
            text="Mono",
            width=10,
            command=lambda: self.switch_color("mono"), 
            style=mono_style,
            state="normal" if mono_supported else "disabled"
        )
        self.mono_button.pack(side="right", anchor="center")
        self.color_mode_frame.pack(side="top", fill="x", padx=5)

        self.apply_button = ttk.Button(self, text="Apply Settings", style="Active.TButton")
        self.apply_button.pack(anchor="center")

        self.sliders = Sliders(self, self.camera)
        self.sliders.pack(fill="both", padx=5)

    def switch_color(self, mode="color"):
        mode = mode.lower()
        if mode == "color" and self.camera.SupportColorFormat:
            self.colored_enabled = True
            self.mono_enabled = False
            self.camera.colored = True
            
            self.colored_button.configure(style='Active.TButton')
            self.mono_button.configure(style='Inactive.TButton')
            
        elif mode == "mono" and self.camera.SupportMonoFormat:
            self.mono_enabled = True
            self.colored_enabled = False
            self.camera.colored = False
            
            self.mono_button.configure(style='Active.TButton')
            self.colored_button.configure(style='Inactive.TButton')

    def __init_buttons(self):
        self.control_button_frame = tk.Frame(self)
        image_paths = {
            "white_balance": "assets/white_balance.png",
            "crosshair": "assets/crosshair.png",
            "flip_h": "assets/flip_h.png",
            "flip_v": "assets/flip_v.png",
            "rotate_right": "assets/rotate_to_right.png",
            "rotate_left": "assets/rotate_to_left.png",
        }

        self.wbalance_image = ImageTk.PhotoImage(Image.open(image_paths["white_balance"]).resize(self.button_size))
        self.crosshair_image = ImageTk.PhotoImage(Image.open(image_paths["crosshair"]).resize(self.button_size))
        self.flip_h_image = ImageTk.PhotoImage(Image.open(image_paths["flip_h"]).resize(self.button_size))
        self.flip_v_image = ImageTk.PhotoImage(Image.open(image_paths["flip_v"]).resize(self.button_size))
        self.rotate_right_image = ImageTk.PhotoImage(Image.open(image_paths["rotate_right"]).resize(self.button_size))
        self.rotate_left_image = ImageTk.PhotoImage(Image.open(image_paths["rotate_left"]).resize(self.button_size))

        self.play_index = 0
        self.play_pause_images = [ImageTk.PhotoImage(Image.open(img).resize((30,30))) 
                                 for img in ["assets/play_button.png", "assets/pause_button.png"]]
        
        self.play_button = tk.Button(
            self.control_button_frame,
            image=self.play_pause_images[self.play_index],
            command=self.play_button_click
        )
        self.play_button.grid(row=0, column=0, padx=5, pady=5)

        buttons_data = [
            (self.wbalance_image, lambda: self.camera.switch_white_balance()),
            (self.crosshair_image, lambda: self.camera.switch_crosshair()),
            (self.flip_h_image, lambda: self.camera.flip_image_horizontally()),
            (self.flip_v_image, lambda: self.camera.flip_image_vertically()),
            (self.rotate_right_image, lambda: self.camera.rotate_image_right()),
            (self.rotate_left_image, lambda: self.camera.rotate_image_left()),
        ]

        for i, (image, command) in enumerate(buttons_data, 1):
            button = tk.Button(
                self.control_button_frame,
                image=image,
                command=command
            )
            button.grid(row=0, column=i, padx=5, pady=5)
            self.control_button_frame.grid_columnconfigure(i, weight=1)
    
    def enable_trigger_button(self):
        self.trigger_button.configure(style='Active.TButton')
    
    def disable_trigger_button(self):
        self.trigger_button.configure(style="Inactive.TButton")

    def disable_play_button(self):
        self.play_index = 0
        self.play_button.config(image=self.play_pause_images[self.play_index])
        self.play_button.image = self.play_pause_images[self.play_index]

    def play_button_click(self):
        self.play_index = 1 - self.play_index
        self.play_button.config(image=self.play_pause_images[self.play_index])
        self.play_button.image = self.play_pause_images[self.play_index]



class CameraSelectionPanel(ttk.Frame):
    def __init__(self, root, cameras_count: int, canvas_manager: CanvasManager ):
        super().__init__(root)
        self.root = root
        self.cameras_count = cameras_count
        self.canvas_manager = canvas_manager
        
        self.buttons: list[ttk.Button] = []
        self._create_panel()
    
    def _create_panel(self):        
        self.all_cameras_btn = ttk.Button(
            self, 
            text="All Cameras",
            command=self._show_all_cameras,
            style="Active.TButton"  
        )
        self.all_cameras_btn.pack(pady=5, padx=25)
        
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill="x", padx=5)
        
        for i in range(self.cameras_count):
            btn = ttk.Button(
                self,
                text=f"Camera {i+1}",
                command=lambda idx=i: self._show_single_camera(idx),
                style="Inactive.TButton"  
            )
            btn.pack(pady=3, padx=10)
            self.buttons.append(btn)
        
        self.mode_label = ttk.Label(
            self, 
            text="Mode: All Cameras", 
            font=("Arial", 8), 
            background="#f0f0f0", 
            foreground="#666"
        )
        self.mode_label.pack()
    
    def _show_all_cameras(self):
        self.canvas_manager.show_all_cameras()
        self.mode_label.config(text="Mode: All Cameras")
        self.all_cameras_btn.configure(style="Active.TButton")
        for btn in self.buttons:
            btn.configure(style="Inactive.TButton")
    
    def _show_single_camera(self, camera_index: int):
        self.canvas_manager.show_single_camera(camera_index)
        self.mode_label.config(text=f"Mode: Camera {camera_index + 1}")
        self.all_cameras_btn.configure(style="Inactive.TButton")
        for i, btn in enumerate(self.buttons):
            if i == camera_index:
                btn.configure(style="Active.TButton")
            else:
                btn.configure(style="Inactive.TButton")

class SettingsFrame(tk.Frame):
    def __init__(self, root, cameras: list[Camera] ):
        super().__init__(root, relief="sunken")
        self.cameras = cameras

        self.settings_panes: list[SettingsPane] = []
        self.buttons: list[ttk.Button] = []

        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(fill="x")

        for i in range(len(self.cameras)):
            settings_pane = SettingsPane(self, self.cameras[i])
            cam_button = ttk.Button(
                self.button_frame,
                command=lambda idx=i: self.switch_settings_pane(idx),
                text=f"Camera{i+1} settings",
                style="Inactive.TButton" 
            )
            cam_button.grid(row=0, column=i, padx=5)
            self.buttons.append(cam_button)
            self.button_frame.grid_columnconfigure(i, weight=1)
            self.settings_panes.append(settings_pane)
        

    def switch_settings_pane(self, index: int):
        for i, pane in enumerate(self.settings_panes):
            pane.pack_forget()
            if i == index:
                self.buttons[i].configure(style="Active.TButton")
            else:
                self.buttons[i].configure(style="Inactive.TButton")
        self.settings_panes[index].pack(fill="both", expand=True)

class GUI:
    def __init__(self, root: tk.Tk, cameras: list[Camera]):
        self.root = root
        self.cameras = cameras
        self.cameras_amount = len(cameras)
        self.frame_viewer = FrameViewer(self.root, self.cameras_amount)
        self.styles = CustomStyles()
        self.main_pane = tk.PanedWindow(self.root, orient="horizontal")
        self.main_pane.pack(fill="both", expand=True, padx=5, pady=5)

        self.canvas_frame = CanvasManager(self.main_pane, self.cameras_amount )
        self.main_pane.add(self.canvas_frame, stretch="always")

        self.right_panel = ttk.Frame(self.main_pane)
        self.main_pane.add(self.right_panel, stretch="never", width=300)

        self.camera_selection_panel = CameraSelectionPanel(
            self.right_panel, self.cameras_amount, self.canvas_frame , 
        )
        self.camera_selection_panel.pack(fill="x")

        self.settings_frame = SettingsFrame(self.right_panel, cameras )
        self.settings_frame.pack(padx=5, pady=5)

        frame_viewer_image = ImageTk.PhotoImage(
            Image.open("assets/video_editor.png").resize((30, 30))
        )
        self.frame_viewer_button = ttk.Button(
            self.right_panel, 
            image=frame_viewer_image,
        )
        self.frame_viewer_button.image = frame_viewer_image
        self.frame_viewer_button.pack(anchor="center", padx=5, pady=5)