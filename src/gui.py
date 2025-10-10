import tkinter as tk
from.video_editor import VideoEditor
from tkinter import messagebox
from src.camera import Camera


class AdjusterFrame(tk.Frame):
    def __init__(self , root , camera:Camera):
        super().__init__(root , bd=2, relief="ridge",
                         background="#e3f0fc",highlightbackground="#8fa8c2",highlightthickness=1,)
        self.root = root
        self.camera = camera
        self.sliders:dict[str , tk.Scale] = {}
        self.entries = {}

        self.__init_original_ranges()
        self.__init_sliders()
        

    def __init_original_ranges(self):
        self.original_ranges = {
            "Width" : self.camera.Width.get_range(),
            "Height" : self.camera.Height.get_range(),
            "OffsetX" : self.camera.OffsetX.get_range(),
            "OffsetY" : self.camera.OffsetY.get_range(),
        }

    def __init_sliders(self):
        slider_configs = self.__get_slider_configuration()

        for row , (param_name , config) in enumerate(slider_configs.items() , 1):
            self.__create_slider_with_entry(param_name , config , row)


    def __get_slider_configuration(self):
        config = {}

        config['Width'] = {
            "range" : self.camera.Width.get_range(),
            "initial" : self.camera.Width.get(),
            "data_type" : int ,
            "label" : "Width",
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
        
        config["NumberOfFrames"] = {
            "range": {"min": 10, "max": 1000, "inc": 1},
            "initial": getattr(self.camera, 'quantity_of_frames', 100),
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


    def __create_slider_with_entry(self , param_name, config , row):
        def __validate_input(value:str , data_type:str) -> bool :
            if value == "":
                return True

            try:
                if data_type == "int" :
                    int(value)
                else:
                    float(value)
                return True
            except ValueError:
                return False


        label_text = config["label"]
        range = config["range"]
        initial_value = config["initial"]
        data_type = config['data_type']

        slider_label = tk.Label(self ,  text=label_text , font=("Segoe UI" , 9) , bg="#e3f0fc", fg="#3B4252")
        min_val = range["min"]
        max_val = range["max"]
        inc = range["inc"]

        slider = tk.Scale(
            self,
            from_=min_val,
            to=max_val,
            orient=tk.HORIZONTAL,
            resolution=inc,
            bg="#e3f0fc",
            troughcolor="#c7d9f0",
            activebackground="#aec5e0",
            sliderrelief="flat",
            width=12,
            length=100,
            font=("Segoe UI", 8),
        )
        slider.set(initial_value)

        validation = self.register(__validate_input)

        entry = tk.Entry(
            self,
            width=10,
            font=("Segoe UI", 10),
            bg="white",
            highlightcolor="#8fa8c2",
            fg="#2E3440",
            relief="flat",
            highlightthickness=1,
            borderwidth=0,
            validate="key",
            validatecommand=(validation, '%P', data_type.__name__)
        )
        entry.insert(0 , str(initial_value))

        slider_label.grid(row=row , column=0, padx=5, sticky="w")
        slider.grid(row=row, column=1, padx=5)
        entry.grid(row=row, column=2, padx=5)

        self.sliders[param_name] = slider
        self.entries[param_name] = entry

        slider.config(command=lambda val, p = param_name : self.__on_slider_changed(p))
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

    def __on_slider_changed(self , param_name:str):
        slider = self.sliders[param_name]
        entry = self.entries[param_name]

        value = slider.get()
        entry.delete(0, "end")
        entry.insert(0, str(value))
        
        self.__adjust_offsets(param_name)


    def __on_entry_changed(self, param_name:str):
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
        if value< min_val:
            return min_val
        if value > max_val:
            return max_val
        
        steps = round((value - min_val) / step)
        adjusted_value = min_val + steps * step

        return min( max(adjusted_value , min_val) , max_val)

    def get_preset(self):
        preset = {}
        for param_name , entry in self.entries.items():
            try:
                value_str = entry.get()
                slider_value = self.__get_value(param_name)
                if isinstance(slider_value , int):
                    preset[param_name] = int(value_str)
                else:
                    preset[param_name] = float(value_str)
            except (ValueError , tk.TclError) :
                preset[param_name] = self.__get_value(param_name)
        
        return preset

    def __get_value(self, param_name):
        if param_name in self.sliders:
            return self.sliders[param_name].get()
        else:
            if hasattr(self.camera, param_name):
                return getattr(self.camera, param_name).get()
            return 0

    def set_values(self, preset:dict):
        for param_name , value in preset.items():
            if param_name in self.sliders and param_name in self.entries:
                self.sliders[param_name].set(value)
                self.entries[param_name].delete(0, tk.END)
                self.entries[param_name].insert(0, str(value))




class SettingsFrame(tk.Frame):
    def __init__(self , root , camera:Camera, button_size = 10):
        super().__init__(root ,             
                         bd=2,
                        relief=tk.SOLID,
                        bg="#88bdf2",)
        self.root = root
        self.camera = camera
        self.button_size = button_size
        self.save_image = tk.PhotoImage(file = "assets/save.png").subsample(10)


        self.colored_enabled = self.camera.colored
        self.mono_enabled = not self.colored_enabled


        self.colored_button = tk.Button(self, text="Colored",state=f"{"normal" if self.camera.SupportColorFormat else "disabled"}",
                                         width=10, font=("Verdana" , 12) , command= lambda :switch_color("color"))
        self.colored_button.grid(row=1, column=0, columnspan=2)

        self.mono_button = tk.Button(self, text="Mono",state=f"{"normal" if self.camera.SupportMonoFormat else "disabled"}",
                                      width=10, font=("Verdana" , 12) , command= lambda: switch_color("mono"))
        self.mono_button.grid(row=1, column=1, columnspan=2)




        self.sliders_frame = AdjusterFrame(self , self.camera)
        self.sliders_frame.grid(row=2, sticky="ew", column=0, columnspan=3)

        self.apply_settings_button = tk.Button(self,image=self.save_image)
        self.apply_settings_button.grid(row=3, column=0 , columnspan=3)

        def switch_color(mode = "color"):
            mode = mode.lower()
            if mode == "color":
                if self.camera.SupportColorFormat:

                    self.colored_enabled = True
                    self.mono_enabled = not self.colored_enabled
                    self.camera.colored = True

                    self.colored_button.config(state="active" , background="green" , foreground="white" , activebackground="green" , activeforeground="white")
                    self.mono_button.config(background="SystemButtonFace" ,activebackground="SystemButtonFace" , foreground="black" ,  activeforeground="black")
                    if self.camera.SupportMonoFormat:
                        self.mono_button.config(state="normal")
                    else:
                        self.mono_button.config(state="disabled")

            elif mode == "mono":
                if self.camera.SupportMonoFormat:

                    self.mono_enabled = True
                    self.colored_enabled = not self.mono_enabled
                    self.camera.colored = False

                    self.mono_button.config(state="active" , background="green" , foreground="white" , activebackground="green" , activeforeground="white")
                    self.colored_button.config(background="SystemButtonFace" ,activebackground="SystemButtonFace" , foreground="black" ,  activeforeground="black")
                    if self.camera.SupportColorFormat:
                        self.colored_button.config(state="normal")
                    else:
                        self.colored_button.config(state="disabled")
    


class CameraControlPane():

    def __init__(self, root: tk.Tk, camera:Camera, canvas:tk.Canvas):
        self.root = root
        self.camera = camera
        self.canvas = canvas

        self.settings_frame = SettingsFrame(self.canvas , self.camera)
        self.settings_frame.lift()

        self.button_size = 10

        self.enabled = False

        self.camera_settings_window_enabled = False

        self.settings_image = tk.PhotoImage(file = "assets/settings.png").subsample(self.button_size)
        self.settings_button = tk.Button(self.canvas , image= self.settings_image , command= self.switch)
        self.settings_button.place(relx=1.0, rely= 0.0 , x=-self.settings_button.winfo_reqwidth())
        self.settings_button.lift()

        self.control_panel_frame = self.__init_control_panel()

    def __init_control_panel(self):
        image_paths = {
            "white_balance": "assets/white_balance.png",
            "crosshair": "assets/crosshair.png",
            "flip_h": "assets/flip_h.png",
            "flip_v": "assets/flip_v.png",
            "rotate_right": "assets/rotate_to_right.png",
            "rotate_left": "assets/rotate_to_left.png",
        }


        self.wbalance_image = tk.PhotoImage(file = image_paths["white_balance"]).subsample(self.button_size)
        self.crosshair_image = tk.PhotoImage(file = image_paths["crosshair"]).subsample(self.button_size)
        self.flip_h_image = tk.PhotoImage(file = image_paths["flip_h"]).subsample(self.button_size)
        self.flip_v_image = tk.PhotoImage(file = image_paths["flip_v"]).subsample(self.button_size)
        self.rotate_right_image = tk.PhotoImage(file = image_paths["rotate_right"]).subsample(self.button_size)
        self.rotate_left_image = tk.PhotoImage(file = image_paths["rotate_left"]).subsample(self.button_size)


        control_panel_frame = tk.Frame(self.canvas , bd=0 )
        self.control_panel_placing = {"sticky": "ew", "pady": 10, "padx": 5}

        self.wbalance_button = tk.Button(control_panel_frame,image=self.wbalance_image, command=lambda : self.camera.switch_white_balance())

        self.crosshair_button = tk.Button(control_panel_frame,image=self.crosshair_image, command=  lambda : self.camera.switch_crosshair())

        self.flip_h_button = tk.Button(control_panel_frame, image=self.flip_h_image , command=lambda : self.camera.flip_image_horizontally())

        self.flip_v_button = tk.Button(control_panel_frame, image=self.flip_v_image , command=lambda : self.camera.flip_image_vertically())

        self.rotate_right_button = tk.Button(control_panel_frame,image=self.rotate_right_image, command=lambda : self.camera.rotate_image_right())

        self.rotate_left_button = tk.Button(control_panel_frame, image=self.rotate_left_image , command=lambda : self.camera.rotate_image_left())

        for i, widget in enumerate(
            [
                self.wbalance_button,
                self.crosshair_button,
                self.flip_h_button,
                self.flip_v_button,
                self.rotate_right_button,
                self.rotate_left_button,
            ]
        ):
            widget.grid(row=0, column=i, **self.control_panel_placing)

        return control_panel_frame

    def switch(self):
        self.enabled = not self.enabled
        if self.enabled:
            self.control_panel_frame.lift()
            self.settings_frame.lift()
            self.control_panel_frame.place(relx=0.0 , rely=0.0)
            self.settings_frame.place(relx=1.0 , rely= 0.0 , x=-self.settings_frame.winfo_reqwidth() , y=self.settings_button.winfo_height() + 5)
        else:
            self.control_panel_frame.lower()
            self.settings_frame.lower()
            self.control_panel_frame.place_forget()
            self.settings_frame.place_forget()

    
class GUI:

    def __init__(self, root: tk.Tk, cameras_count:int = 1):
        self.root = root
        self.video_editor = VideoEditor(self.root)
        self.canvases:list[tk.Canvas] = []
        self.fps_labels:list[tk.Label] = []

        self.cameras_count = cameras_count

        self.play_pause_index = 0

        self.trigger_frame_enabled = False
        
        self.trigger_modes = {
            "SOFTWARE" : True,
            "LINE0" : False,
            "LINE2" : False
        }

        general_control_frame_pos={"relx": 0.0,"rely": 0.0,"x": 0, "y": 0, "relwidth": 1.0, "relheight": 0.1}
        general_image_frame_pos = {"relx" : 0.0 , "rely" : 0.1 , "x" : 0 , "y" : 0 , "relwidth" : 1.0 , "relheight" : 0.9}

        self.general_control_frame = tk.Frame(self.root , bd=0 , bg="#fff3e0")
        self.general_control_frame.place(general_control_frame_pos)

        self.general_image_frame = tk.Frame(self.root , bd=0 , bg="#faf4ed")
        self.general_image_frame.place(general_image_frame_pos)


        self.__init_general_control_frame()
        self.__init_general_image_frame()

        self.drag_mode = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.current_drag_canvas = None

    def __init_general_control_frame(self):
        self.play_pause_images = [
            tk.PhotoImage(file=img).subsample(20)
            for img in ["assets/play_button.png", "assets/pause_button.png"]
        ]
        self.play_button = tk.Button(self.general_control_frame, image=self.play_pause_images[self.play_pause_index])
        self.play_button.place(x=25 ,relx=0.0,  rely=0.5 , anchor="center" )

        self.trigger_button = tk.Button(self.general_control_frame , text="Trigger" , font=("Verdana" , 12) , command= self.switch_trigger_frame)
        self.trigger_button.place(relx=0.5 , rely=0.5 , anchor="center")

        self.drag_button = tk.Button(self.general_control_frame , text="🔄 Move Canvases" , font=("Verdana", 12), command=self.switch_drag_mode)
        self.drag_button.place(relx=0.8, rely=0.5, anchor="center")

        self.trigger_frame = self.__init_trigger_frame()



    def __init_general_image_frame(self): 
        self.video_editor_image = tk.PhotoImage(file="assets/video_editor.png").subsample(10)
        self.video_editor_button = tk.Button(self.root , image=self.video_editor_image)

        self.video_editor_button.place(
            relx=1.0,
            rely=1.0,
            x=-self.video_editor_button.winfo_reqwidth() - 5,
            y=-self.video_editor_button.winfo_reqheight() - 5,
        )


        for i in range(self.cameras_count):
            canvas = tk.Canvas(self.general_image_frame)
            self.canvases.append( canvas )
            self.fps_labels.append( tk.Label(self.general_image_frame , text="FPS :" , font=("Arial" , 12)) ) 

            canvas.bind("<Button-1>" , self.start_drag)
            canvas.bind("<B1-Motion>" , self.on_drag)
            canvas.bind("<ButtonRelease-1>" , self.stop_drag)


        self.update_canvas_layout()

    def play_button_click(self):
        self.play_pause_index = 1 - self.play_pause_index
        self.play_button.config(image=self.play_pause_images[self.play_pause_index])
        self.play_button.image = self.play_pause_images[self.play_pause_index]

    def switch_trigger_input(self , input = "SOFTWARE"):
        self.switch_trigger_frame()
        input = input.lower()
        inputs = {
            "software" : (True , False , False),
            "line0" : (False , True , False),
            "line2" : (False , False , False),
        }
        if input in inputs:
            soft , l0 , l2 = inputs[input]
            self.SOFTWARE_enabled = soft
            self.LINE0_enabled = l0
            self.LINE2_enabled = l2
        self.trigger_button.config(text=input.upper() , background="green" , activebackground="green" , foreground="white" , activeforeground="white")
        self.switch_trigger_frame()
        
    def switch_trigger_frame(self):
        self.trigger_frame_enabled = not self.trigger_frame_enabled
        if self.trigger_frame_enabled:
            self.trigger_frame.place(relx=0.5 , rely=0.5 , anchor="center")
            self.trigger_frame.lift()
        else:
            self.cancel_trigger()
            self.trigger_frame.lower()
            self.trigger_frame.place_forget()

    def cancel_trigger(self):
        self.trigger_button.config(text="Trigger" , background="SystemButtonFace" , activebackground="SystemButtonFace" , foreground="black" , activeforeground="black")

    def switch_drag_mode(self):
        self.drag_mode = not self.drag_mode
        if self.drag_mode:
            self.drag_button.config(bg="lightblue", text="✅ Move Mode")

            for canvas in self.canvases:
                canvas.config(cursor="fleur")

        else:
            self.drag_button.config(bg="SystemButtonFace", text="🔄 Move Canvases")

            for canvas in self.canvases:
                canvas.config(cursor="")

    def start_drag(self, event):
        if not self.drag_mode :
            return
        self.current_drag_canvas = event.widget


        self.drag_start_y = event.y


    def on_drag(self , event):

        if not self.drag_mode:
            return

        dy = event.y - self.drag_start_y
        current_index = self.canvases.index(self.current_drag_canvas)
        if dy > 0:
            self.current_drag_canvas.configure(height = self.current_drag_canvas.winfo_height() + int(dy))

            if self.current_drag_canvas.winfo_height() > self.general_image_frame.winfo_height():
                self.current_drag_canvas.configure(height = self.general_image_frame.winfo_height())
            if current_index  < self.cameras_count - 1 and delta_y >= 0:
                delta_y = event.y - self.canvases[current_index+1].winfo_height() // 2
                current_index+=1
                self.canvases[current_index].grid(row=current_index)
                self.canvases[current_index+1].grid(row=current_index-1)
            
        elif dy < 0: 
            self.current_drag_canvas.configure(height = self.current_drag_canvas.winfo_height() - int(dy))

            if self.current_drag_canvas.winfo_height() < self.general_image_frame.winfo_height():
                self.current_drag_canvas.configure(height = self.general_image_frame.winfo_height())
            if current_index > 0 and delta_y < 0:
                delta_y = event.y - self.canvases[current_index-1].winfo_height() // 2
                current_index-=1    
                self.canvases[current_index].grid(row=current_index)
                self.canvases[current_index-1].grid(row=current_index+1)

        

    def stop_drag(self , event):
        if not self.drag_mode or self.current_drag_canvas is None:
            return
        self.current_drag_canvas = None




    def update_canvas_layout(self):
        for i , canvas in enumerate(self.canvases):
            canvas.place(relwidth=1.0)

    def update_fps_labels(self , fps , fps_label:tk.Label):
        fps_label.configure(text=f"FPS : {fps if fps else "None"}")

    def __init_trigger_frame(self):
        trigger_frame = tk.Frame(self.general_control_frame,bg="#f5e6d3",relief=tk.RAISED,bd=2)

        self.software_btn = tk.Button(
            trigger_frame,
            text="SOFTWARE",
            font=("Verdana", 10),
            command=lambda: self.set_trigger_mode("SOFTWARE")
        )
        
        self.line0_btn = tk.Button(
            trigger_frame,
            text="LINE0", 
            font=("Verdana", 10),
            command=lambda: self.set_trigger_mode("LINE0")
        )
        
        self.line2_btn = tk.Button(
            trigger_frame,
            text="LINE2",
            font=("Verdana", 10), 
            command=lambda: self.set_trigger_mode("LINE2")
        )

        self.software_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        self.line0_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        self.line2_btn.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        self.update_trigger_buttons_appearance()

        return trigger_frame
    

    def update_trigger_buttons_appearance(self):
        for mode, btn in zip(["SOFTWARE", "LINE0", "LINE2"], 
                           [self.software_btn, self.line0_btn, self.line2_btn]):
            if self.trigger_modes[mode]:
                btn.config(
                    bg="green",
                    activebackground="darkgreen",
                    fg="white",
                    activeforeground="white"
                )
            else:
                btn.config(
                    bg="SystemButtonFace",
                    activebackground="SystemButtonFace",
                    fg="black",
                    activeforeground="black"
                )
        
        active_mode = next((mode for mode, active in self.trigger_modes.items() if active), "Trigger")
        self.trigger_button.config(text=active_mode)

    def set_trigger_mode(self, mode: str):
        for trigger_mode in self.trigger_modes:
            self.trigger_modes[trigger_mode] = (trigger_mode == mode)

        self.update_trigger_buttons_appearance()
        
        self.switch_trigger_frame()
        