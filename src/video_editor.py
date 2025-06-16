import tkinter as tk
from tkinter import ttk
from PIL import Image , ImageTk
from tkinter import filedialog, messagebox
import cv2
from threading import Thread,Timer
import numpy as np
import os


class DualScale(tk.Canvas):
    def __init__(self, root: tk.Frame, min_val=0, max_val=100, **kwargs):
        super().__init__(root, **kwargs)
        self.min_val = min_val
        self.max_val = max_val
        self.range = max_val - min_val
        
        self.width = kwargs.get("width", 300)
        self.height = kwargs.get("height", 80)
        self.padding = 20 
        
        self.start_val = min_val
        self.end_val = max_val
        self.marker_size = 12
        
        self.config(
            width=self.width, 
            height=self.height, 
            bg=kwargs.get("bg", "white"), 
            highlightthickness=0
        )
        
        self.track_start = self.padding
        self.track_end = self.width - self.padding
        self.track_y = self.height * 0.4
        
        self.create_line(
            self.track_start, 
            self.track_y, 
            self.track_end, 
            self.track_y, 
            fill="#808080", 
            width=3
        )
        
        marker_size = 12
        self.start_marker = self.create_oval(
            0, 0, marker_size, marker_size, 
            fill="#4CAF50", outline="#2E7D32", width=2
        )
        
        self.end_marker = self.create_oval(
            0, 0, marker_size, marker_size, 
            fill="#2196F3", outline="#0D47A1", width=2
        )
        
        self.start_text = self.create_text(
            0, self.height * 0.7, 
            text=str(min_val), 
            font=("Arial", 10)
        )
        
        self.end_text = self.create_text(
            0, self.height * 0.7, 
            text=str(max_val), 
            font=("Arial", 10)
        )
        
        self.tag_bind(self.start_marker, '<ButtonPress-1>', self.on_start_press)
        self.tag_bind(self.end_marker, '<ButtonPress-1>', self.on_end_press)
        self.tag_bind(self.start_text, '<ButtonPress-1>', self.on_start_press)
        self.tag_bind(self.end_text, '<ButtonPress-1>', self.on_end_press)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_release)
        
        self.update_markers()
        self.dragging = None

    def pixel_to_value(self, x):
        x = max(self.track_start, min(x, self.track_end))
        position = (x - self.track_start) / (self.track_end - self.track_start)
        return self.min_val + position * self.range

    def value_to_pixel(self, value):
        value = max(self.min_val, min(value, self.max_val))
        position = (value - self.min_val) / self.range
        return self.track_start + position * (self.track_end - self.track_start)

    def on_start_press(self, event):
        self.dragging = 'start'

    def on_end_press(self, event):
        self.dragging = 'end'

    def on_drag(self, event):
        if not self.dragging:
            return

        value = self.pixel_to_value(event.x)
        
        if self.dragging == 'start':
            if value > self.end_val:
                value = int(self.end_val)
            self.start_val = int(value)
        else:
            if value < self.start_val:
                value = int(self.start_val)
            self.end_val = int(value)
            
        self.update_markers()

    def on_release(self, event):
        self.dragging = None

    def update_markers(self):
        start_x = self.value_to_pixel(self.start_val)
        end_x = self.value_to_pixel(self.end_val)
        
        self.coords(
            self.start_marker,
            start_x - self.marker_size/2,
            self.track_y - self.marker_size/2,
            start_x + self.marker_size/2,
            self.track_y + self.marker_size/2
        )
        
        self.coords(
            self.end_marker,
            end_x - self.marker_size/2,
            self.track_y - self.marker_size/2,
            end_x + self.marker_size/2,
            self.track_y + self.marker_size/2
        )
        
        self.coords(self.start_text, start_x, self.height * 0.7)
        self.coords(self.end_text, end_x, self.height * 0.7)
        
        start_val_str = f"{self.start_val:.0f}" if self.start_val.is_integer() else f"{self.start_val:.1f}"
        end_val_str = f"{self.end_val:.0f}" if self.end_val.is_integer() else f"{self.end_val:.1f}"
        
        self.itemconfig(self.start_text, text=start_val_str)
        self.itemconfig(self.end_text, text=end_val_str)

    def get_range(self):
        return (self.start_val, self.end_val)

    def set_range(self, start, end):
        self.start_val = max(self.min_val, min(start, self.max_val))
        self.end_val = min(self.max_val, max(end, self.min_val))
        self.update_markers()
        
    def set_limits(self, min_val, max_val):
        if min_val >= max_val:
            raise ValueError("min_val must be less than max_val")
            
        self.min_val = min_val
        self.max_val = max_val
        self.range = max_val - min_val
        
        self.start_val = max(min_val, min(self.start_val, max_val))
        self.end_val = min(max_val, max(self.end_val, min_val))
        
        if self.start_val > self.end_val:
            self.start_val = min_val
            self.end_val = max_val
            
        self.update_markers()


class VideoEditor(tk.Frame):
    def __init__(self , root:tk.Tk):
        super().__init__(root)
        self.root = root
        self.fps = 10

        self.themes = {
            "RetroCream" : {
                "settings_frame" : "#fff3e0",
                "thumbnail_frame" : "#f5e6d3",
                "preview_frame" : "#faf4ed",
            },
            "Nature" : {
                "settings_frame" : "#3a6351",
                "thumbnail_frame" : "#f2e8cf",
                "preview_frame" : "#e4dccf"
            },
            "CyberPunk": {
                "settings_frame" : "#1a1a1a",
                "thumbnail_frame" : "#2d2d2d",
                "preview_frame" : "#0a0a0a"
            },
            "ProDark" : {
                "settings_frame" : "#2b2b2b",
                "thumbnail_frame" : "#363636",
                "preview_frame" : "#212121"
            }
        }

        self.original_images:list[Image.Image] = []
        self.images:list[Image.Image] = []
        self.timestamps:list[float | None] = []
        self.thumbnail_frames = []
        self.thumbnail_cache = {}
        self.thumbnail_size = (120, 90)
        self.image_index = 0
        self.trimming_window_enabled = False
        self.preview_video_enabled = False
        self.output_dir = "output"
        self.init_editor()

    def init_settings_frame(self):
        self.settings_frame = tk.Frame(self)
        self.settings_frame.place(relx=0 , rely=0 , relheight=0.8 , relwidth=0.2)

        self.theme_combobox = ttk.Combobox(self.settings_frame, width=15)
        self.theme_combobox.place(relx=0 , rely=1.0 , y =-self.theme_combobox.winfo_reqheight() - 5 , x= 5)
        self.theme_combobox.bind("<<ComboboxSelected>>" , self.theme_selected)
        themes = self.themes.keys()
        themes = list(themes)
        self.theme_combobox['values'] = themes

        self.trim_button_image = ImageTk.PhotoImage(Image.open("assets/cut.png").resize((25,25)))
        self.trim_button = tk.Button(self.settings_frame, image= self.trim_button_image, command=self.switch_trimming_frame)
        self.trim_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.preview_image = ImageTk.PhotoImage(Image.open("assets/preview.png").resize((25,25)))
        self.preview_button = tk.Button(self.settings_frame ,image= self.preview_image , command=lambda: self.switch_video_preview(self.preview_button) ,border=3)
        self.preview_button.image = self.preview_image
        self.preview_button.grid(row=0 , column=1, padx=5, pady=5, sticky="ew")
        self.preview_button_label = tk.Label(
            self,
            text="Video Preview",
            background="#FFF8DC",
            foreground="#5C3317",
            font=("Verdana", 8),
            borderwidth=2,
            relief="ridge",
        )
        self.preview_button.bind("<Enter>", lambda e: self.preview_button_label.place(
                x=self.preview_button.winfo_x(),
                y=self.preview_button.winfo_y() + self.preview_button.winfo_reqheight(),
            ),
        )
        self.preview_button.bind("<Leave>", lambda e: self.preview_button_label.place_forget())
        self.preview_button_label.lift()

        self.load_images_image = ImageTk.PhotoImage(Image.open("assets/load_from_file.png").resize((25,25)))
        self.load_images_button = tk.Button(self.settings_frame,image=self.load_images_image, command=self.load_images_from_file)
        self.load_images_button.image = self.load_images_image
        self.load_images_button.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        self.save_video_image = ImageTk.PhotoImage(Image.open("assets/save.png").resize((25,25)))
        self.save_video_button = tk.Button(self.settings_frame, image=self.save_video_image, command=self.export_video)
        self.save_video_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.delete_images_image = ImageTk.PhotoImage(Image.open("assets/delete.png").resize((25,25)))
        self.delete_images_button = tk.Button(self.settings_frame, image=self.delete_images_image, command=lambda: Thread(target=self.delete_images, daemon=True).start())
        self.delete_images_button.grid(row=1 , column=1 , padx=5, pady=5, sticky="ew")

    def init_preview_frame(self):
        self.preview_frame = tk.Frame(self)
        self.preview_frame.place(relx=0.2 , rely=0 , relheight=0.8 , relwidth=0.8)

        previous_button = tk.Button(
            self.preview_frame,
            text="◄",
            command=self.previous_button_clicked,
            font=("arial", 20),
            bg="#4CAF50",
            fg="white",
            anchor="center"
        )
        previous_button.place(relx=0 , rely=0.5 ,  relwidth=0.025, relheight=0.1)

        self.preview_image = tk.Label(self.preview_frame)
        self.preview_image.place(relx=0.5 , rely=0.5 , relwidth=0.95 , relheight=1.0 , anchor="center" )
        image = tk.PhotoImage(file="assets/no_image.png")
        self.preview_image.config(image=image , anchor="center")
        self.preview_image.image = image

        self.preview_text = tk.Label(self.preview_frame , text=f"Time : {self.timestamps[self.image_index] if self.timestamps else "There's no timestamp"} " , font=("Arial" , 12))
        self.preview_text.place(relx=0.5 , rely=1.0 , anchor="center" , y=-self.preview_text.winfo_reqheight()-5)

        next_button = tk.Button(
            self.preview_frame,
            text="►",
            command=self.next_button_clicked,
            font=("arial", 20),
            bg="#4CAF50",
            fg="white",
            anchor="center"
        )
        next_button.place(relx=0.975 , rely=0.5 , relwidth=0.025, relheight=0.1)

    def init_thumbnail_frame(self):
        self.thumbnail_frame = tk.Frame(self)
        self.thumbnail_frame.place(rely=0.8 , relx=0 , relwidth=1.0 , relheight=0.2)

        self.thumbnail_canvas = tk.Canvas(self.thumbnail_frame)
        self.thumbnail_scroll = tk.Scrollbar(self.thumbnail_frame , orient="horizontal" , command=self.thumbnail_canvas_xview)
        self.thumbnail_canvas.configure(xscrollcommand=self.thumbnail_scroll.set)

        self.thumbnail_canvas.place(relheight=0.9 , relwidth=1.0)
        self.thumbnail_scroll.place(rely=0.9 , relheight=0.1 , relwidth=1.0)

        self.thumbnail_container = tk.Frame(self.thumbnail_canvas)

        self.thumbnail_canvas.create_window((0,0) , window=self.thumbnail_container , anchor="nw")

        self.thumbnail_container.bind("<Configure>" , lambda e: self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all")))
        self.thumbnail_canvas.bind_all("<MouseWheel>" , lambda event: self.thumbnail_canvas.xview_scroll(int(1*(event.delta/120)), "units"))

    def init_trimming_window(self):
        self.trimming_window = tk.LabelFrame(
            self.root,
            bd=2,
            relief=tk.SOLID,
            bg="#88bdf2",
            padx=2.5,
            pady=2.5,
            font=("Arial", 10),
        )
        self.fps_label = tk.Label(self.trimming_window , font=("Arial", 10) , text="FPS")

        self.fps_entry = tk.Entry(
            self.trimming_window,
            font=("Arial", 12),
            highlightthickness=3,
            width=10,
            justify="center",
        )
        self.fps_entry.delete(0, "end")
        self.fps_entry.insert(0 , self.fps)
        self.fps_label.grid(row=1 , column=0 , pady=5,padx=0)
        self.fps_entry.grid(row=1, column=1, pady=5 , padx=0)

        self.dual_scale = DualScale(self.trimming_window, 1 , 10 , width = 200 , height = 80)
        self.dual_scale.grid(row=2 , columnspan=2)

    def switch_video_preview(self, widget:tk.Widget):
        self.preview_video_enabled = not self.preview_video_enabled
        if not self.preview_video_enabled:
            widget.config(bg='SystemButtonFace', activebackground='SystemButtonFace')
            return
        widget.config(bg='#90EE90', activebackground='#76EE76')
        if self.images:
            fps = int(self.fps_entry.get())
            delay = int(1000 / fps)
            min_val , max_val = self.dual_scale.get_range()
            index = min_val - 1
            self.update_preview_window(index , delay, min_val , max_val)

    def update_preview_window(self, index:int, delay:int, min_val , max_val):
        if not self.preview_video_enabled:
            return
        self.update_preview(index)
        index +=1
        if index > max_val - 1:
            index = min_val
        self.root.after(delay , lambda: self.update_preview_window(index, delay , min_val , max_val))

    def switch_trimming_frame(self):
        self.trimming_window_enabled = not self.trimming_window_enabled
        if self.trimming_window_enabled:
            window_width = self.trimming_window.winfo_reqwidth()
            window_height = self.trimming_window.winfo_reqheight()
            button_y = self.trim_button.winfo_y()
            button_x = self.trim_button.winfo_x()
            button_height = self.trim_button.winfo_reqheight()
            self.trimming_window.place(
                x = button_x,
                y= button_y + button_height,
                width=window_width,
                height=window_height,
            )
            self.trimming_window.lift()
        else:
            self.trimming_window.place_forget()

    def init_editor(self):
        self.root.bind("<Left>" , self.previous_button_clicked)
        self.root.bind("<Right>" , self.next_button_clicked)

        self.init_settings_frame()
        self.init_preview_frame()
        self.init_thumbnail_frame()
        self.init_trimming_window()
        self.apply_theme(self.themes['Nature'])

        self.close_button_image = ImageTk.PhotoImage(Image.open("assets/camera.png").resize((25,25)))
        self.close_button = tk.Button(self, image=self.close_button_image, command=self.close)
        self.close_button.pack()

    def update_preview(self , index:int):
        image = self.images[index]
        timestamp = self.timestamps[index]

        frame_width = self.preview_image.winfo_width()
        frame_height = self.preview_image.winfo_height()

        if frame_width <= 1 or frame_height <= 1:
            image_tk = ImageTk.PhotoImage(image)
        else:
            width_ratio = frame_width / image.width
            height_ratio = frame_height / image.height
            scale_ratio = min(width_ratio, height_ratio)

            new_width = int(image.width * scale_ratio)
            new_height = int(image.height * scale_ratio)

            resized_image = image.resize((new_width, new_height), Image.LANCZOS)
            image_tk = ImageTk.PhotoImage(resized_image)

        self.preview_image.config(image=image_tk)
        self.preview_image.image = image_tk
        self.preview_text.config(text=f"Frame: {index + 1} Time: {timestamp if timestamp or timestamp == 0.0 else 'None'}µs")

    def close(self):
        self.place_forget()

    def load_camera_data(self, images:list[Image.Image], timestamps:list[float | str]):
        self.load_images(images)
        self.load_timestamps(timestamps)
        self.create_thumbnails(images)
        self.update_preview(self.image_index)
        self.after(1000, lambda: self.dual_scale.set_limits(1, len(self.images)))

    def load_images(self , images:list[Image.Image]):
        for img in images:
            try:
                self.original_images.append(img)
                self.images.append(img)
            except Exception as e:
                print(e)

    def load_timestamps(self, timestamps:list[float | str]):
        for timestamp in timestamps:
            self.timestamps.append(timestamp)

    def load_images_from_file(self):
        file_paths = filedialog.askopenfilenames(
            title="Choose Images",
            filetypes=(
                ("All", "*.png;*.jpg;*.jpeg;*.gif"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg;*.jpeg"),
                ("GIF", "*.gif")
            )
        )
        if not file_paths:
            return

        images:list[Image.Image] = []
        errors = []
        timestamps = []

        for path in file_paths:
            try:
                img = Image.open(path)
                images.append(img)
                timestamps.append("None")
            except ( IOError, OSError) as e:
                errors.append(f"Error in loading {path}: {str(e)}")

        if errors:
            messagebox.showerror("Error" , "\n".join(errors))

        if images:
            Thread(target=lambda : self.load_images(images), daemon=True).start()
            Thread(target=lambda : self.load_timestamps(timestamps), daemon=True).start()
            Thread(target = lambda: self.create_thumbnails(images), daemon=True).start()

    def delete_images(self):
        self.timestamps.clear()
        self.images.clear()
        self.thumbnail_frames.clear()
        self.original_images.clear()
        self.image_index = 0

        for widget in self.thumbnail_container.winfo_children():
            widget.destroy()

        no_image = tk.PhotoImage(file="assets/no_image.png")
        self.preview_image.config(image=no_image)
        self.preview_image.image = no_image
        self.preview_text.config(text="Time: No image")

        self.dual_scale.set_limits(1, 10)

        if self.trimming_window_enabled:
            self.trimming_window.place_forget()
            self.trimming_window_enabled = False

        self.preview_video_enabled = False
        self.preview_button.config(bg='SystemButtonFace', activebackground='SystemButtonFace')

    def export_video(self):
        def save_video():
            try:
                self.root.focus_set()

                first_frame = np.array(self.images_copy[0])
                size = (first_frame.shape[1], first_frame.shape[0])
                processed_frames = 0
                total_frames = len(self.images_copy)

                progress_frame = tk.Frame(self.root, bg="#C0C0C0")
                progress_frame.place(relx=0.5, rely=0.5, anchor="center")

                progress_label = tk.Label(progress_frame, text=f"Progress: {processed_frames}/{total_frames}", bg="#C0C0C0", font=("arial", 12))
                progress_label.pack(anchor="center")

                progress_bar = ttk.Progressbar(progress_frame,orient="horizontal",length=300,mode="determinate")
                progress_bar.pack(pady=5)
                progress_bar.config(variable=processed_frames , maximum=total_frames)
                progress_bar.start()

                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                video = cv2.VideoWriter(output_file,fourcc,self.fps, size)

                for frame in self.images_copy:
                    frame_array = np.array(frame)
                    if len(frame_array.shape) == 2:
                        frame_array = cv2.cvtColor(frame_array, cv2.COLOR_GRAY2BGR)
                    video.write(frame_array)
                    processed_frames += 1
                    progress_label.config(text=f"Progress: {processed_frames}/{total_frames}")
                    progress_bar.update()

                video.release()
                progress_bar.stop()
                progress_frame.destroy()
                print(f"Successfully saved video to {output_file}")
                messagebox.showinfo("Success", "Video saved successfully!")
                self.root.focus_set()
            except Exception as e:
                print(f"Error in save_video: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to save video: {str(e)}"))

        start, end = self.dual_scale.get_range()

        output_file = filedialog.asksaveasfilename(
            initialdir=self.output_dir,
            initialfile=f"video_({end-start+1})frames.mp4",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4")]
        )

        if not output_file:
            self.root.focus_set()
            return

        self.fps = int(self.fps_entry.get())

        self.images_copy = self.original_images.copy()
        self.timestamps_copy = self.timestamps.copy()

        self.images_copy = self.images_copy[start-1: end]
        self.timestamps_copy = self.timestamps_copy[start-1:end]

        Thread(target=save_video, daemon=True).start()

    def create_thumbnails(self,images:list[Image.Image]):
        index = 1
        if len(self.thumbnail_frames) > 0 :
            index = len(self.thumbnail_frames)+1
        for image in images:
            image = ImageTk.PhotoImage(image.resize(self.thumbnail_size), Image.LANCZOS)
            # self.thumbnail_cache[index] = image

            thumbnail_frame = tk.Frame(self.thumbnail_container)

            thumbnail = tk.Label(thumbnail_frame, image=image)
            thumbnail.image = image
            thumbnail.pack(side="top", pady=(5, 0))

            timestamp = tk.Label(thumbnail_frame, text=str(index), font=("Arial" , 12) , justify="center")
            timestamp.pack(side="bottom")

            self.thumbnail_frames.append(thumbnail_frame)

            thumbnail_frame.pack(side="left" , padx=5)
            thumbnail.bind("<Button-1>", lambda e, i=index-1 : self.thumbnail_clicked(i))
            index+=1

    def thumbnail_canvas_xview(self , *args):
        self.thumbnail_canvas.xview(*args)

    def thumbnail_clicked(self , index:int):
        self.image_index = index
        self.update_preview(self.image_index)
        self.update_thumbnails_position(self.image_index)

    def update_thumbnails_position(self , index:int):
        frame = self.thumbnail_frames[index]
        x = frame.winfo_x()
        container_width = self.thumbnail_container.winfo_width()
        if container_width > 0:
            scroll_pos = x / container_width
            self.thumbnail_canvas.xview_moveto(scroll_pos)

    def previous_button_clicked(self , event = None):
        if len(self.images) > 0:
            self.image_index-=1
            if self.image_index < 0 :
                self.image_index = len(self.images)-1
            self.update_preview(self.image_index)
            self.update_thumbnails_position(self.image_index)

    def next_button_clicked(self , evemt = None):
        if len(self.images) > 0:
            self.image_index +=1
            if self.image_index > len(self.images) -1:
                self.image_index = 0
            self.update_preview(self.image_index)
            self.update_thumbnails_position(self.image_index)

    def theme_selected(self , event=None):
        theme_name = self.theme_combobox.get()
        theme = self.themes[theme_name]
        self.apply_theme(theme)

    def apply_theme(self, theme):
        self.settings_frame.config(bg=theme['settings_frame'])
        self.preview_frame.config(bg=theme['preview_frame'])
        self.thumbnail_frame.config(bg = theme["thumbnail_frame"])
