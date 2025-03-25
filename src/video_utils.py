import tkinter as tk
from tkinter import ttk
from PIL import Image , ImageTk
from tkinter import filedialog, messagebox
import cv2
from threading import Thread
import numpy as np
import os

class VideoEditor:
    def __init__(self, root:tk.Tk, frames_data: list[tuple[Image.Image, float]] , output_dir : str = "output"):
        self.root = root
        self.output_dir = output_dir
        self.frames_data = frames_data.copy()
        self.current_index = 0
        self.fps = 10
        self.images_copy = []
        self.images_tk =  []
        self.thumbnail_images_tk = []
        self.timestamps = []
        self.convert_images(frames_data)
        self.init_ui()
        
    def convert_images(self, frames_data: list[tuple[Image.Image, float]]):
        thumbnail_size = (160,90)
        
        for i, (img, timestamp) in enumerate(frames_data):
            try:
                img_copy = img.copy()
                self.images_copy.append(img_copy)
                self.images_tk.append(ImageTk.PhotoImage(img_copy))
                self.thumbnail_images_tk.append(ImageTk.PhotoImage(img_copy.resize(thumbnail_size, Image.Resampling.LANCZOS)))
                self.timestamps.append(timestamp)
            except Exception as e:
                print(f"Error converting image {i}: {str(e)}")
                continue
        print(f"Total frames loaded: {len(self.images_tk)}")
        print(f"Total thumbnails created: {len(self.thumbnail_images_tk)}")
            
    def init_ui(self):
        self.root.title("Video Editor")
        self.root.geometry(f"{self.root.winfo_screenwidth()-150}x{self.root.winfo_screenheight()-150}+0+0")
        self.root.config(bg="black")
        self.root.focus_set()
        self.root.bind("<Left>", lambda e: self.handle_previous_button_click())
        self.root.bind("<Right>", lambda e: self.handle_next_button_click())
        
        main_frame = tk.LabelFrame(self.root, background="#696969", borderwidth=2)
        main_frame.pack(expand=True, anchor="center", fill="both", padx=10, pady=(0,10))

        working_space = tk.Frame(main_frame)
        working_space.place(rely=0 , relheight=0.75 , relwidth=1)
        
        settings_panel = tk.LabelFrame(working_space ,relief="solid",bg="#C0C0C0", width=100  , borderwidth=2)
        settings_panel.pack(side="left",fill="y")
        
        self.create_sliders(settings_panel)
        
        preview_container = tk.Frame(working_space, relief="solid", borderwidth=2)
        preview_container.pack(expand=True, side="right", fill="both")
        
        navigation_frame = tk.Frame(preview_container, bg="#C0C0C0")
        navigation_frame.pack(expand=True, fill="both")
        
        prev_button = tk.Button(
            navigation_frame,
            text="◄",
            command=self.handle_previous_button_click,
            font=("arial", 20),
            bg="#4CAF50",
            fg="white"
        )
        prev_button.pack(side="left")
        
        preview_frame = tk.Frame(navigation_frame )
        preview_frame.pack(expand=True, side="left", fill="both")
        
        self.image_label = tk.Label(preview_frame, image=self.images_tk[self.current_index], bg="#C0C0C0")
        self.image_label.pack(expand=True, fill="both")
        
        next_button = tk.Button(
            navigation_frame,
            text="►",
            command=self.handle_next_button_click,
            font=("arial", 20),
            bg="#4CAF50",
            fg="white"
        )
        next_button.pack(side="right")
        
        self.frame_counter = tk.Label(
            preview_container,
            text=f"Кадр: 1 / {str(len(self.images_tk))}\nTime: {self.timestamps[0]}",
            bg="#C0C0C0",
            font=("arial", 12),
            fg="black"
        )
        self.frame_counter.pack(fill="x", pady=5 , anchor="center")
        
        timeline_frame = tk.LabelFrame(main_frame, text="T i m e l i n e", bg="#696969" , font=("arial",12) , fg="white")
        timeline_frame.place(rely=0.75, relheight=0.25, relwidth=1)
        
        self.canvas = tk.Canvas(timeline_frame, bg="#404040", highlightthickness=2)
        scroll_x = tk.Scrollbar(timeline_frame, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(xscrollcommand=scroll_x.set)
        
        scroll_x.pack(side="bottom", fill="x")
        self.canvas.pack(side="top", fill="both", expand=True)
        
        self.frames_container = tk.Frame(self.canvas, bg="#404040")
        self.canvas.create_window((0, 0), window=self.frames_container, anchor="center")
        
        self.add_thumbnails()
        
        self.frames_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
    def add_thumbnails(self):
        self.thumbnail_frames = []
        for widget in self.frames_container.winfo_children():
            widget.destroy()
            
        for i, img in enumerate(self.thumbnail_images_tk):
            try:
                frame = tk.Frame(self.frames_container, bg="#404040", padx=5)
                self.thumbnail_frames.append(frame)
                label = tk.Label(frame, image=img, bg="white", relief="solid", borderwidth=1)
                label.pack()
                tk.Label(frame, text=f"Frame: {i+1} \n Time: {self.timestamps[i]}", fg="white", bg="#404040").pack()
                label.bind("<Button-1>", lambda e, index=i: self.handle_thumbnail_click(index))
                frame.pack(side="left", fill="y")
            except Exception as e:
                print(f"Error creating thumbnail {i}: {str(e)}")
                continue    
            
    def update_scroll_position(self):
        if not self.thumbnail_frames:
            return

        current_frame = self.thumbnail_frames[self.current_index]
        self.root.update_idletasks() 

        x = current_frame.winfo_x()
        width = current_frame.winfo_width()
        canvas_width = self.canvas.winfo_width()

        scroll_offset = (x + width/2 - canvas_width/2) / self.frames_container.winfo_width()
        self.canvas.xview_moveto(max(0, min(scroll_offset, 1)))

    def create_sliders(self, root):
        controls_frame = tk.Frame(root, bg="#C0C0C0")
        controls_frame.pack()
        
        self.trim_start_label = tk.Label(controls_frame, text=f"Start: 1 time: {self.timestamps[0]}", bg="#C0C0C0",font=("arial" , 12))
        self.trim_start_label.pack()
        
        self.trim_start_slider = tk.Scale(
            controls_frame,
            from_=0,
            to=len(self.frames_data)-1,
            orient="horizontal",
            command=self.update_trim_start,
            length=200
        )
        self.trim_start_slider.pack()
        
        self.trim_end_label = tk.Label(controls_frame, text=f"End: {len(self.frames_data)} time: {self.timestamps[-1]}", bg="#C0C0C0", font=("arial" , 12))
        self.trim_end_label.pack()
        
        self.trim_end_slider = tk.Scale(
            controls_frame,
            from_=0,
            to=len(self.frames_data)-1,
            orient="horizontal",
            command=self.update_trim_end,
            length=200
        )
        self.trim_end_slider.set(len(self.frames_data)-1)
        self.trim_end_slider.pack()
        
        def validate_int(input_text):

            if input_text == "" or input_text == "-":
                return True
            try:
                int(input_text)
                return True
            except ValueError:
                return False
            
        validate_command = self.root.register(validate_int)
        
        self.fps_label = tk.Label(controls_frame , width=10 , text="FPS" , bg="#C0C0C0")
        self.fps_label.pack(pady=(5,0))
        
        self.fps_entry = tk.Entry(controls_frame ,justify="center",validate="key",validatecommand=(validate_command , "%P"))
        self.fps_entry.insert(0, f"{self.fps}")
        self.fps_entry.pack()
        
        tk.Button(
            controls_frame,
            text="Export Video",
            command=self.export_video,
            bg="#4CAF50",
            fg="white"
        ).pack(pady=10)               
        
    def update_frame(self, index):
        index = int(index)
        if 0 <= index < len(self.images_tk):
            current_frame = self.images_tk[index]
            self.image_label.config(image=current_frame)
            self.frame_counter.config(text=f"Кадр: {index + 1} / {len(self.images_tk)}\nTime: {self.timestamps[index]}")
        elif index < 0:
            self.current_index = len(self.images_tk) - 1
            self.update_frame(self.current_index)
        elif index >= len(self.images_tk):
            self.current_index = 0
            self.update_frame(self.current_index)
    
    def handle_next_button_click(self):
        self.current_index += 1
        self.update_frame(self.current_index)
        self.update_scroll_position()
        
    def handle_previous_button_click(self):
        self.current_index -= 1
        self.update_frame(self.current_index)
        self.update_scroll_position()
               
    def handle_thumbnail_click(self, index):
        self.current_index = index
        self.update_frame(self.current_index)
        self.update_scroll_position()
        
    def update_trim_start(self, value):
        start = int(value)
        end = int(self.trim_end_slider.get())
        if start > end:
            self.trim_end_slider.set(start)
            self.trim_end_label.config(text=f"End:\n Frame: {start+1} \n Time: {self.timestamps[start]}")
        self.trim_start_label.config(text=f"Start:\n Frame: {start+1} \n Time: {self.timestamps[start]}")

    def update_trim_end(self, value):
        end = int(value)
        start = int(self.trim_start_slider.get())
        if end < start:
            self.trim_start_slider.set(end)
            self.trim_start_label.config(text=f"Start:\n Frame: {end+1} \n Time: {self.timestamps[end]}")
        self.trim_end_label.config(text=f"End:\n Frame: {end+1} \n Time: {self.timestamps[end]}")


    def export_video(self):
        def save_video():
            try:
                self.root.focus_set()
                first_frame = np.array(self.images_copy[0])
                size = (first_frame.shape[1], first_frame.shape[0])
                processed_frames = 0
                total_frames = len(self.images_copy)
                
                
                progress_frame = tk.Frame(self.root, bg="#C0C0C0")
                progress_frame.pack()
                
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
            finally:
                self.images_copy = original_images
                self.timestamps = original_timestamps
                
        def save_images():
            try:
                print(f"Saving {len(self.images_copy)} images to {images_dir}")
                from concurrent.futures import ThreadPoolExecutor
                
                def save_single_image(args):
                    i, (img, timestamp) = args
                    try:
                        img.save(f"{images_dir}/T_{str(i)}   {str(timestamp)}.jpg")
                        if (i + 1) % 10 == 0:
                            print(f"Saved {i + 1}/{len(self.images_copy)} images")
                    except Exception as e:
                        print(f"Error saving image {i}: {str(e)}")
                        
                with ThreadPoolExecutor(max_workers=4) as executor:
                    executor.map(save_single_image, enumerate(zip(self.images_copy, self.timestamps)))
                        
                print(f"Successfully saved images to {images_dir}")
            except Exception as e:
                print(f"Error in save_images: {str(e)}")
          
          
        start = int(self.trim_start_slider.get())
        end = int(self.trim_end_slider.get())
        
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
        
        original_images = self.images_copy.copy()
        original_timestamps = self.timestamps.copy()
        
        self.images_copy = self.images_copy[start:end+1]
        self.timestamps = self.timestamps[start:end+1]
            
        images_dir = os.path.join(self.output_dir, f"images/{end-start+1} frames")
        os.makedirs(images_dir, exist_ok=True)
    
        
        Thread(target=save_video, daemon=True).start()
        Thread(target=save_images, daemon=True).start()
        


            
            
