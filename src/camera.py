import gxipy as gx
from PIL import Image
from threading import Event
import json


class PresetManager:
    def __init__(self):
        self.presets = {
            "default" : {},
            "preview" : {},
            "trigger" : {},
        }

    def checkExistence(self, preset_name):
        if preset_name in self.presets:
            return True
        
        raise ValueError(f"Preset : {preset_name} doesn't exist")


    def changePreset(self , preset_name , preset_data):
        if self.checkExistence(preset_name):
            self.presets[preset_name] = preset_data

    def getPreset(self, preset_name) :
        if self.checkExistence(preset_name):
            return self.presets[preset_name]
    
    def addPreset(self , preset_name , preset_data = None):
        if preset_data is None:
            preset_data = {}
        self.presets[preset_name] = preset_data

    def saveToFile(self, preset_name , filename):
        with open(filename , "w") as f:
            json.dump(self.presets[preset_name], f  , indent=4)



class CameraControl:
    def __init__(self):
        self.devices:list[str] = []
        self.cams= []
        self.cameras:list[Camera] = []

        self.deviceManager = gx.DeviceManager()
        dev_num, dev_info_list = self.deviceManager.update_device_list()



        if dev_num == 0:
            print("No available devices")
            raise Exception("No available devices")
        else:
            for i in range(dev_num):
                self.devices.append(dev_info_list[i].get("model_name"))
                cam = self.deviceManager.open_device_by_index(i+1)
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
            image_convert = self.deviceManager.create_image_format_convert()
            camera = Camera(cam , type , image_convert , model)
            self.cameras.append(camera)

        


class Camera:
    def __init__(self ,  cam, type , image_convert , model):
        self.cam = None
        self.type = None
        self.model = model
        self.imageConvert =  None
        self.presetManager = PresetManager()

        self.isRecording = False
        self.isTriggered = False
        self.colored = False
        self.supportColorFormat = False
        self.supportMonoFormat = False


        self.FramesCaptured = 0
        self.FramesQuantity = 10
        self.timeout = 12.0

        self.crosshairEnabled = False
        self.flipHorEnabled = False
        self.flipVerEnabled = False
        self.imageAngle =0 

        self.images:list[Image.Image] =[]
        self.rawImages:list = []
        self.timestamps:list[float] = []
        self.numpyImages:list = []

        self.settings = ["Width" , "Height" , "OffsetX" , "OffsetY" ,"FrameRate", "ExposureTime" , "Gain" , "TriggerDelay" , "FramesQuantity"]



        


        
        self._initDevice(cam , type , image_convert) 

    def _initDevice(self , cam , type , image_convert):
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
            self.FrameRateMode = self.FeatureControl.get_enum_feature("AcquisitionFrameRateMode")
            self.TriggerSoftware = self.FeatureControl.get_command_feature("TriggerSoftware")
            self.LineMode = self.FeatureControl.get_enum_feature("LineMode")
            self.LineSource = self.FeatureControl.get_enum_feature("LineSource")
            self.LineSelector = self.FeatureControl.get_enum_feature("LineSelector")
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

            self.pixelFormats = self.FeatureControl.get_enum_feature("PixelFormat").get_range()

            for pixelFormat in self.pixelFormats:
                if gx.Utility.is_gray(pixelFormat['value']):
                    if not self.colored:
                        self.colored = False
                    self.supportMonoFormat = True
                else:
                    self.colored = True
                    self.supportColorFormat = True
                    self.supportMonoFormat = True
            self.OffsetX.set(0)
            self.OffsetY.set(0)
            

            default_preset = {
                "Width" : self.Width.get_range().get("max"),
                "Height" : 220,
                "ExposureTime" :40000.0,
                "FrameRate": 24.0,
                "Gain" : self.Gain.get_range().get("max"),
                "TriggerDelay" : self.TriggerDelay.get_range().get("min"),
                "FramesQuantity" : self.FramesQuantity,
                "OffsetX" : 0 , 
                "OffsetY" : 0,
            }

            self.presetManager.changePreset("default" , default_preset)

            preview_preset = default_preset.copy()
            preview_preset["ExposureTime"] = 40000.0

            self.presetManager.changePreset("preview" , preview_preset)

            trigger_preset = default_preset.copy()

            self.presetManager.changePreset("trigger" , trigger_preset)

            self.applyPreset(default_preset)
            self.defaultSettings()
        except Exception as e:
            print(f"{str(e)}")
    
    def getRawImage(self) :
        return self.cam.data_stream[0].get_image()

    def convertRawImage(self , rawImage):
        height = rawImage.frame_data.height
        width = rawImage.frame_data.width
        if not self.colored:
            mono_image_array, mono_image_buffer_length = self.convert_to_special_pixel_format(rawImage, gx.GxPixelFormatEntry.MONO8)
            if mono_image_array is None:
                return
            numpy_image = gx.numpy.frombuffer( mono_image_array, dtype=gx.numpy.ubyte, count=mono_image_buffer_length).reshape(height, width)
            
        else:
            rgb_image_array, rgb_image_buffer_length = self.convert_to_special_pixel_format(rawImage, gx.GxPixelFormatEntry.RGB8)
            if rgb_image_array is None:
                return None
            numpy_image = gx.numpy.frombuffer(rgb_image_array, dtype=gx.numpy.ubyte, count=rgb_image_buffer_length).reshape(height, width, 3)
        return numpy_image

    def getImage(self , numpyImage) :
        if not self.colored:
            return Image.fromarray(numpyImage, "L")
        else:
            return Image.fromarray(numpyImage, "RGB")

    def defaultSettings(self):
        defaultPreset = self.presetManager.getPreset("default")
        self.FrameRate.set(defaultPreset["FrameRate"])

        self.FrameRateMode.set("ON")
        self.TriggerMode.set("OFF")

    def triggerSettings(self, triggerSource:str ):
        self.applyPreset(self.presetManager.getPreset("trigger"))
        self.TriggerActivation.set(gx.GxTriggerActivationEntry.FALLINGEDGE)
        self.FrameRateMode.set("ON")
        if self.type != "MER":
            self.TriggerSelector.set(gx.GxTriggerSelectorEntry.FRAME_BURST_START)
            self.AcquisitionBurstFrameCount.set(self.AcquisitionBurstFrameCount.get_range().get("max"))
        
        self.TriggerMode.set("ON")
        self.TriggerSource.set(triggerSource)



    def applyPreset(self, preset):
        self.OffsetX.set(0)
        self.OffsetY.set(0)

        self.Width.set(preset["Width"])
        self.Height.set(preset["Height"])

        if self.type != "MER":
            if preset["ExposureTime"] < 20:
                self.ExposureTimeMode.set("UltraShort")
            else:
                self.ExposureTimeMode.set("Standard")

        self.ExposureTime.set(preset['ExposureTime'])
        self.FrameRate.set(preset['FrameRate'])
        self.Gain.set(preset['Gain'])
        self.TriggerDelay.set(preset['TriggerDelay'])

        self.FramesQuantity = preset["FramesQuantity"]
        self.OffsetX.set(preset["OffsetX"])
        self.OffsetY.set(preset['OffsetY'])
        
    def previewMode(self):
        if hasattr(self , "ExposureTimeMode"):
            self.cam.stream_off()
            self.ExposureTimeMode.set("Standard")
            self.cam.stream_on()
        self.ExposureTime.set(float(40000))

    def triggerMode(self):
        exposureTime = self.presetManager.getPreset("default").get("ExposureTime")
        if exposureTime < 20 and hasattr(self , "ExposureTimeMode"):
            self.cam.stream_off()
            self.ExposureTimeMode.set("UltraShort")
            self.cam.stream_on()
        self.ExposureTime.set(exposureTime)  

    def  saveImages(self , dir_path ):
        for i, (img, timestamp) in enumerate(zip(self.images, self.timestamps)):
            img.save(f"{dir_path}/Frame{i+1}__T{timestamp} µs.png")



    def convert_to_special_pixel_format(self, rawImage , pixelFormat):
        self.image_convert.set_dest_format(pixelFormat)
        valid_bits = self.get_best_valid_bits(rawImage.frame_data.pixel_format)
        self.image_convert.set_valid_bits(valid_bits)
        buffer_out_size = self.image_convert.get_buffer_size_for_conversion(rawImage)
        output_image_array = (gx.c_byte * buffer_out_size)()
        output_image = gx.addressof(output_image_array)
        self.image_convert.convert(rawImage, output_image, buffer_out_size, False)
        if output_image is None:
            return
        return output_image_array, buffer_out_size

    def __str__(self):
        return (
            f"{self.model}\n"
            f"Width:{self.Width.get()}\tHeight:{self.Height.get()}\tOffsetX:{self.OffsetX.get()}\tOffsetY:{self.OffsetY.get()}\n"
            f"FrameRate:{self.CurrentFrameRate.get()}\tFrames:{self.FramesQuantity}\tExposureTime:{self.ExposureTime.get()}\n"
            f"TriggerSource:{self.TriggerSource.get()}\tTriggerDelay:{self.TriggerDelay.get()}"
        )

        
    def switch_crosshair(self):
        self.crosshairEnabled = not self.crosshairEnabled
        print(f"{self.model} Crosshair is {"ON" if self.crosshairEnabled else "OFF"}\n")

    def flip_image_horizontally(self):
        self.flipHorEnabled = not self.flipHorEnabled
        print("{} Image flipped HORIZONTALLY".format(self.model))

    def flip_image_vertically(self):
        self.flipVerEnabled = not self.flipVerEnabled
        print("{} Image flipped VERTICALLY".format(self.model))

    def rotate_image_right(self):
        self.imageAngle -= 90
        if abs(self.imageAngle) == 360:
            self.imageAngle =0
        print(f"{self.model} Current image angle : {self.imageAngle}")

    def rotate_image_left(self):
        self.imageAngle +=90
        if abs(self.imageAngle) == 360:
            self.imageAngle =0
        print(f"{self.model} Current image angle : {self.imageAngle}")

    def switch_white_balance(self):
        self.cam.BalanceWhiteAuto.set(gx.GxAutoEntry.ONCE)

    def close(self):
        if self.cam:
            print("{} is off".format(self.model))
            self.TriggerMode.set("OFF")
            self.cam.close_device()
    
    def get_best_valid_bits(self, pixel_format):
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
    




