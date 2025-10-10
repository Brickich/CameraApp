import gxipy as gx

from src.camera import Camera , CameraControl
from src.gui import GUI , CameraControlPane

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

        self.camera_control_panes:dict[Camera , CameraControlPane] = {}
        self.camera_canvas_map:dict[Camera , Canvas] = {}
        self.camera_fps_map:dict[Camera , Label] = {}


 

        self.gui = GUI(root=self.root, cameras_count= len(self.cameras))

        for i, camera in enumerate(self.cameras):
            canvas = self.gui.canvases[i]
            fps_label = self.gui.fps_labels[i]
            self.camera_control_panes[camera] = CameraControlPane(self.root , camera , canvas)
            self.camera_canvas_map[camera] = canvas
            self.camera_fps_map[camera] = fps_label

        self.configure_control_frame()



    def start_camera_trigger(self, camera:Camera , trigger_source:gx.GxTriggerSourceEntry): 
        camera.trigger_start_time = None
        camera.trigger_event.clear()
        camera.images.clear()
        camera.timestamps.clear()
        camera.capture_event.set()

        if camera.is_recording:
            camera.switch_recording()

        camera.trigger_settings(trigger_source)

        if not camera.is_recording():
            camera.switch_recording()

        camera.print_settings()

        if trigger_source == gx.GxTriggerSourceEntry.SOFTWARE:
                camera.TriggerSoftware.send_command()

        while not camera.trigger_event.is_set():
            try:
                if camera.trigger_start_time:
                    if time.perf_counter() - camera.trigger_start_time > camera.timeout:
                        print("break due to timeout")
                        break
                
                result = camera.image_handling()  
                if result is None:
                    continue


                if camera.type=="MER" and camera.captured_frames ==0:
                    camera.TriggerMode.set("OFF")

                image, timestamp = result
                camera.images.append(image)

                if camera.captured_frames == 0 :
                    camera.timestamps.append(timestamp)
                    camera.trigger_start_time = time.perf_counter()
                    camera.captured_frames+=1
                    continue
                else:
                    camera.timestamps.append(int(timestamp - camera.timestamps[0])/1000)
                    
                    if camera.captured_frames+1 >= camera.quantity_of_frames:
                        break

                    camera.captured_frames+=1

            except Exception as e:
                pass

        if camera.is_triggered:
            camera.timestamps[0] = 0.0
            print(f"Total frames recorded: {camera.captured_frames + 1}")
            self.switch_camera_trigger(camera, trigger_source)


    def stop_camera_trigger(self , camera:Camera , trigger_source:gx.GxTriggerSourceEntry):
        camera.trigger_event.set()
        camera.capture_event.clear()

        if len(camera.images) > 4:
            self.check_trigger_completion(camera)
        else:
            print("not enough images")

        camera.captured_frames = 0
        camera.quantity_of_frames = None

        if camera.is_recording:
            camera.switch_recording()

        camera.default_settings()
 
        if not camera.is_recording:
            camera.switch_recording()




    def display_images(self , camera:Camera , canvas:Canvas):

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


            resized_image = image.resize((new_width , new_height) , Image.Resampling.LANCZOS)
            photo_image = ImageTk.PhotoImage(resized_image)

            canvas.delete("all")
            canvas.create_image(canvas_width//2 , canvas_height//2 , image = photo_image , anchor = "center")

            canvas._photo_image = photo_image

        while not camera.capture_event.is_set():
            try:
                result = camera.image_handling()
                if result is None:
                    continue
                image, _ = result
                self.last_image = image
                self.root.after(0 , lambda: update_canvas(image , canvas))
            except Exception as e:
                continue

    
    def switch_camera_trigger(self, camera:Camera , trigger_source:gx.GxTriggerSourceEntry ):
        if not camera.is_recording:
            messagebox.showerror("Error" , "Turn ON the camera")
            return

        camera.switch_trigger()

        if not camera.is_triggered:
            self.stop_camera_trigger(camera, trigger_source)
            return

        trigger_thread = Thread(target=lambda: self.start_camera_trigger(camera, trigger_source))
        trigger_thread.start()
        
    def check_trigger_completion(self, camera:Camera , dir):
        dir_path = check_dir(dir)
        Thread(target=lambda :camera.save_images(dir_path) ,daemon=True).start()


    def configure_control_frame(self):
        self.gui.play_button.bind("<Button-1>" , lambda e : self.play_button_click())

    


    def apply_settings(self, camera:Camera , control_pane:CameraControlPane):
        if camera.is_triggered:
            messagebox.showinfo("Info" , "Can't change settings\nCamera in trigger mode")
            return
        preset = control_pane.settings_frame.sliders_frame.get_preset()
        trigger_preset = preset


        default_preset = preset.copy()
        default_preset['fps'] = 24.0

        preview_preset = default_preset.copy()
        preview_preset["exposure_time"] = 40000

        camera.preset_manager.change_preset("default" , default_preset)
        camera.preset_manager.change_preset("trigger" , trigger_preset)
        camera.preset_manager.change_preset("preview" , preview_preset)

        was_recording = camera.is_recording
        if was_recording:
            camera.switch_capture()

        camera.apply_preset(trigger_preset)
        
        fps_label = self.camera_fps_map[camera]
        fps_label.configure(text=f"FPS : {camera.FrameRate.get()}")

        camera.print_settings()
        camera.apply_preset(default_preset)

        if was_recording:
            camera.switch_capture()

    def play_button_click(self ):
        self.gui.play_button_click()
        for camera, canvas in self.camera_canvas_map.items():
            camera.switch_capture()
            if camera.is_recording:
                Thread(target=self.display_images, args=(camera , canvas) , daemon=True ).start()




    def switch_preview(self):
        pass


    
    def run(self):
        self.root.mainloop()
    
    def destroy(self):
        for camera in self.camera_control.cameras:
            camera.close()
        self.root.destroy()




def check_dir(dir="output", basename = None) -> str:
    print(basename)
    dirPath = dir + "/"
    i = 0
    if not os.path.exists(dir):
        print(f"Directory ---> {str(dir)} does not exist")
        os.mkdir(dir)
    while os.path.exists(dirPath + "_" + str(i)):
        i += 1
    destPath = dirPath +f"{basename if basename else ""}" + "_" + str(i)
    print(f"Results directory ---> {destPath}")
    os.makedirs(destPath)

    return destPath
  
if __name__ == "__main__":
    camera_app = CameraApp()

    camera_app.run()
    