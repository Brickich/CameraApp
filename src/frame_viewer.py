import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import glob
import threading
import time
import cv2
import numpy as np
from enum import Enum

class VideoDirection(Enum):
    forward = 0
    backward = 1

class FrameViewer:
    def __init__(self, root, cameras_amount: int):
        self.root = root
        self.cameras_amount = cameras_amount
        

    
        
        self.camera_index = None
        self.camera_attributes = []
        self.camera_buttons = []
        
        self.is_playing = False
        self.video_direction = VideoDirection.forward
        self.fps = 30
        self.video_thread = None
        
        self.image_cache = {}
        self.current_frame_size = None
        
        self.main_window = tk.PanedWindow(self.root, orient="horizontal")
        
        self.right_panel = tk.Frame(self.main_window, bg="#f0f0f0", width=200)
        self.frame_panel = tk.Frame(self.main_window)
        
        self.main_window.add(self.right_panel, stretch="never")
        self.main_window.add(self.frame_panel, stretch="always")
        
        self.choose_camera_frame = tk.Frame(self.right_panel)
        self.all_cameras_button = tk.Button(
            self.choose_camera_frame, text="All cameras", font=("Segoe UI", 12),
            fg="white", bg="green", command=self.show_all_images
        )
        self.all_cameras_button.pack(anchor="center", side="top", pady=5)
        
        for i in range(cameras_amount):
            self.camera_attributes.append({
                "label": None,
                "canvas": None, 
                "images": [],
                "timestamps": [],
                "current_index": 0,
                "current_photo": None,
            })
            
            button = tk.Button(
                self.choose_camera_frame,
                command=lambda i=i: self.change_current_camera_index(i),
                text=f"Camera {i+1}", bg="white", fg="black", font=("Segoe UI", 10)
            )
            button.pack(side="top", anchor="center", pady=2)
            self.camera_buttons.append(button)
        
        self.choose_camera_frame.pack(side="top", fill="x", padx=5, pady=5)
        
        self.create_camera_frames()
        self.button_frame = self.__init_button_frame()
        
        self.frame_panel.pack(side="left", fill="both", expand=True)
        self.right_panel.pack(side="right", fill="y")
        
        self.root.bind("<Right>", lambda e: self.next_button_click())
        self.root.bind("<Left>", lambda e: self.previous_button_click())
        self.root.bind("<space>", lambda e: self.toggle_video_playback())
        
        
        self.button_frame.pack(side="top", fill="x", pady=5)
        # self.enable()
        # self.load_test_images()
        
    def create_camera_frames(self):
        for i in range(self.cameras_amount):
            canvas = tk.Canvas(self.frame_panel, bg="black", highlightthickness=0)
            canvas.pack(fill="both", expand=True, padx=5, pady=5)
            
            timestamp_label = tk.Label(
                canvas, font=("Segoe UI", 10), 
                text="Timestamp: None", bg="black", fg="white"
            )
            
            self.camera_attributes[i]["canvas"] = canvas
            self.camera_attributes[i]["label"] = timestamp_label
            self.camera_attributes[i]["timestamp_label"] = timestamp_label


    def _get_scaled_image(self, image, target_width, target_height):
        cache_key = (id(image), target_width, target_height)
        
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        img_width, img_height = image.size
        img_ratio = img_width / img_height
        target_ratio = target_width / target_height
        
        if target_ratio > img_ratio:
            new_height = target_height
            new_width = int(new_height * img_ratio)
        else:
            new_width = target_width
            new_height = int(new_width / img_ratio)
        
        if new_width != img_width or new_height != img_height:
            scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            scaled_image = image
        
        photo_image = ImageTk.PhotoImage(scaled_image)
        self.image_cache[cache_key] = photo_image
        
        if len(self.image_cache) > 50:
            oldest_key = next(iter(self.image_cache))
            del self.image_cache[oldest_key]
        
        return photo_image


    def _update_single_frame(self, camera_index):
        attr = self.camera_attributes[camera_index]
        
        if not attr["images"]:
            return
            
        index = attr["current_index"]
        canvas = attr["canvas"]
        label = attr["timestamp_label"]
        
        if 0 <= index < len(attr["images"]):
            image = attr["images"][index]
            
            canvas = attr["canvas"]
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()


            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = canvas.winfo_reqwidth()
                canvas_height = canvas.winfo_reqheight()
    
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = image.width
                canvas_height = image.height


            image_ratio = image.width / image.height
            canvas_ratio = canvas_width / canvas_height

            if canvas_ratio > image_ratio:
                new_height = canvas_height
                new_width = int(new_height * image_ratio)
            else:
                new_width = canvas_width
                new_height = int(new_width / image_ratio)

                                                                
            resized_image = image.resize((new_width , new_height))
            photo_image = ImageTk.PhotoImage(resized_image)

            canvas.delete("all")
            canvas.create_image(canvas_width//2 , canvas_height//2 , image = photo_image , anchor = "center")

            canvas._photo_image = photo_image

            attr["current_photo"] = photo_image
            timestamp = attr["timestamps"][index]
            label.configure(text=f"Frame: {index+1} Timestamp: {timestamp}µs")
            
            label.pack(side = "bottom" , anchor = "center")

    # def load_test_images(self):
    #     images = []
    #     image_paths = glob.glob("assets/*.png")[:50] 
        
    #     for img_path in image_paths:
    #         try:
    #             image = Image.open(img_path)
    #             if image.mode != 'RGB':
    #                 image = image.convert('RGB')
    #             images.append(image)
    #         except Exception as e:
    #             print(f"Error loading image {img_path}: {e}")
        
    #     if not images:
    #         for i in range(10):
    #             img = Image.new('RGB', (self.camera_width, self.camera_height), 
    #                           color=(i * 25, i * 15, i * 35))
    #             images.append(img)
        
    #     processed_images = self.preprocess_images(images)
    #     timestamps = list(range(len(processed_images)))
        
    #     for i in range(len(self.camera_attributes)):
    #         self.load_images(i, processed_images, timestamps)
    #     self.show_all_images()
    
    def load_images(self, camera_index: int, images: list, timestamps: list):
        if not images:
            return
        
        attr = self.camera_attributes[camera_index]
        attr["images"] = images
        attr["timestamps"] = timestamps
        attr["current_index"] = 0
        
        
        self.camera_index = None
        self._update_single_frame(camera_index)
    
    def update_frame(self, attr):
        camera_index = self.camera_attributes.index(attr)
        self._update_single_frame(camera_index)
    
    def change_current_camera_index(self, index: int):
        self.all_cameras_button.configure(
            bg="white", fg="black", 
            activebackground="white", activeforeground="black"
        )
        self.camera_index = index
        
        for attr in self.camera_attributes:
            attr["canvas"].pack_forget()
        
        attr = self.camera_attributes[index]
        attr["canvas"].pack(fill="both", expand=True, padx=5, pady=5)
        self._update_single_frame(index)
        
        for i, button in enumerate(self.camera_buttons):
            if i == index:
                button.configure(fg="white", bg="green", 
                               activeforeground="white", activebackground="green")
            else:
                button.configure(fg="black", bg="white", 
                               activeforeground="black", activebackground="white")
    
    def show_all_images(self):
        self.all_cameras_button.configure(
            bg="green", activebackground="green", 
            fg="white", activeforeground="white"
        )
        
        for button in self.camera_buttons:
            button.configure(fg="black", bg="white", 
                           activeforeground="black", activebackground="white")

        for attr in self.camera_attributes:
            attr["canvas"].pack(fill="both", expand=True, padx=5, pady=5)
            self._update_single_frame(self.camera_attributes.index(attr))
        
        self.camera_index = None
    
    def next_button_click(self):
        if self.camera_index is not None:
            attr = self.camera_attributes[self.camera_index]
            if attr["images"]:
                attr["current_index"] = (attr["current_index"] + 1) % len(attr["images"])
                self._update_single_frame(self.camera_index)
        else:
            for i, attr in enumerate(self.camera_attributes):
                if attr["images"]:
                    attr["current_index"] = (attr["current_index"] + 1) % len(attr["images"])
                    self._update_single_frame(i)
    
    def previous_button_click(self):
        if self.camera_index is not None:
            attr = self.camera_attributes[self.camera_index]
            if attr["images"]:
                attr["current_index"] = (attr["current_index"] - 1) % len(attr["images"])
                self._update_single_frame(self.camera_index)
        else:
            for i, attr in enumerate(self.camera_attributes):
                if attr["images"]:
                    attr["current_index"] = (attr["current_index"] - 1) % len(attr["images"])
                    self._update_single_frame(i)
    
    def toggle_video_playback(self):
        if self.is_playing:
            self.stop_video()
        else:
            self.start_video()
    
    def start_video(self):
        if self.is_playing:
            return
            
        self.is_playing = True
        self.video_thread = threading.Thread(target=self._video_loop, daemon=True)
        self.video_thread.start()
        
        self.video_forward_button.configure(bg="red", text="⏸️")
        self.video_backward_button.configure(state="disabled")
    
    def stop_video(self):
        self.is_playing = False
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=1.0)
        
        self.video_forward_button.configure(bg="green", text="►►")
        self.video_backward_button.configure(state="normal")
    
    def _video_loop(self):
        while self.is_playing:
            start_time = time.time()
            
            if self.video_direction == VideoDirection.forward:
                self.root.after(0 , lambda : self.next_button_click())
            elif self.video_direction == VideoDirection.backward:
                self.root.after(0 , lambda : self.previous_button_click())
            
            elapsed = time.time() - start_time
            sleep_time = max(0, 1.0 / self.fps - elapsed)
            time.sleep(sleep_time)
    
    def set_video_direction_forward(self):
        self.video_direction = VideoDirection.forward
        self.video_forward_button.configure(bg="green")
        self.video_backward_button.configure(bg="lightgray")
    
    def set_video_direction_backward(self):
        self.video_direction = VideoDirection.backward
        self.video_forward_button.configure(bg="lightgray")
        self.video_backward_button.configure(bg="green")
    
    def set_fps(self, value):
        self.fps = int(value)
    
    def __init_button_frame(self):
        button_frame = tk.Frame(self.right_panel)
        
        nav_frame = tk.Frame(button_frame)
        self.previous_button = tk.Button(nav_frame, text="◄", bg="green", font=("Arial", 14),
                                      command=self.previous_button_click)
        self.next_button = tk.Button(nav_frame, text="►", bg="green", font=("Arial", 14),
                                  command=self.next_button_click)
        
        self.previous_button.grid(row=0, column=0, padx=2, pady=2)
        self.next_button.grid(row=0, column=1, padx=2, pady=2)
        nav_frame.grid(row=0, column=0, columnspan=2, pady=5)
        
        video_frame = tk.Frame(button_frame)
        self.video_backward_button = tk.Button(video_frame, text="◄◄", bg="lightgray", font=("Arial", 12),
                                            command=self.set_video_direction_backward)
        self.video_forward_button = tk.Button(video_frame, text="►►", bg="green",
                                            font=("Arial", 12),command=self.set_video_direction_forward)
        self.video_backward_button.grid(row=0, column=0, padx=2, pady=2)
        self.video_forward_button.grid(row=0, column=1, padx=2, pady=2)
        video_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        fps_frame = tk.Frame(button_frame)
        tk.Label(fps_frame, text="FPS:", font=("Segoe UI", 9)).pack(side="left")
        self.fps_scale = tk.Scale(fps_frame, from_=1, to=60, orient="horizontal",
                               command=self.set_fps, length=120, showvalue=True)
        self.fps_scale.set(self.fps)
        self.fps_scale.pack(side="left", fill="x", expand=True)
        fps_frame.grid(row=2, column=0, columnspan=2, pady=5, padx=5, sticky="ew")
        
        self.play_button = tk.Button(button_frame, text="⏯️ Play", bg="lightblue",
                                   font=("Arial", 11),command=self.toggle_video_playback)
        self.play_button.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")

        control_frame = tk.Frame(button_frame)
        camera_app_image = ImageTk.PhotoImage(Image.open("assets/camera.png").resize((30, 20)))
        self.camera_app_button = tk.Button(control_frame , image=camera_app_image)
        self.camera_app_button.image = camera_app_image
        self.camera_app_button.pack(side="right", anchor="center" , padx=5 , pady=5)

        self.delete_button = tk.Button(control_frame , text="Delete Images" , font=("Segue UI" , 12) ,
                                     bd=2 , relief="raised" , bg="white" , fg="black" , command=self.delete_images)
        self.delete_button.pack(side="left" , padx=5 , pady=5)

        self.export_video_button = tk.Button(control_frame , text="Export Video" , font=("Segue UI" , 12) , bg="white" ,
                                       fg="black" , bd=2 , relief="sunken" , command=self.export_video)
        self.export_video_button.pack(side="bottom" , padx=5 , pady=5)

        control_frame.grid(row=4 , columnspan=2  ,padx=5 , pady=5 , sticky="ew")
        
        return button_frame
    
    def delete_images(self):
        for attr in self.camera_attributes:
            attr["images"].clear()
            attr["timestamps"].clear()
            attr["current_index"] = 0
            if attr["canvas"]:
                no_image = Image.open("assets/no_image.png").resize((400,300))
                attr["images"].append(no_image) 
                attr["timestamps"].append("None")
                attr["canvas"].delete("all")
                self._update_single_frame(self.camera_attributes.index(attr))
            
        self.show_all_images()

    def export_video(self):
        def save_video(images:list[Image.Image] , fps , output_file):
            if not images:
                return
                
            size = images[0].size
            fourcc_codes = ['mp4v', 'avc1', 'X264', 'MJPG']
            video = None
            for codec in fourcc_codes:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    video = cv2.VideoWriter(output_file, fourcc, fps, size)
                    if video.isOpened():
                        break
                    else:
                        video = None
                except Exception as e:
                    video = None

            if video is None:
                print("Cannot initialize codec.")
                return

            for image in images:
                frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                video.write(frame)
            video.release()

        fps = self.fps_scale.get()
        for i, attr in enumerate(self.camera_attributes):
            images = attr["images"]
            if not images:
                continue
            output_file = filedialog.asksaveasfilename(
                filetypes=[("MP4 files", "*.mp4")], 
                defaultextension=".mp4",
                initialfile=f'camera{i+1}_frames{len(images)}', 
                initialdir="output/Camera{i+1}"
            )
            if not output_file:
                continue
            threading.Thread(target=save_video, args=(images, fps, output_file), daemon=True).start()

    def enable(self):
        self.main_window.pack(fill="both", expand=True)

# if __name__ == "__main__":
#     root = tk.Tk()
#     root.title("High-Speed Camera Viewer - Optimized")
#     root.geometry("1200x800")
    
#     app = FrameViewer(root, cameras_amount=4)
#     root.mainloop()