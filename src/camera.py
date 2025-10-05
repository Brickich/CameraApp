import gxipy as gx
import tkinter as tk
from tkinter import messagebox
from gxipy.gxidef import *
from gxipy.ImageFormatConvert import *
from PIL import Image, ImageDraw, ImageTk
from threading import Event , Thread
import time
from .video_editor import VideoEditor
from typing import Any


class Camera:
    def __init__(self , root:tk.Tk, video_editor:VideoEditor):
        super().__init__()
        
        self.video_editor = video_editor
        self.root = root
        self.cam = None
        self.type = None
        self.devices:list[str] = []

        self.is_recording = False
        self.is_triggered = False
        self.isColored = False
        self.SupportColorFormat = False
        self.SupportMonoFormat = False


        self.trigger_start_time = None
        self.captured_frames = 0
        self.quantity_of_frames = 100
        self.timeout = 12.0

        self.trigger_event = Event()
        self.capture_event = Event()
        self.crosshair_enabled = False
        self.flip_h_enabled = False
        self.flip_v_enabled = False
        self.image_angle =0 

        self.images:list[Image.Image] =[]
        self.timestamps:list[float] = []
        
        self.device_manager = gx.DeviceManager()

        self.init_device() 

    def init_device(self):
        try: 
            
            dev_num, dev_info_list = self.device_manager.update_device_list()

            # self.image_process = self.device_manager.create_image_process()
            self.image_convert = self.device_manager.create_image_format_convert()
            if dev_num == 0:
                print("No available devices")
                raise Exception("No available devices")
            else:
                for i in range(dev_num):
                    self.devices.append(dev_info_list[i].get("model_name"))
                self.cam = self.device_manager.open_device_by_index(1)
                
                for i, device in enumerate(self.devices):
                    print(f"Device {i+1}: {device}")  

                model = self.devices[0]
                model = model.lower()
                if "mer2" in model:
                    self.type = "MER2"
                elif "mer" in model:
                    self.type = "MER"
                else:
                    self.type = model.upper()
                
                self.FeatureControl = self.cam.get_remote_device_feature_control()
                self.Width = self.FeatureControl.get_int_feature("Width")
                self.Height = self.FeatureControl.get_int_feature("Height")
                self.ExposureTime = self.FeatureControl.get_float_feature("ExposureTime")
                self.Gain = self.FeatureControl.get_float_feature("Gain")
                self.FrameRate = self.FeatureControl.get_float_feature("AcquisitionFrameRate")
                self.OffsetX = self.FeatureControl.get_int_feature("OffsetX")
                self.OffsetY = self.FeatureControl.get_int_feature("OffsetY")

                self.TriggerMode = self.FeatureControl.get_enum_feature("TriggerMode")
                self.TriggerSource = self.FeatureControl.get_enum_feature("TriggerSource")
                self.TriggerDelay = self.FeatureControl.get_float_feature("TriggerDelay")
                self.TriggerSelector = self.FeatureControl.get_enum_feature("TriggerSelector")
                self.TriggerActivation = self.FeatureControl.get_enum_feature("TriggerActivation")
                # print(self.cam.TriggerActivation.get_range())
                # print(self.TriggerActivation.get())

                self.FrameRateMode = self.FeatureControl.get_enum_feature("AcquisitionFrameRateMode")
                self.TriggerSoftware = self.FeatureControl.get_command_feature("TriggerSoftware")
                self.LineMode = self.FeatureControl.get_enum_feature("LineMode")
                self.CurrentFrameRate = self.FeatureControl.get_float_feature("CurrentAcquisitionFrameRate")
                self.AcquisitionMode = self.FeatureControl.get_enum_feature("AcquisitionMode")

                self.DeviceLinkThroughputLimit = self.FeatureControl.get_int_feature("DeviceLinkThroughputLimit")
                self.DeviceLinkThroughputLimit.set(self.DeviceLinkThroughputLimit.get_range()['max'])
                self.DeviceLinkThroughputLimitMode  =self.FeatureControl.get_enum_feature("DeviceLinkThroughputLimitMode")
                self.DeviceLinkThroughputLimitMode.set("OFF")
                self.DeviceReset = self.FeatureControl.get_command_feature("DeviceReset")

                if self.type == "MER2":
                    self.AcquisitionBurstFrameCount = self.FeatureControl.get_int_feature("AcquisitionBurstFrameCount")
                    self.ExposureTimeMode = self.FeatureControl.get_enum_feature("ExposureTimeMode")

                self.PixelFormats = self.FeatureControl.get_enum_feature("PixelFormat").get_range()
                for pixel_format in self.PixelFormats:
                    if gx.Utility.is_gray(pixel_format['value']):
                        if not self.isColored:
                            self.isColored = False
                        self.SupportMonoFormat = True
                    else:
                        self.isColored = True
                        self.SupportColorFormat = True
                        self.SupportMonoFormat = True

                self.OffsetX.set(0)
                self.OffsetY.set(0)
                
                self.default_preset = {
                    "width" : self.Width.get_range().get("max"),
                    "height" : 210,
                    "exposure_time" :1000.0,
                    "fps": 24.0,
                    "gain" : self.Gain.get_range().get("max"),
                    "trigger_delay" : self.TriggerDelay.get_range().get("min"),
                    "quantity_of_frames" : self.quantity_of_frames,
                    "offsetX" : 0 , 
                    "offsetY" : 0,
                }
                self.preview_preset = self.default_preset.copy()
                self.preview_preset["exposure_time"] = 40000


                self.trigger_preset = self.default_preset.copy()
                self.trigger_preset['exposure_time'] = self.ExposureTime.get_range().get("min")
                self.trigger_preset["fps"] = 1000.0

                self.general_standard_settings()
                self.apply_preset(self.default_preset)
                print(f"The {self.devices[0]} is synchronized")
                print(f"{"Colored" if self.isColored else "Mono"} Camera")
        except Exception as e:
            print(f"{str(e)}")

    def get_image(self) -> tuple[Image.Image , Any] | None:
        try:
            raw_image = self.cam.data_stream[0].get_image()
            timestamp = raw_image.get_timestamp()
            if raw_image is None:
                return None

            height = raw_image.frame_data.height
            width = raw_image.frame_data.width

            if not self.isColored:
                mono_image_array, mono_image_buffer_length = self.convert_to_special_pixel_format(raw_image, GxPixelFormatEntry.MONO8)
                if mono_image_array is None:
                    return
                numpy_image = numpy.frombuffer( mono_image_array, dtype=numpy.ubyte, count=mono_image_buffer_length).reshape(height, width)

                return Image.fromarray(numpy_image, "L"), timestamp
            
            else:
                rgb_image_array, rgb_image_buffer_length = self.convert_to_special_pixel_format(raw_image, GxPixelFormatEntry.RGB8)
                if rgb_image_array is None:
                    return None
                numpy_image = numpy.frombuffer(rgb_image_array, dtype=numpy.ubyte, count=rgb_image_buffer_length).reshape(height, width, 3)

                return Image.fromarray(numpy_image, "RGB"), timestamp

        except Exception as e:
            return None

    def general_standard_settings(self):
        self.FrameRateMode.set("ON")
        self.TriggerMode.set("OFF")

    def general_trigger_settings(self , trigger_source:GxTriggerSourceEntry):
        self.apply_preset(self.trigger_preset)
        self.TriggerActivation.set(GxTriggerActivationEntry.FALLINGEDGE)
        self.FrameRateMode.set("ON")
        if self.type == "MER2":
            self.TriggerSelector.set(GxTriggerSelectorEntry.FRAME_BURST_START)
            self.AcquisitionBurstFrameCount.set(self.AcquisitionBurstFrameCount.get_range().get("max"))

        self.LineMode.set("Input")
        self.TriggerMode.set("ON")

        self.TriggerSource.set(trigger_source)

    def set_preview_preset(self , preset):
        self.preview_preset = preset

    def set_default_preset(self, preset):
        self.default_preset = preset

    def set_trigger_preset(self, preset):
        self.trigger_preset = preset

    def apply_preset(self, preset):

        self.OffsetX.set(0)
        self.OffsetY.set(0)

        self.Width.set(preset['width'])
        self.Height.set(preset['height'])


        max_width = self.Width.get_range().get("max")


        if max_width != preset['width']:
            offsetX = int(max_width/2 - preset['width']/2)
            offsetX_inc = self.OffsetX.get_range().get("inc")

            offsetX_diff = offsetX % offsetX_inc
            if offsetX_diff != 0:
                offsetX -= offsetX_diff
            if offsetX < offsetX_inc:
                offsetX = self.OffsetX.get_range().get("min")
            preset['offsetX'] = offsetX
            self.cam.OffsetX.set(offsetX)

        if self.type == "MER2":
            if preset['exposure_time'] < 20:
                self.ExposureTimeMode.set("UltraShort")
            else:
                self.ExposureTimeMode.set("Standard")

        self.ExposureTime.set(preset['exposure_time'])
        self.FrameRate.set(preset['fps'])
        self.Gain.set(preset['gain'])
        self.TriggerDelay.set(preset['trigger_delay'])
        self.quantity_of_frames = preset["quantity_of_frames"]
        self.OffsetY.set(preset['offsetY'])
        
    def apply_settings_clicked(self , preview_preset = False):
        
        was_recording = self.is_recording
        if was_recording:
            self.switch_capture()
        self.apply_preset(self.trigger_preset)
        self.image_view.current_fps_label.config(text = f"Current FPS : {self.CurrentFrameRate.get()}")
        if preview_preset:
            self.apply_preset(self.preview_preset)
        else:
            print(self.trigger_preset)
            self.apply_preset(self.default_preset)

        if was_recording:
            self.switch_capture()

    def image_handling(self) -> tuple[Image.Image | Any, Any] | None:
        result = self.get_image()
        if result is None:
            return None
        image, timestamp = result
        if not image:
            return None
        if self.image_angle!=0:
            image = image.rotate(self.image_angle)
        if self.flip_v_enabled:
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        if self.flip_h_enabled:
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        if self.crosshair_enabled:
            image = add_crosshair(image)

        return image, timestamp

    def switch_trigger(self , button:tk.Widget, trigger_source:GxTriggerSourceEntry , basename = None):
        if not self.is_recording:
            messagebox.showerror("Error" , "Turn ON the camera")
            return

        self.is_triggered = not self.is_triggered
        print(f"Trigger is {'ON' if self.is_triggered else 'OFF'}")

        if not self.is_triggered:
            self.stop_trigger(button , trigger_source, basename)
            return

        self.trigger_thread = Thread(target=lambda: self.start_trigger(button , trigger_source , basename))
        self.trigger_thread.start()

    def start_trigger(self, button:tk.Widget, trigger_source:GxTriggerSourceEntry, basename = None):
        self.is_triggered = True
        self.capture_event.set()
        self.trigger_start_time = None
        self.trigger_event.clear()
        self.images.clear()
        self.timestamps.clear()
        

        change_calling_button(button, self.is_triggered)

        self.cam.stream_off()
        self.general_trigger_settings(trigger_source)
        self.cam.stream_on()

        self.get_settings()

        if trigger_source == GxTriggerSourceEntry.SOFTWARE:
                self.TriggerSoftware.send_command()

        while not self.trigger_event.is_set():
            try:
                if self.trigger_start_time:
                    if time.perf_counter() - self.trigger_start_time > self.timeout:
                        print("break due to timeout")
                        break
                
                result = self.image_handling()  
                if result is None:
                    continue


                if self.type=="MER" and self.captured_frames ==0:
                    self.TriggerMode.set("OFF")

                image, timestamp = result
                image.resize((self.new_width , self.new_height))
                self.images.append(image)

                if self.captured_frames == 0 :
                    self.timestamps.append(timestamp)
                    self.trigger_start_time = time.perf_counter()
                    self.captured_frames+=1
                    continue
                else:
                    self.timestamps.append(int(timestamp - self.timestamps[0])/1000)
                    
                    if self.captured_frames+1 >= self.quantity_of_frames:
                        break

                    self.captured_frames+=1

            except Exception as e:
                pass

        if self.is_triggered:
            self.timestamps[0] = 0.0
            print(f"Total frames recorded: {self.captured_frames + 1}")
            self.switch_trigger(button , trigger_source, basename)


    def stop_trigger(self, button:tk.Widget, trigger_source:GxTriggerSourceEntry , basename = None):
        self.trigger_event.set()
        self.capture_event.clear()
        change_calling_button(button, self.is_triggered)
        self.cam.stream_off()
        self.general_standard_settings()
        self.apply_preset(self.default_preset)
        self.cam.stream_on()
        self.check_trigger_completion(basename)
        self.captured_frames = 0
        self.quantity_of_frames = None
        self.video_editor.place(relx=0.5 , rely=0.5, anchor="center", relwidth=1, relheight=1)
        self.video_editor.lift()
        self.root.after(5000 , lambda: Thread(target=self.capture_and_display , daemon=True).start())

    def save_images(self , basename = None):
        output_dir = check_dir("output" , basename)
        for i, (img, timestamp) in enumerate(zip(self.images, self.timestamps)):
            img.save(f"{output_dir}/Frame{i+1}__T{timestamp} µs.png")
    
    
    def check_trigger_completion(self , basename = None):
        if len(self.images) < 5 :
            print("Not enough images")
            return
        Thread(target=lambda :self.save_images(basename) ,daemon=True).start()
        Thread(target= lambda: self.video_editor.load_camera_data(self.images , self.timestamps), daemon=True).start()


    def load_image_view(self, image_view):
        self.image_view  = image_view
        self.image_frame = self.image_view.image_frame
 
    def capture_and_display(self):
        while not self.capture_event.is_set():
            try:
                result = self.image_handling()
                if result is None:
                    continue
                image, _ = result
                self.last_image = image
                self.root.after(0 , lambda: self.update_image_frame(image))
            except Exception as e:
                continue

    def update_image_frame(self , image:Image.Image):
        image_frame_width = self.image_frame.winfo_width()
        image_frame_height = self.image_frame.winfo_height()
        image_width = image.width
        image_height = image.height
        
        if image_frame_width == 1:
            image_frame_width = self.image_frame.winfo_reqwidth()
            image_frame_height = self.image_frame.winfo_reqheight()
        if image_frame_width <= 1 or image_frame_height <= 1:
            image_frame_width = image.width
            image_frame_height = image.height




        width_ratio = image_width / image_frame_width
        height_ratio = image_height / image_frame_height

        if width_ratio >=1 :
            self.new_width = image_frame_width
        else:
            self.new_width = image_width
        
        if height_ratio >=1 :
            self.new_height = image_frame_height
        else:
            self.new_height = image_height


        image = image.resize((self.new_width , self.new_height) , Image.Resampling.LANCZOS)


        image = ImageTk.PhotoImage(image=image)
        self.image_frame.config(image = image)
        self.image_frame.image = image
        


    def switch_recording(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.cam.stream_on()
        else:
            self.cam.stream_off()

    def convert_to_special_pixel_format(self, raw_image , pixel_format):
        self.image_convert.set_dest_format(pixel_format)
        valid_bits = get_best_valid_bits(raw_image.frame_data.pixel_format)
        self.image_convert.set_valid_bits(valid_bits)
        buffer_out_size = self.image_convert.get_buffer_size_for_conversion(raw_image)
        output_image_array = (c_byte * buffer_out_size)()
        output_image = addressof(output_image_array)
        self.image_convert.convert(raw_image, output_image, buffer_out_size, False)
        if output_image is None:
            return
        return output_image_array, buffer_out_size

    def get_settings(self):
        if self.cam:
            print(f"    Current FPS : {self.CurrentFrameRate.get()}      FrameRate : {self.FrameRate.get()}")
            print(f"    Width : {self.Width.get()}    Height: {self.Height.get()}")
            print(f"    Exposure Time: {self.ExposureTime.get()}    Gain: {self.Gain.get()} ")
            print(f"    Trigger Delay : {self.TriggerDelay.get()}")
            print(f"    Quantity of Frames : {self.quantity_of_frames}")
            print("-------------------------------------------")

    def switch_capture(self):
        self.switch_recording()
        print(f"Recording is {'ON' if self.is_recording else 'OFF'}")
        if not self.is_recording:
            self.capture_event.set()
            return
        self.capture_event.clear()
        Thread(target=self.capture_and_display, daemon=True).start()

    def switch_crosshair(self):
        self.crosshair_enabled = not self.crosshair_enabled
        print(f"Crosshair is {"ON" if self.crosshair_enabled else "OFF"}")

    def flip_image_horizontally(self):
        self.flip_h_enabled = not self.flip_h_enabled
        print("Image flipped HORIZONTALLY")

    def flip_image_vertically(self):
        self.flip_v_enabled = not self.flip_v_enabled
        print("Image flipped VERTICALLY")

    def rotate_image_right(self):
        self.image_angle -= 90
        if abs(self.image_angle) == 360:
            self.image_angle =0
        print(f"Current image angle : {self.image_angle}")

    def rotate_image_left(self):
        self.image_angle +=90
        if abs(self.image_angle) == 360:
            self.image_angle =0
        print(f"Current image angle : {self.image_angle}")

    def switch_white_balance(self):
        self.cam.BalanceWhiteAuto.set(gx.GxAutoEntry.ONCE)
        print(f"Auto white balance is ON")

    def close(self):
        if self.cam:
            print("Camera is off")
            self.TriggerMode.set("OFF")
            self.cam.close_device()

def add_crosshair(image: Image.Image) -> Image.Image:
    img = image.copy()
    draw = ImageDraw.Draw(img)
    width, height = img.size
    draw.line(
        [(0, height / 2), (width, height / 2)], fill="red", width=2
    )
    draw.line(
        [(width / 2, 0), (width / 2, height)], fill="red", width=2
    )
    return img

def get_best_valid_bits(pixel_format):
    valid_bits = DxValidBit.BIT0_7
    if pixel_format in (
        GxPixelFormatEntry.MONO8,
        GxPixelFormatEntry.BAYER_GR8,
        GxPixelFormatEntry.BAYER_RG8,
        GxPixelFormatEntry.BAYER_GB8,
        GxPixelFormatEntry.BAYER_BG8,
        GxPixelFormatEntry.RGB8,
        GxPixelFormatEntry.BGR8,
        GxPixelFormatEntry.R8,
        GxPixelFormatEntry.B8,
        GxPixelFormatEntry.G8,
    ):
        valid_bits = DxValidBit.BIT0_7
    elif pixel_format in (
        GxPixelFormatEntry.MONO10,
        GxPixelFormatEntry.MONO10_PACKED,
        GxPixelFormatEntry.MONO10_P,
        GxPixelFormatEntry.BAYER_GR10,
        GxPixelFormatEntry.BAYER_RG10,
        GxPixelFormatEntry.BAYER_GB10,
        GxPixelFormatEntry.BAYER_BG10,
        GxPixelFormatEntry.BAYER_GR10_P,
        GxPixelFormatEntry.BAYER_RG10_P,
        GxPixelFormatEntry.BAYER_GB10_P,
        GxPixelFormatEntry.BAYER_BG10_P,
        GxPixelFormatEntry.BAYER_GR10_PACKED,
        GxPixelFormatEntry.BAYER_RG10_PACKED,
        GxPixelFormatEntry.BAYER_GB10_PACKED,
        GxPixelFormatEntry.BAYER_BG10_PACKED,
    ):
        valid_bits = DxValidBit.BIT2_9
    elif pixel_format in (
        GxPixelFormatEntry.MONO12,
        GxPixelFormatEntry.MONO12_PACKED,
        GxPixelFormatEntry.MONO12_P,
        GxPixelFormatEntry.BAYER_GR12,
        GxPixelFormatEntry.BAYER_RG12,
        GxPixelFormatEntry.BAYER_GB12,
        GxPixelFormatEntry.BAYER_BG12,
        GxPixelFormatEntry.BAYER_GR12_P,
        GxPixelFormatEntry.BAYER_RG12_P,
        GxPixelFormatEntry.BAYER_GB12_P,
        GxPixelFormatEntry.BAYER_BG12_P,
        GxPixelFormatEntry.BAYER_GR12_PACKED,
        GxPixelFormatEntry.BAYER_RG12_PACKED,
        GxPixelFormatEntry.BAYER_GB12_PACKED,
        GxPixelFormatEntry.BAYER_BG12_PACKED,
    ):
        valid_bits = DxValidBit.BIT4_11
    elif pixel_format in (
        GxPixelFormatEntry.MONO14,
        GxPixelFormatEntry.MONO14_P,
        GxPixelFormatEntry.BAYER_GR14,
        GxPixelFormatEntry.BAYER_RG14,
        GxPixelFormatEntry.BAYER_GB14,
        GxPixelFormatEntry.BAYER_BG14,
        GxPixelFormatEntry.BAYER_GR14_P,
        GxPixelFormatEntry.BAYER_RG14_P,
        GxPixelFormatEntry.BAYER_GB14_P,
        GxPixelFormatEntry.BAYER_BG14_P,
    ):
        valid_bits = DxValidBit.BIT6_13
    elif pixel_format in (
        GxPixelFormatEntry.MONO16,
        GxPixelFormatEntry.BAYER_GR16,
        GxPixelFormatEntry.BAYER_RG16,
        GxPixelFormatEntry.BAYER_GB16,
        GxPixelFormatEntry.BAYER_BG16,
    ):
        valid_bits = DxValidBit.BIT8_15
    return valid_bits

def change_calling_button(button:tk.Button, calling_state:bool) :
    if calling_state:
        button.config(bg='green', activebackground='green', state = "active",activeforeground="white", fg="white")
        return
    button.config(bg="SystemButtonFace", activebackground='SystemButtonFace', state = "normal", fg="black" , activeforeground="black")

def check_dir(dir="output", basename = None) -> str:
    print(basename)
    dirPath = dir + "/"
    i = 0
    if not os.path.exists(dir):
        print(f"Directory ---> {str(dir)} does not exist")
        os.mkdir(dir)
    while os.path.exists(dirPath + "_" + str(i)):
        # print(f"Directory ---> {dirPath + "_" + str(i)} is not empty")
        i += 1
    destPath = dirPath +f"{basename if basename else ""}" + "_" + str(i)
    print(f"Results directory ---> {destPath}")
    os.makedirs(destPath)

    return destPath
