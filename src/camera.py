import gxipy as gx
from gxipy.gxidef import *
from gxipy.ImageFormatConvert import *
from PIL import Image


class Camera:
    def __init__(self):
        self.device_manager = gx.DeviceManager()
        self.cam = None
        self.settings_implemented = False
        self.is_recording = False
        self.is_triggered = False
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
                self.cam = self.device_manager.open_device_by_index(1)
                self.width = self.cam.Width
                self.height = self.cam.Height
                self.exposure_time = self.cam.ExposureTime
                self.gain = self.cam.Gain
                self.framerate = self.cam.AcquisitionFrameRate
                self.remote_device_feature_control = self.cam.get_remote_device_feature_control()
                print("Camera is synchronized")
                
                self.init_default_parameters()
        except Exception as e:
            print(f"Can't initialize the camera {str(e)}")
               
        
    def get_RGB_image(self) -> Image.Image | None:
        try:
            raw_image = self.cam.data_stream[0].get_image()
            if raw_image is None:
                return None
                
            pixel_format = raw_image.frame_data.pixel_format
            height = raw_image.frame_data.height
            width = raw_image.frame_data.width
            
            if pixel_format != GxPixelFormatEntry.RGB8:
                rgb_image_array, rgb_image_buffer_length = self.convert_to_RGB(raw_image, GxPixelFormatEntry.RGB8)
                if rgb_image_array is None:
                    return None
                numpy_image = numpy.frombuffer(rgb_image_array, dtype=numpy.ubyte, count=rgb_image_buffer_length).reshape(height, width, 3)
            else:
                numpy_image = raw_image.get_numpy_array()
                
            if numpy_image is None:
                print('Failed to get numpy array')
                return None
                
            return Image.fromarray(numpy_image, "RGB")
            
        except Exception as e:
            print(f"Error in get_RGB_image: {str(e)}")
            return None
        

    def switch_trigger(self):
        def default_trigger_parameters():
            ## ---------------------------Это параметры, которые должны быть в реальности ----------------------------------##
            # self.cam.stream_off()
            # self.cam.TriggerMode.set(GxSwitchEntry.ON)
            # self.cam.TriggerDelay.set(0)
            # self.cam.AcquisitionFrameRateMode.set(GxSwitchEntry.OFF)
            # self.cam.AcquisitionFrameRate.set(500)
            # self.cam.TriggerSource.set(GxTriggerSourceEntry.LINE0)
            # self.cam.stream_on()
            self.init_default_parameters()
            
        self.is_triggered = not self.is_triggered
        print(f"Trigger is {'ON' if self.is_triggered else 'OFF'}")
        if self.is_triggered:
            if self.settings_implemented:
                pass
            else:
                default_trigger_parameters()
        else:
            self.init_default_parameters()

    def switch_recording(self):
        self.is_recording = not self.is_recording
        print(f"Recording is {'ON' if self.is_recording else 'OFF'}")
        if self.is_recording:
            self.cam.stream_on()
        else:
            self.cam.stream_off()

    def convert_to_RGB(self, raw_image , pixel_format):
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


    def switch_white_balance(self):
            self.cam.BalanceWhiteAuto.set(gx.GxAutoEntry.ONCE)
            print(f"Auto white balance is ON")

    def get_settings(self):
        if self.cam:
            print(
                f"    Image width : {self.width.get()}    Image Height: {self.height.get()}"
            )
            print(
                f"    Exposure Time: {self.exposure_time.get()}    Gain: {self.gain.get()}       FrameRate : {self.framerate.get()}"
            )
            print("-------------------------------------------")
            print("Current FPS=" + str(self.framerate.get()))
            print("-------------------------------------------")

    def init_default_parameters(self):  
        
        def default_parameters():
            self.width.set(800)
            self.height.set(600)
            self.cam.TriggerDelay.set(0)
            self.cam.TriggerSource.set(GxTriggerSourceEntry.SOFTWARE)
            self.cam.TriggerMode.set(GxSwitchEntry.OFF)
            self.framerate.set(500)
            self.exposure_time.set(10000)
            self.gain.set(24)
            self.cam.DeviceLinkThroughputLimit.set(400000000)
            self.cam.DeviceLinkThroughputLimitMode.set(gx.GxSwitchEntry.OFF)

            

              
        if self.is_recording:
            self.cam.stream_off()
            default_parameters()
            self.cam.stream_on()
            return
            
        default_parameters()

    def close(self):
        if self.cam:
            print("Camera is off")
            self.cam.close_device()


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
