import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
from .video_utils import VideoEditor
from .camera import Camera
import time
import os
from threading import Thread, Event, Lock
import queue

IMAGES = {
    'play_pause': ["assets/play_button.png", "assets/pause_button.png"],
    'white_balance': "assets/white_balance.png",
    'crosshair': "assets/crosshair.png",
    'save': "assets/save.png",
    'no_photo': "assets/no_image.png",
    'flip_h': "assets/flip_h.png",
    'flip_v': "assets/flip_v.png",
    'rotate_right': "assets/rotate_to_right.png",
    'rotate_left': "assets/rotate_to_left.png"
} 

class GUI:
    def __init__(self, root: tk.Tk = None):
        self.root = root
        self.init_variables()
        self.init_gui()

    def init_variables(self):
        self.play_pause_index = 0 
        self.camera = Camera()
        self.image_frame = None
        self.output_dir = "output"
        self.capturing_event = Event()
        self.saving_event = Event()
        self.saving_image_queue = queue.Queue(maxsize=25)
        self.capturing_image_queue = queue.Queue(maxsize=3)
        self.image_lock = Lock()
        self.crosshair_enabled = False
        self.flip_h_enabled = False
        self.flip_v_enabled = False
        self.image_angle = 0
        self.frames_data = [] 
        self.trigger_start_time = None 
        self.trigger_time = 1000

    def get_image_from_camera(self):
        while not self.capturing_event.is_set():
            try:
                image = self.camera.get_RGB_image()
                if not image:
                    continue
                    
                if self.image_angle != 0:
                    image = image.rotate(self.image_angle)
                if self.flip_v_enabled:
                    image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                if self.flip_h_enabled:
                    image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    
                try:
                    with self.image_lock:
                        if self.camera.is_triggered and self.trigger_start_time is not None:
                            image_copy = image.copy()
                            timestamp = round(time.perf_counter() - self.trigger_start_time, 4)
                            try:
                                self.saving_image_queue.put((image_copy, timestamp))
                            except queue.Full:
                                print("Warning: Saving queue is full, skipping frame")
                                
                        self.capturing_image_queue.put(image)
                except queue.Full:
                    time.sleep(0.01)
                    
            except Exception as e:
                print(f"Error in get_image_from_camera: {str(e)}")
                time.sleep(0.1)

    def update_image_frame(self):
        while not self.capturing_event.is_set():
            try:
                image = self.capturing_image_queue.get(timeout=0.1)
                if self.crosshair_enabled:
                    image = self.add_crosshair(image)
                self.root.after(0, self.update_frame, ImageTk.PhotoImage(image))
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in update_image_frame: {str(e)}")
                time.sleep(0.1)
                
    def update_frame(self, image: ImageTk.PhotoImage):
        self.image_frame.config(image=image)
        self.image_frame.image = image

        
    def save_images_to_array(self):
        while not self.saving_event.is_set():
            try:
                image, timestamp = self.saving_image_queue.get(timeout=0.1) 
                with self.image_lock:
                    self.frames_data.append((image, timestamp))
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in save_images_to_array: {str(e)}")
                continue

    def switch_camera_recording_mode(self):
        self.camera.switch_recording()
        self.play_pause_index = 1 - self.play_pause_index
        self.on_off_button.config(image=self.play_pause_images[self.play_pause_index])
        self.start_camera_stream() if self.camera.is_recording else self.stop_camera_stream()

    def switch_camera_trigger_mode(self):
        try:
            if not self.camera.is_recording:
                raise Exception("Turn ON the camera")

            self.camera.switch_trigger()
            if self.camera.is_triggered:
                self.saving_event.clear()
                self.frames_data.clear() 
                self.trigger_start_time = time.perf_counter() 
                self.save_images_thread = Thread(target=self.save_images_to_array, daemon=True)
                self.save_images_thread.start()
                self.root.after(self.trigger_time, lambda: [self.saving_event.set(), self.camera.switch_trigger()])
                self.root.after(self.trigger_time+1000, lambda: self.check_completion())
            else:
                self.saving_event.set()
                self.trigger_start_time = None

        except Exception as e:
            messagebox.showerror("Error", f"{str(e)}")
            return

    def check_completion(self):
        if not self.saving_image_queue.empty():
            print(f"Waiting for queue to empty. Queue size: {self.saving_image_queue.qsize()}")
            self.root.after(2000, self.check_completion)
        elif not self.frames_data:
            print("No frames were saved")
            messagebox.showinfo("Info", "There's no saved images in memory")
            return
        else:
            print(f"Trigger completed. Total frames saved: {len(self.frames_data)}")
            self.root.after(1000, self.open_editor)

    def open_editor(self):
        editor_window = tk.Toplevel()
        output_dir = check_dir(self.output_dir)
        VideoEditor(root=editor_window, frames_data=self.frames_data, output_dir=output_dir)
        self.frames_data.clear() 

    def start_camera_stream(self):
        self.capturing_event.clear()
        self.capture_image_thread = Thread(
            target=self.get_image_from_camera, daemon=True
        )
        self.update_frame_thread = Thread(target=self.update_image_frame, daemon=True)
        self.capture_image_thread.start()
        self.update_frame_thread.start()

    def stop_camera_stream(self):
        self.capturing_event.set()

    def init_gui(self):
        self.camera_settings_frame = None
        self.init_buttons()
        self.init_image_frame()


    def init_image_frame(self):
        self.image_frame = tk.Label(self.root , bd=0)
        self.image_frame.place(anchor="center" ,relx=0.5 , rely=0.575)

        frame_default_image = ImageTk.PhotoImage(Image.open(IMAGES['no_photo']))
        self.image_frame.config(image=frame_default_image)
        self.image_frame.image = frame_default_image
        self.image_frame.lower()

    def init_buttons(self):
        button_size = (50, 50)
        self.play_pause_images = [
            ImageTk.PhotoImage(Image.open(img).resize(button_size))
            for img in IMAGES['play_pause']
        ]
        
        self.white_balance_image = ImageTk.PhotoImage(Image.open(IMAGES['white_balance']).resize(button_size))
        self.crosshair_image = ImageTk.PhotoImage(Image.open(IMAGES['crosshair']).resize(button_size))
        self.flip_h_image = ImageTk.PhotoImage(Image.open(IMAGES['flip_h']).resize(button_size))
        self.flip_v_image = ImageTk.PhotoImage(Image.open(IMAGES['flip_v']).resize(button_size))
        self.rotate_right_image = ImageTk.PhotoImage(Image.open(IMAGES['rotate_right']).resize(button_size))
        self.rotate_left_image = ImageTk.PhotoImage(Image.open(IMAGES['rotate_left']).resize(button_size))

        buttons_frame = tk.LabelFrame(self.root, padx=5, pady=5, bg="#A9A9A9")
        buttons_frame.place(relx=0, rely=0, relwidth=0.45, relheight=0.15)

        switch_frame = tk.LabelFrame(self.root, padx=5, pady=5, bg="#A9A9A9")
        switch_frame.place(relx=0.45, rely=0, relwidth=0.55, relheight=0.15)

        self.on_off_button = tk.Button(
            buttons_frame,
            image=self.play_pause_images[self.play_pause_index],
            command=self.switch_camera_recording_mode,
        )
        self.wbalance_button = tk.Button(
            buttons_frame,
            image=self.white_balance_image,
            command=self.switch_wbalance_button,
        )
        self.crosshair_button = tk.Button(
            buttons_frame, 
            image=self.crosshair_image, 
            command=self.switch_crosshair
        )

        self.flip_h_button = tk.Button(
            buttons_frame, 
            image=self.flip_h_image, 
            command=self.flip_h
        )
        self.flip_v_button = tk.Button(
            buttons_frame, 
            image=self.flip_v_image, 
            command=self.flip_v
        )
        self.rotate_right_button = tk.Button(
            buttons_frame, 
            image=self.rotate_right_image, 
            command=self.rotate_right
        )
        self.rotate_left_button = tk.Button(
            buttons_frame, 
            image=self.rotate_left_image, 
            command=self.rotate_left
        )

        self.on_off_button.pack(side="left", pady=10, padx=5, anchor="center")
        self.wbalance_button.pack(side="left", pady=10, padx=5, anchor="center")
        self.crosshair_button.pack(side="left", pady=10, padx=5, anchor="center")
        self.flip_h_button.pack(side="left", pady=10, padx=5, anchor="center")
        self.flip_v_button.pack(side="left", pady=10, padx=5, anchor="center")
        self.rotate_left_button.pack(side="left", pady=10, padx=5, anchor="center")
        self.rotate_right_button.pack(side="left", pady=10, padx=5, anchor="center")

        self.settings_button = tk.Button(
            switch_frame,
            text="Settings",
            command=self.switch_camera_settings_window,
        )
        self.trigger_button = tk.Button(
            switch_frame, text="Trigger", command=self.switch_camera_trigger_mode
        )
        self.settings_button.pack(side="right", anchor="center", padx=25, pady=(25, 0))
        self.trigger_button.pack(side="left", anchor="center", padx=25, pady=25)

    def switch_camera_settings_window(self):
        if self.camera_settings_frame is not None:
            self.camera_settings_frame.place_forget()
            self.camera_settings_frame = None
        else:
            self.camera_settings_frame = tk.LabelFrame(
                self.root, bd=2, relief=tk.SOLID, padx=2.5, pady=2.5, bg="silver"
            )

            width_slider, _ = add_slider_with_entry(
                self.camera_settings_frame,
                "Image Width",
                64,
                1440,
                row=0,
                initial_value=800,
                inc=8,
            )
            height_slider, _ = add_slider_with_entry(
                self.camera_settings_frame,
                "Image Height",
                4,
                1080,
                row=1,
                initial_value=600,
                inc=2,
            )
            exposure_time_slider, _ = add_slider_with_entry(
                self.camera_settings_frame,
                "Exposure Time",
                1000,
                100000,
                row=2,
                initial_value=10000,
            )
            fps_slider, _ = add_slider_with_entry(
                self.camera_settings_frame, "FPS", 0.1, 100, row=3, initial_value=60
            )
            gain_slider, _ = add_slider_with_entry(
                self.camera_settings_frame, "Gain", 0.0, 24.0, row=4, initial_value=24.0
            )

            def save_parameters():
                try:
                    if self.camera.is_recording:
                        self.camera.cam.stream_off()

                    width = width_slider.get()
                    height = height_slider.get()
                    exposure_time = exposure_time_slider.get()
                    fps = fps_slider.get()
                    gain = gain_slider.get()


                    self.camera.width.set(width)
                    self.camera.height.set(height)
                    self.camera.exposure_time.set(float(exposure_time))
                    self.camera.framerate.set(float(fps))
                    self.camera.gain.set(float(gain))
                    self.camera.settings_implemented = True
                    self.camera.cam.stream_on()
                    print(f"{self.camera.get_settings()}")
                except Exception as e:
                    messagebox.showerror(
                        "Ошибка", f"Ошибка при сохранении файла \n{str(e)}"
                    )

            tk.Button(
                self.camera_settings_frame, text="Сохранить", command=save_parameters
            ).grid(row=7, column=0, columnspan=2, pady=10)

            self.camera_settings_frame.update_idletasks()
            frame_width = self.camera_settings_frame.winfo_reqwidth()
            frame_height = self.camera_settings_frame.winfo_reqheight()

            self.camera_settings_frame.place(x=-frame_width - 5, relx=1.0, rely=0.15)

    def on_closing(self):
        self.capturing_event.set()
        self.saving_event.set()
        self.camera.close()
        self.root.destroy()

    def switch_wbalance_button(self):
        self.camera.switch_white_balance()

    def add_crosshair(self, image: Image.Image) -> Image.Image:
        try:
            img = image.copy()
            draw = ImageDraw.Draw(img)
            width, height = img.size

            line_color = (255, 0, 0)
            draw.line([(0, height / 2), (width, height / 2)], fill=line_color, width=2)
            draw.line([(width / 2, 0), (width / 2, height)], fill=line_color, width=2)
            return img
        except Exception as e:
            print(f"Error : {str(e)}")
        return image

    def switch_crosshair(self):
        self.crosshair_enabled = not self.crosshair_enabled
        print(f"Crosshair {"ON" if self.crosshair_enabled else "OFF"}")

    def rotate_right(self):
        self.image_angle -= 90
        if self.image_angle == -360:
            self.image_angle = 0
        print(f"Rotate right \nCurrent angle = {self.image_angle}")

    def rotate_left(self):
        self.image_angle += 90
        if self.image_angle == 360:
            self.image_angle = 0
        print(f"Rotate left \nCurrent angle = {self.image_angle}")

    def flip_v(self):
        print(f"flipped top/bottom")
        self.flip_v_enabled = not self.flip_v_enabled

    def flip_h(self):
        print(f"flipped left/right")
        self.flip_h_enabled = not self.flip_h_enabled



def add_slider_with_entry(root: tk.Tk, label_text, from_, to, row, initial_value=None, inc=None):
    tk.Label(root, text=label_text , font=("arial" , 11)).grid(row=row, column=0, padx=5, pady=5)

    slider = tk.Scale(root, from_=from_, to=to, orient=tk.HORIZONTAL, resolution=inc)
    slider.grid(row=row, column=1, padx=5, pady=5)
    if initial_value is not None:
        slider.set(initial_value)

    entry = tk.Entry(root, width=10 , font=("arial",11))
    entry.grid(row=row, column=2, padx=5, pady=5)
    entry.insert(0, slider.get())

    def update_entry(*args):
        entry.delete(0, "end")
        entry.insert(0, slider.get())

    def update_slider(event):
        try:
            value = float(entry.get())
            if from_ <= value <= to:
                slider.set(value)
            else:
                messagebox.showerror("Ошибка", "Вы ввели неправильное значение")
                update_entry()
        except ValueError:
            pass
    slider.config(command=update_entry)
    entry.bind("<Return>", update_slider)

    return slider, entry


def check_dir( dir = "output") -> str:
    dirPath = dir + "/"
    i=0
    if os.path.exists(dirPath):
            while os.path.exists(dirPath + "_" + str(i)):
                print(f"Directory ---> {dirPath + "_" + str(i)} is not empty")
                i += 1
            destPath = dirPath + "_" + str(i)
            print(f"Results directory ---> {destPath}")
            os.makedirs(destPath)
    else:
        print(f"Directory ---> {str(dirPath - "/")} does not exist")
    return destPath