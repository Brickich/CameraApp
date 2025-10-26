import gxipy as gx

from src.camera import Camera , CameraControl
from src.gui import GUI 
import tkinter as tk
from tkinter import messagebox
from threading import Thread 
import time
from PIL import Image , ImageTk
import os


class CameraApp:
    def __init__(self):
        self.root = tk.Tk()

        self.root.geometry(f"{int(self.root.winfo_screenwidth()/2)}x{int(self.root.winfo_screenheight()/2)}")
        self.root.title("Camera Control App")   
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)
        self.camera_control = CameraControl()
        self.cameras:list[Camera] = self.camera_control.cameras

        

        self.gui = GUI(self.root , self.cameras)




        self.camera_attr = {}


        self.gui.frame_viewer_button.bind('<Button-1>' , lambda e : self.enable_frame_viewer())
        self.gui.frame_viewer.camera_app_button.bind("<Button-1>" , lambda e : [self.gui.main_pane.pack(fill="both" , expand=True), self.gui.frame_viewer.main_window.pack_forget()])
        



        for i, camera in enumerate(self.cameras):
            canvas = self.gui.canvas_frame.canvases[i]
            settings_pane = self.gui.settings_frame.settings_panes[i]
            fps_label = self.gui.canvas_frame.fps_labels[i]
            settings_pane.trigger_button.bind("<Button-1>" , lambda e , cam = camera: self.switch_camera_trigger(cam) , add="+")
            
            settings_pane.apply_button.bind("<Button-1>" , lambda e , cam = camera: self.apply_settings(cam) , add="+")
            settings_pane.trigger_mode_button.bind("<Button-1>" , lambda e , cam = camera: self.trigger_mode(cam) , add="+")
            settings_pane.preview_mode_button.bind("<Button-1>" , lambda e , cam = camera : self.preview_mode(cam), add="+")
            settings_pane.play_button.bind("<Button-1>" , lambda e , cam = camera : self.play_button_click(cam) , add="+" )
            self.camera_attr[camera] = {"canvas" : canvas , "settings_pane" : settings_pane , "fps" : fps_label}

            




    def start_camera_trigger(self, camera:Camera , trigger_source:str): 
        camera.trigger_event.clear()
        camera.raw_images.clear()
        camera.images.clear()
        camera.timestamps.clear()
        camera.capture_event.set()


        if camera.is_recording:
            camera.switch_recording()

        camera.trigger_settings(trigger_source)

        if not camera.is_recording:
            camera.switch_recording()

        camera.print_settings()

        if trigger_source == "Software":
            camera.TriggerMode.set("OFF")

        while not camera.trigger_event.is_set():
            try:
                raw_image = camera.get_raw_image()  
                if raw_image is None:
                    continue

                camera.raw_images.append(raw_image)


                if camera.captured_frames+1 >= camera.QuantityOfFrames:
                    break

                camera.captured_frames+=1

            except Exception as e:
                pass

        if camera.is_triggered:
            def process_images():
                for i, raw_image in enumerate(camera.raw_images):
                    if i > 0 :
                        camera.timestamps.append(int(raw_image.get_timestamp() - camera.timestamps[0])/1000)
                    else :
                        camera.timestamps.append(raw_image.get_timestamp())
                    camera.images.append(camera.convert_raw_image(raw_image))
                camera.timestamps[0] = 0.0
                self.switch_camera_trigger(camera)

            Thread(target=process_images , daemon=True).start()
            print(f"{camera.model} recorded: {camera.captured_frames + 1}\n")
            


    def stop_camera_trigger(self , camera:Camera):
        camera.trigger_event.set()
        camera.capture_event.clear()

        camera.captured_frames = 0
        camera.QuantityOfFrames = None
        
        self.check_trigger_completion(camera)
    
        if camera.is_recording:
            camera.switch_recording()

        camera.default_settings()

        if not camera.is_recording:
            camera.switch_recording()

        Thread(target=self.display_images , args=(camera,) , daemon=True).start()


    def switch_camera_trigger(self, camera:Camera ):        
        camera.switch_trigger()
        if not camera.is_triggered:
            self.camera_attr[camera]["settings_pane"].disable_trigger_button()
            self.stop_camera_trigger(camera)
            return

        self.camera_attr[camera]["settings_pane"].enable_trigger_button()
        self.camera_attr[camera]["settings_pane"].on_trigger_switch()
        trigger_source = self.camera_attr[camera]["settings_pane"].trigger_source
        Thread(target=self.start_camera_trigger , args=(camera , trigger_source) , daemon=True).start()



    def display_images(self , camera:Camera):
        
        def update_canvas(image:Image.Image , canvas:tk.Canvas):

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


            resized_image = image.resize((new_width , new_height) , Image.Resampling.NEAREST)
            photo_image = ImageTk.PhotoImage(resized_image)

            canvas.delete("all")
            canvas.create_image(canvas_width//2 , canvas_height//2 , image = photo_image , anchor = "center")

            canvas._photo_image = photo_image
        
        canvas = self.camera_attr[camera]["canvas"]

        while not camera.capture_event.is_set():
            if not canvas.winfo_viewable():
                continue
            result = camera.image_handling()
            if result is None:
                time.sleep(0.01)
                continue
            image = result
            
            self.root.after(20 , lambda : update_canvas(image , canvas ))

    


    def trigger_mode(self , camera:Camera):
        if camera.is_triggered:
            messagebox.showinfo("Warning" , "Camera waits for trigger")
            return
        
        was_recording  = not bool(camera.is_recording)
        if was_recording:
            camera.switch_capture()

        self.camera_attr[camera]["settings_pane"].on_trigger_switch()

        camera.apply_preset(camera.preset_manager.get_preset("default"))
        if was_recording:
            camera.switch_capture()
            Thread(target=self.display_images , args=(camera,) , daemon=True).start()

        

    def preview_mode(self , camera:Camera):
        if camera.is_triggered:
            messagebox.showinfo("Warning" , "Camera waits for trigger")
            return
        
        self.camera_attr[camera]["settings_pane"].on_preview_switch()

        was_recording = bool(camera.is_recording)
        if was_recording:
            camera.switch_capture()
        camera.apply_preset(camera.preset_manager.get_preset("preview"))
        if was_recording:
            camera.switch_capture()
            Thread(target=self.display_images , args=(camera,) , daemon=True).start()

        
    def check_trigger_completion(self, camera:Camera):
        if len(camera.images) > 3:
            dir_path = check_dir(f'output/Camera{self.cameras.index(camera)+1}')
            camera.preset_manager.save_to_file("trigger" , f'{dir_path}/TriggerPreset.json')
            Thread(target=camera.save_images, args=(dir_path,) , daemon=True).start()
            Thread(target=self.gui.frame_viewer.load_images(self.cameras.index(camera) , camera.images , camera.timestamps) , daemon=True).start()
            self.enable_frame_viewer()
            return


    def apply_settings(self, camera:Camera):
        if camera.is_triggered:
            messagebox.showinfo("Info" , "Can't change settings\nCamera in trigger mode")
            return
        preset = self.camera_attr[camera]["settings_pane"].sliders.get_preset()
        trigger_preset = preset


        default_preset = preset.copy()
        default_preset['FrameRate'] = float(24)

        preview_preset = default_preset.copy()
        preview_preset["ExposureTime"] = float(40000)

        camera.preset_manager.change_preset("default" , default_preset)
        camera.preset_manager.change_preset("trigger" , trigger_preset)
        camera.preset_manager.change_preset("preview" , preview_preset)

        was_recording = bool(camera.is_recording)
        if was_recording:
            camera.switch_capture()
        print(trigger_preset)
        camera.apply_preset(trigger_preset)

        self.camera_attr[camera]["fps"].configure(text=f'FPS : {camera.CurrentFrameRate.get()}')

        self.camera_attr[camera]["settings_pane"].on_trigger_switch()

        camera.apply_preset(camera.preset_manager.get_preset("default"))
        if was_recording:
            camera.switch_capture()
            Thread(target=self.display_images , args=(camera,) , daemon=True).start()

    def play_button_click(self , camera:Camera):
        camera.switch_capture()
        if camera.is_recording:
            Thread(target=self.display_images, args=(camera,) , daemon=True ).start()

    def enable_frame_viewer(self):
        self.gui.frame_viewer.enable()
        self.gui.main_pane.pack_forget()

    def run(self):
        self.root.mainloop()
    
    def destroy(self):
        for camera in self.camera_control.cameras:
            camera.close()
        self.root.destroy()




def check_dir(dir="output" ) -> str:
    dirPath = dir + "/"
    i = 0
    if not os.path.exists(dir):
        print(f"Directory ---> {str(dir)} does not exist")
        os.makedirs(dir)
    while os.path.exists(dirPath + "_" + str(i)):
        i += 1
    destPath = dirPath  + "_" + str(i)
    print(f"Results directory ---> {destPath}")
    os.makedirs(destPath)

    return destPath
  
if __name__ == "__main__":
    camera_app = CameraApp()

    camera_app.run()
    