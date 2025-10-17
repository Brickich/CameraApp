import gxipy as gx

from src.camera import Camera , CameraControl
from src.gui import GUI , SettingsPane
from tkinter import Tk , messagebox , Canvas , Label
from threading import Thread
import time
from PIL import Image , ImageTk
import os


class CameraApp:
    def __init__(self):
        self.root = Tk()
        self.root.geometry(f"{int(self.root.winfo_screenwidth()/2)}x{int(self.root.winfo_screenheight()/2)}")
        self.root.title("Camera Control App")   
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)
        self.camera_control = CameraControl()
        self.cameras:list[Camera] = self.camera_control.cameras

        self.camera_canvas_map:dict[Camera , Canvas] = {}
        self.camera_fps_label_map:dict[Camera , Label ] = {}
        self.camera_settings_map:dict[Camera, SettingsPane] = {}
        self.gui = GUI(self.root , self.cameras)

        self.gui.trigger_button.bind("<Button-1>" , lambda e : self.switch_trigger())
        


        for i, camera in enumerate(self.cameras):
            canvas = self.gui.canvas_frame.canvases[i]
            self.camera_canvas_map[camera] = canvas
            self.camera_settings_map[camera] = self.gui.settings_frame.settings_panes[i]
            self.camera_fps_label_map[camera] = self.gui.canvas_frame.fps_labels[i]
            self.camera_settings_map[camera].play_button.bind("<Button-1>" , lambda e: self.play_button_click(camera))
            self.camera_settings_map[camera].apply_button.bind("<Button-1>" , lambda e : self.apply_settings(camera))
            self.camera_settings_map[camera].trigger_mode_button.bind("<Button-1>" , lambda e : self.trigger_mode(camera) )
            self.camera_settings_map[camera].preview_mode_button.bind("<Button-1>" , lambda e : self.preview_mode(camera))

            
 




    def start_camera_trigger(self, camera:Camera , trigger_source:str): 
        camera.trigger_start_time = None
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
            camera.TriggerSoftware.send_command()

        while not camera.trigger_event.is_set():
            try:
                if camera.trigger_start_time:
                    if time.perf_counter() - camera.trigger_start_time > camera.timeout:
                        print("break due to timeout")
                        break
                
                raw_image = camera.get_raw_image()  
                if raw_image is None:
                    continue


                if camera.type=="MER" and camera.captured_frames ==0:
                    camera.TriggerMode.set("OFF")

                camera.raw_images.append(raw_image)

                if camera.captured_frames == 0 :
                    camera.trigger_start_time = time.perf_counter()
                else:
                    
                    if camera.captured_frames+1 >= camera.QuantityOfFrames:
                        break

                camera.captured_frames+=1

            except Exception as e:
                pass

        if camera.is_triggered:
            for raw_image in camera.raw_images:
                camera.timestamps.append(raw_image.get_timestamp())
                camera.images.append(camera.convert_raw_image(raw_image))

            for i in range(len(camera.timestamps)):
                if i > 0 :
                    new_timestamp = int(camera.timestamps[i] - camera.timestamps[0])/1000
                    camera.timestamps[i] = new_timestamp
            camera.timestamps[0] = 0.0
            print(f"Total frames recorded: {camera.captured_frames + 1}\n")
            self.switch_camera_trigger(camera)


    def stop_camera_trigger(self , camera:Camera):
        camera.trigger_event.set()
        camera.capture_event.clear()

        if len(camera.images) > 4:
            self.check_trigger_completion(camera)
        else:
            print("not enough images")

        camera.captured_frames = 0
        camera.QuantityOfFrames = None

        if camera.is_recording:
            camera.switch_recording()

        camera.default_settings()
 
        if not camera.is_recording:
            camera.switch_recording()

    def switch_camera_trigger(self, camera:Camera ):

        if not camera.is_recording:
            messagebox.showerror("Error" , "Turn ON the camera")
            return
        self.camera_settings_map[camera].on_trigger_switch()
        camera.switch_trigger()

        if not camera.is_triggered:
            self.stop_camera_trigger(camera)
            return

        trigger_source = self.camera_settings_map[camera].trigger_source
        Thread(target=self.start_camera_trigger , args=(camera , trigger_source) , daemon=True).start()



    def display_images(self , camera:Camera):
        
        
        def update_canvas(image:Image.Image , canvas:Canvas):
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


            resized_image = image.resize((new_width , new_height) , Image.Resampling.BOX)
            photo_image = ImageTk.PhotoImage(resized_image)

            canvas.delete("all")
            canvas.create_image(canvas_width//2 , canvas_height//2 , image = photo_image , anchor = "center")

            canvas._photo_image = photo_image
        
        canvas = self.camera_canvas_map[camera]
        while not camera.capture_event.is_set():
            result = camera.image_handling()
            if result is None:
                continue
            image = result
            
            self.root.after(10 , lambda : update_canvas(image , canvas ))

    
    def switch_trigger(self):
        self.gui.switch_trigger_button()
        for camera in self.cameras:
            if not camera.is_recording:
                camera.switch_recording()
            self.switch_camera_trigger(camera)
    
    def trigger_mode(self , camera:Camera):
        if camera.is_triggered:
            messagebox.showinfo("Warning" , "Camera waits for trigger")
            return
        settings = self.camera_settings_map[camera]
        settings.on_trigger_switch()
        was_recording  = camera.is_recording
        if was_recording:
            camera.switch_capture()
            camera.apply_preset(camera.preset_manager.get_preset("default"))
        if was_recording:
            camera.switch_capture()
            Thread(target=self.display_images , args=(camera,) , daemon=True).start()

        

    def preview_mode(self , camera:Camera):
        if camera.is_triggered:
            messagebox.showinfo("Warning" , "Camera waits for trigger")
            return
        settings = self.camera_settings_map[camera]
        settings.on_preview_switch()
        was_recording = camera.is_recording
        if was_recording:
            camera.switch_capture()
            camera.apply_preset(camera.preset_manager.get_preset("preview"))
        if was_recording:
            camera.switch_capture()
            Thread(target=self.display_images , args=(camera,) , daemon=True).start()

        
    def check_trigger_completion(self, camera:Camera):
        dir_path = check_dir(f'output/Camera{self.cameras.index(camera)+1}')
        camera.preset_manager.save_to_file("trigger" , f'{dir_path}/TriggerPreset.json')
        Thread(target=camera.save_images, args=(dir_path,) , daemon=True).start()


    def apply_settings(self, camera:Camera):
        if camera.is_triggered:
            messagebox.showinfo("Info" , "Can't change settings\nCamera in trigger mode")
            return
        preset = self.camera_settings_map[camera].sliders.get_preset()
        trigger_preset = preset


        default_preset = preset.copy()
        default_preset['FrameRate'] = float(24)

        preview_preset = default_preset.copy()
        preview_preset["ExposureTime"] = float(40000)

        camera.preset_manager.change_preset("default" , default_preset)
        camera.preset_manager.change_preset("trigger" , trigger_preset)
        camera.preset_manager.change_preset("preview" , preview_preset)

        was_recording = camera.is_recording
        if was_recording:
            camera.switch_capture()
        print(trigger_preset)
        camera.apply_preset(trigger_preset)

        self.camera_fps_label_map[camera].configure(text=f'FPS : {camera.CurrentFrameRate.get()}')

        camera.print_settings()
        self.trigger_mode(camera)

        if was_recording:
            camera.switch_capture()
            Thread(target=self.display_images , args=(camera,) , daemon=True).start()

    def play_button_click(self , camera:Camera ):
        camera.switch_capture()
        if camera.is_recording:
            Thread(target=self.display_images, args=(camera,) , daemon=True ).start()


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
    