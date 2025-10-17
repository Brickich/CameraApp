import gxipy as gx
from PIL import Image, ImageDraw
from threading import Event
import json

class PresetManager:
    def __init__(self):
        self.presets = {
            "default" : {},
            "preview" : {},
            "trigger" : {},
        }

    def check_existence(self, preset_name):
        if preset_name in self.presets:
            return True
        
        raise ValueError(f"Preset : {preset_name} doesn't exist")


    def change_preset(self , preset_name , preset_data):
        if self.check_existence(preset_name):
            self.presets[preset_name] = preset_data

    def get_preset(self, preset_name) :
        if self.check_existence(preset_name):
            return self.presets[preset_name]
    
    def add_preset(self , preset_name , preset_data = None):
        if preset_data is None:
            preset_data = {}
        self.presets[preset_name] = preset_data

    def save_to_file(self, preset_name , filename):
        with open(filename , "w") as f:
            json.dump(self.presets[preset_name], f  , indent=4)





class CameraControl:
    def __init__(self):
        self.devices:list[str] = []
        self.cams= []
        self.cameras:list[Camera] = []

        self.device_manager = gx.DeviceManager()
        dev_num, dev_info_list = self.device_manager.update_device_list()

        if dev_num == 0:
            print("No available devices")
            raise Exception("No available devices")
        else:
            for i in range(dev_num):
                self.devices.append(dev_info_list[i].get("model_name"))
                cam = self.device_manager.open_device_by_index(i+1)
                self.cams.append(cam)

                
        for i in range(len(self.cams)):
            cam = self.cams[i]
            device = self.devices[i]
            print(f"Device {i+1}: {device}")  
            model = device
            
            type = (
                "MER3" if "MER3" in model else
                "MER2" if "MER2" in model else
                "MER" if "MER" in model else
                model.upper())
            print(type)
            image_convert = self.device_manager.create_image_format_convert()
            camera = Camera(cam , type , image_convert)
            self.cameras.append(camera)
            print(f"The {model.upper()} is synchronised")

        


class Camera:
    def __init__(self ,  cam, type , image_convert):
        self.cam = None
        self.type = None
        self.image_convert =  None
        self.preset_manager = PresetManager()

        self.is_recording = False
        self.is_triggered = False
        self.colored = False
        self.SupportColorFormat = False
        self.SupportMonoFormat = False


        self.trigger_start_time = None
        self.captured_frames = 0
        self.QuantityOfFrames = 100
        self.timeout = 12.0

        self.trigger_event = Event()
        self.capture_event = Event()

        self.crosshair_enabled = False
        self.flip_h_enabled = False
        self.flip_v_enabled = False
        self.image_angle =0 

        self.images:list[Image.Image] =[]
        self.raw_images:list = []
        self.timestamps:list[float] = []

        
        self.__init__device(cam , type , image_convert) 

    def __init__device(self , cam , type , image_convert):
        try: 
            self.cam = cam
            self.type = type
            self.image_convert = image_convert
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

            if self.type != "MER":
                self.AcquisitionBurstFrameCount = self.FeatureControl.get_int_feature("AcquisitionBurstFrameCount")
                self.ExposureTimeMode = self.FeatureControl.get_enum_feature("ExposureTimeMode")

            self.PixelFormats = self.FeatureControl.get_enum_feature("PixelFormat").get_range()

            for pixel_format in self.PixelFormats:
                if gx.Utility.is_gray(pixel_format['value']):
                    if not self.colored:
                        self.colored = False
                    self.SupportMonoFormat = True
                else:
                    self.colored = True
                    self.SupportColorFormat = True
                    self.SupportMonoFormat = True
            self.OffsetX.set(0)
            self.OffsetY.set(0)
            

            default_preset = {
                "Width" : self.Width.get_range().get("max"),
                "Height" : 220,
                "ExposureTime" :40000.0,
                "FrameRate": 24.0,
                "Gain" : self.Gain.get_range().get("max"),
                "TriggerDelay" : self.TriggerDelay.get_range().get("min"),
                "QuantityOfFrames" : self.QuantityOfFrames,
                "OffsetX" : 0 , 
                "OffsetY" : 0,
            }

            self.preset_manager.change_preset("default" , default_preset)

            preview_preset = default_preset.copy()
            preview_preset["ExposureTime"] = 40000.0

            self.preset_manager.change_preset("preview" , preview_preset)

            trigger_preset = default_preset.copy()
            trigger_preset['ExposureTime'] = self.ExposureTime.get_range().get("min")
            trigger_preset["FrameRate"] = 1000.0

            self.preset_manager.change_preset("trigger" , trigger_preset)

            self.default_settings()

            print(f"{"Colored" if self.colored else "Mono"} Camera")
        except Exception as e:
            print(f"{str(e)}")
    
    def get_raw_image(self) :
        raw_image = self.cam.data_stream[0].get_image()
        return raw_image

    def convert_raw_image(self , raw_image):
        height = raw_image.frame_data.height
        width = raw_image.frame_data.width
        if not self.colored:
            mono_image_array, mono_image_buffer_length = self.convert_to_special_pixel_format(raw_image, gx.GxPixelFormatEntry.MONO8)
            if mono_image_array is None:
                return
            numpy_image = gx.numpy.frombuffer( mono_image_array, dtype=gx.numpy.ubyte, count=mono_image_buffer_length).reshape(height, width)
            return Image.fromarray(numpy_image, "L")
            
        else:
            rgb_image_array, rgb_image_buffer_length = self.convert_to_special_pixel_format(raw_image, gx.GxPixelFormatEntry.RGB8)
            if rgb_image_array is None:
                return None
            numpy_image = gx.numpy.frombuffer(rgb_image_array, dtype=gx.numpy.ubyte, count=rgb_image_buffer_length).reshape(height, width, 3)
            return Image.fromarray(numpy_image, "RGB")

    def get_image(self) -> tuple[Image.Image] | None:
        try:
            raw_image = self.get_raw_image()
            if raw_image is None:
                return None


            return self.convert_raw_image(raw_image)

            
        except Exception as e:
            return None

    def default_settings(self):
        self.apply_preset(self.preset_manager.get_preset("default"))
        self.FrameRateMode.set("ON")
        self.TriggerMode.set("OFF")

    def trigger_settings(self , trigger_source:str):
        self.apply_preset(self.preset_manager.get_preset("trigger"))
        self.TriggerActivation.set(gx.GxTriggerActivationEntry.FALLINGEDGE)
        self.FrameRateMode.set("ON")
        if self.type != "MER":
            self.TriggerSelector.set(gx.GxTriggerSelectorEntry.FRAME_BURST_START)
            self.AcquisitionBurstFrameCount.set(self.AcquisitionBurstFrameCount.get_range().get("max"))

        self.LineMode.set("Input")
        self.TriggerMode.set("ON")

        self.TriggerSource.set(trigger_source)


    def apply_preset(self, preset):

        self.OffsetX.set(0)
        self.OffsetY.set(0)

        self.Width.set(preset["Width"])
        self.Height.set(preset["Height"])

        if self.type == "MER2":
            if preset["ExposureTime"] < 20:
                self.ExposureTimeMode.set("UltraShort")
            else:
                self.ExposureTimeMode.set("Standard")

        self.ExposureTime.set(preset['ExposureTime'])
        self.FrameRate.set(preset['FrameRate'])
        self.Gain.set(preset['Gain'])
        self.TriggerDelay.set(preset['TriggerDelay'])
        self.QuantityOfFrames = preset["QuantityOfFrames"]
        self.OffsetX.set(preset["OffsetX"])
        self.OffsetY.set(preset['OffsetY'])
        

    def save_images(self , dir_path ):
        for i, (img, timestamp) in enumerate(zip(self.images, self.timestamps)):
            img.save(f"{dir_path}/Frame{i+1}__T{timestamp} µs.png")

    def image_handling(self) :
        result = self.get_image()
        if result is None:
            return None
        image = result
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

        return image

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
        output_image_array = (gx.c_byte * buffer_out_size)()
        output_image = gx.addressof(output_image_array)
        self.image_convert.convert(raw_image, output_image, buffer_out_size, False)
        if output_image is None:
            return
        return output_image_array, buffer_out_size

    def print_settings(self):
        if self.cam:
            print(f"    Current FPS : {self.CurrentFrameRate.get()}      FrameRate : {self.FrameRate.get()}")
            print(f"    Width : {self.Width.get()}    Height: {self.Height.get()}")
            print(f"    Exposure Time: {self.ExposureTime.get()}    Gain: {self.Gain.get()} ")
            print(f"    Trigger Delay : {self.TriggerDelay.get()}")
            print(f"    Quantity of Frames : {self.QuantityOfFrames}")
            print("-------------------------------------------")

    def switch_trigger(self):
        self.is_triggered = not self.is_triggered
        print(f"Trigger {"ON" if self.is_triggered else "OFF"}")




        
    def switch_capture(self):
        self.switch_recording()
        print(f"Recording is {'ON' if self.is_recording else 'OFF'}")
        if not self.is_recording:
            self.capture_event.set()
            return
        self.capture_event.clear()

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
    valid_bits = gx.DxValidBit.BIT0_7
    if pixel_format in (
        gx.GxPixelFormatEntry.MONO8,
        gx.GxPixelFormatEntry.BAYER_GR8,
        gx.GxPixelFormatEntry.BAYER_RG8,
        gx.GxPixelFormatEntry.BAYER_GB8,
        gx.GxPixelFormatEntry.BAYER_BG8,
        gx.GxPixelFormatEntry.RGB8,
        gx.GxPixelFormatEntry.BGR8,
        gx.GxPixelFormatEntry.R8,
        gx.GxPixelFormatEntry.B8,
        gx.GxPixelFormatEntry.G8,
    ):
        valid_bits = gx.DxValidBit.BIT0_7
    elif pixel_format in (
        gx.GxPixelFormatEntry.MONO10,
        gx.GxPixelFormatEntry.MONO10_PACKED,
        gx.GxPixelFormatEntry.MONO10_P,
        gx.GxPixelFormatEntry.BAYER_GR10,
        gx.GxPixelFormatEntry.BAYER_RG10,
        gx.GxPixelFormatEntry.BAYER_GB10,
        gx.GxPixelFormatEntry.BAYER_BG10,
        gx.GxPixelFormatEntry.BAYER_GR10_P,
        gx.GxPixelFormatEntry.BAYER_RG10_P,
        gx.GxPixelFormatEntry.BAYER_GB10_P,
        gx.GxPixelFormatEntry.BAYER_BG10_P,
        gx.GxPixelFormatEntry.BAYER_GR10_PACKED,
        gx.GxPixelFormatEntry.BAYER_RG10_PACKED,
        gx.GxPixelFormatEntry.BAYER_GB10_PACKED,
        gx.GxPixelFormatEntry.BAYER_BG10_PACKED,
    ):
        valid_bits = gx.DxValidBit.BIT2_9
    elif pixel_format in (
        gx.GxPixelFormatEntry.MONO12,
        gx.GxPixelFormatEntry.MONO12_PACKED,
        gx.GxPixelFormatEntry.MONO12_P,
        gx.GxPixelFormatEntry.BAYER_GR12,
        gx.GxPixelFormatEntry.BAYER_RG12,
        gx.GxPixelFormatEntry.BAYER_GB12,
        gx.GxPixelFormatEntry.BAYER_BG12,
        gx.GxPixelFormatEntry.BAYER_GR12_P,
        gx.GxPixelFormatEntry.BAYER_RG12_P,
        gx.GxPixelFormatEntry.BAYER_GB12_P,
        gx.GxPixelFormatEntry.BAYER_BG12_P,
        gx.GxPixelFormatEntry.BAYER_GR12_PACKED,
        gx.GxPixelFormatEntry.BAYER_RG12_PACKED,
        gx.GxPixelFormatEntry.BAYER_GB12_PACKED,
        gx.GxPixelFormatEntry.BAYER_BG12_PACKED,
    ):
        valid_bits = gx.DxValidBit.BIT4_11
    elif pixel_format in (
        gx.GxPixelFormatEntry.MONO14,
        gx.GxPixelFormatEntry.MONO14_P,
        gx.GxPixelFormatEntry.BAYER_GR14,
        gx.GxPixelFormatEntry.BAYER_RG14,
        gx.GxPixelFormatEntry.BAYER_GB14,
        gx.GxPixelFormatEntry.BAYER_BG14,
        gx.GxPixelFormatEntry.BAYER_GR14_P,
        gx.GxPixelFormatEntry.BAYER_RG14_P,
        gx.GxPixelFormatEntry.BAYER_GB14_P,
        gx.GxPixelFormatEntry.BAYER_BG14_P,
    ):
        valid_bits = gx.DxValidBit.BIT6_13
    elif pixel_format in (
        gx.GxPixelFormatEntry.MONO16,
        gx.GxPixelFormatEntry.BAYER_GR16,
        gx.GxPixelFormatEntry.BAYER_RG16,
        gx.GxPixelFormatEntry.BAYER_GB16,
        gx.GxPixelFormatEntry.BAYER_BG16,
    ):
        valid_bits = gx.DxValidBit.BIT8_15
    return valid_bits


