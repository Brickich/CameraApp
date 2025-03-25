from tkinter import Tk, Canvas, PhotoImage, Button, Label, Frame, Entry
from tkinter.filedialog import asksaveasfilename
import gxipy as gx
#import imageio
from PIL import Image
from PIL import ImageTk
import os
#import cv2 as cv
import numpy as np
#import moviepy.editor as mp
from datetime import datetime
from threading import Thread
##########################################
######### images params #################
image_width = 1440
image_height = 464
image_offset_X = 0#int(2448 / 2 - 0*image_width / 2)
image_offset_Y = 0
image_angle = 0
image_flip_h = False
image_flip_v = False
##########################################
######### preview params #################
exposure_preview = 1000
gain_preview = 24.0
#fps_preview = 10
##########################################
######### arming params ##################
exposure_arming = 1000
gain_arming = 24.0
time_of_frames = 0.25
trigger_delay = 0
file_save_dir = os.path.dirname(__file__)
default_folder_name = '1'
##########################################
######### canvas params #################
canvas_width = int(image_width/1)
canvas_height = int(image_height/1)
##########################################
##########################################
canvas_image = None
lineH = None
lineW = None

improvement_params = {'color_correction_param': None, 'contrast_lut': None, 'gamma_lut': None}

closing_req = False
play_pause_req = False
arm_req = False

save_img_req = False
wbalance_req = False
camera_colored = False
const_video = False
arm_req_multiple = False
arm_state_multiple = False
multiple_images_counter = 0
raw_image = []
gif_images = []
softwareTrig_req = False

crosschair = False
arm_state = False

preview_state = True
cam = 0
root = Tk()
counter = 0
def main():
    global root
    global cam
    global camera_colored
    global image_width
    global image_height
    global image_offset_X
    global image_offset_Y
    global lineH
    global lineW
    global closing_req
    global play_pause_req
    global arm_state
    global arm_state_multiple
    global preview_state
    global arm_req
    global arm_req_multiple
    global multiple_images_counter
    global save_img_req
    global wbalance_req
    global raw_image
    global softwareTrig_req
    global trigger_delay
    global num_of_frames
    btns_frame = Frame(root, height = 55)
    btns_frame.pack(side = 'top', fill = 'x')
    
    photo_pause = PhotoImage(file = 'assets/pause-button.png').subsample(15,15)
    photo_preview = PhotoImage(file = 'assets/play-button.png').subsample(15,15)
    btn_preview = Button(btns_frame, image = photo_pause, command = lambda: btn_preview_onClick1())
    btn_preview.place(x = 5, y = 5, height = 50, width = 50)

    photo_arm = PhotoImage(file = 'assets/repeat-one.png').subsample(15,15)
    btn_arm = Button(btns_frame, image = photo_arm, bg = 'green', command = lambda: btn_arm_onClick1())
    btn_arm.place(x = 60, y = 5, height = 50, width = 50)
    
    btn_wbalance = Button(btns_frame, text = "WB", command = lambda: btn_wbalance_onClick1())
    btn_wbalance.place(x = 115, y = 5, height = 50, width = 50)

    photo_flip_h = PhotoImage(file = 'assets/flip_h.png').subsample(15,15)
    btn_flip_h = Button(btns_frame, image = photo_flip_h, command = lambda: btn_flip_h_onClick1())
    btn_flip_h.place(x = 170, y = 5, height = 50, width = 50)
    
    photo_flip_v = PhotoImage(file = 'assets/flip_v.png').subsample(15,15)
    btn_flip_v = Button(btns_frame, image = photo_flip_v, command = lambda: btn_flip_v_onClick1())
    btn_flip_v.place(x = 225, y = 5, height = 50, width = 50)

    photo_rotate_right = PhotoImage(file = 'assets/rotate-to-right.png').subsample(15,15)
    btn_rotate_right = Button(btns_frame, image = photo_rotate_right, command = lambda: btn_rotate_right_onClick1())
    btn_rotate_right.place(x = 280, y = 5, height = 50, width = 50)
    
    photo_rotate_left = PhotoImage(file = 'assets/rotate-to-left.png').subsample(15,15)
    btn_rotate_left = Button(btns_frame, image = photo_rotate_left, command = lambda: btn_rotate_left_onClick1())
    btn_rotate_left.place(x = 335, y = 5, height = 50, width = 50)

    photo_save = PhotoImage(file = 'assets/save.png').subsample(15,15)
    btn_save = Button(btns_frame, image = photo_save, state = "disabled", command = lambda: btn_save_onClick1())
    btn_save.place(x = 390, y = 5, height = 50, width = 50)

    label_msg = Label(btns_frame, text = "")
    label_msg.place(x = 445, y = 5, height = 50, width = 300)

    btn_softwareTrig = Button(btns_frame, text = "Trig", state = "active", command = lambda: btn_softwareTrig_onClick1())
    btn_softwareTrig.place(x = 760, y = 5, height = 50, width = 50)

    canvas = Canvas(root, height=canvas_height, width=canvas_width)
    canvas.bind("<Button-1>", canvas_onClick1)
    canvas.bind("<Button-3>", canvas_onClick2)
    canvas.pack(anchor = 'nw')
    
    lineH = canvas.create_line(0, canvas_height/2, canvas_width, canvas_height/2, fill='yellow',width=1)

    lineW = canvas.create_line(canvas_width/2, 0, canvas_width/2, canvas_height, fill='yellow',width=1)

    #current_frame_rate = cam.CurrentAcquisitionFrameRate.get()
    #print (current_frame_rate)
    #num_of_frames = current_frame_rate*time_of_frames

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # create a device manager
    device_manager = gx.DeviceManager()
    dev_num, dev_info_list = device_manager.update_device_list()
    if dev_num == 0:
        print("Number of enumerated devices is 0")
        return

    # open the first device
    cam = device_manager.open_device_by_index(1)   
    #cam.DeviceReset.send_command()
    print("Camera connection OK!")
    
    if cam.PixelColorFilter.is_implemented():
        camera_colored = True
    
    #cam.Width.set(image_width)
    #cam.Height.set(image_height)

    if camera_colored:
        # get param of improving image quality
        if cam.GammaParam.is_readable():
            gamma_value = cam.GammaParam.get()
            gamma_lut = gx.Utility.get_gamma_lut(gamma_value)
        else:
            gamma_lut = None
        if cam.ContrastParam.is_readable():
            contrast_value = cam.ContrastParam.get()
            contrast_lut = gx.Utility.get_contrast_lut(contrast_value)
        else:
            contrast_lut = None
        if cam.ColorCorrectionParam.is_readable():
            color_correction_param = cam.ColorCorrectionParam.get()
        else:
            color_correction_param = 0
            
        improvement_params['gamma_lut'] = gamma_lut
        improvement_params['contrast_lut'] = contrast_lut
        improvement_params['color_correction_param'] = color_correction_param

    cam.Width.set(image_width)
    image_width = cam.Width.get()
    cam.Height.set(image_height)
    cam.OffsetX.set(image_offset_X)
    cam.OffsetY.set(image_offset_Y)
    print("Image width: " + str(image_width) + ",  height: " + str(image_height))


    cam.DeviceLinkThroughputLimit.set(400000000)
    cam.DeviceLinkThroughputLimitMode.set(gx.GxSwitchEntry.OFF)

    root.title("Состояние: Просмотр")
    set_camera_preview(cam)

    noFoto = ImageTk.PhotoImage(file = "assets/No_image_available.png") 
    cimage = canvas.create_image(canvas_width/2.0,canvas_height/2.0, anchor='center',image=noFoto)

    current_image = None
    
    while not closing_req:
        root.update()
        
        if play_pause_req:
            play_pause_req = False
            arm_state = False
            arm_state_multiple = False
            btn_arm.configure(bg = "green")
            preview_state = not preview_state
            if preview_state:
                btn_preview.configure(image = photo_pause)
                btn_save["state"] = "disabled"
                root.title("Состояние: Просмотр")
                set_camera_preview(cam)
            else:
                btn_preview.configure(image = photo_preview)
                btn_save["state"] = "active"
                root.title("Состояние: Пауза")
                set_camera_pause(cam)
        
        if arm_req:
            arm_req = False
            arm_state = True
            preview_state = False
            btn_save["state"] = "disabled"
            btn_preview.configure(image = photo_preview)
            btn_arm.configure(bg = "red")
            current_image = None
            root.title("Состояние: Ожидание пуска")
            set_camera_arm(cam)
            
        if arm_req_multiple:
            arm_req_multiple = False
            arm_state_multiple = True
            preview_state = False
            btn_save["state"] = "disabled"
            btn_preview.configure(image = photo_preview)
            btn_arm.configure(bg = "red")
            current_image = None
            raw_image = []
            multiple_images_counter = 0
            root.title("Состояние: Ожидание пуска на линии LINE0")
            set_camera_arm_multiple(cam)
            
        if save_img_req:
            save_img_req = False
            if current_image is not None:
                try:
                    current_image.save(file_save_dir)
                    print("File <" + file_save_dir + " saved")
                    label_msg.config(text = "File <" + file_save_dir + " saved")
                except Exception as e:
                    print("Can't save file: " + str(e))
                    label_msg.config(text = "Can't save file: " + str(e))
          
        if softwareTrig_req:
            softwareTrig_req = False
            try:
                cam.TriggerSource.set(gx.GxTriggerSourceEntry.SOFTWARE)
                cam.TriggerSoftware.send_command()
            except Exception as e:
                    print("Exception: " + str(e))

          
        if preview_state: 
            if camera_colored:
                current_image = get_image_from_colored_camera(cam, improvement_params)   
            else:
                current_image = get_image_from_monochrome_camera(cam)   

            if current_image is not None:
                ratio = image_width / canvas_width
                current_image = current_image.resize((canvas_width, int(image_height / ratio)))
                #current_image = current_image.resize((canvas_width, canvas_height), Image.ANTIALIAS)
    
                imgTk = ImageTk.PhotoImage(image=current_image)
                canvas.itemconfig(cimage,image=imgTk)
                current_frame_rate = cam.CurrentAcquisitionFrameRate.get()
                root.title("Состояние: Просмотр fps: " + str(current_frame_rate))
                num_of_frames = int(current_frame_rate*time_of_frames)

        if arm_state:
            if camera_colored:
                current_image = get_image_from_colored_camera(cam, improvement_params)   
            else:
                current_image = get_image_from_monochrome_camera(cam)        
            if current_image is not None:
                arm_state = False
                btn_save["state"] = "active"
                root.title("Состояние: Пауза")
                btn_arm.configure(bg = "green")
                set_camera_pause(cam)
                imgTk = ImageTk.PhotoImage(image=current_image)
                canvas.itemconfig(cimage,image=imgTk)

        if arm_state_multiple:
            current_raw_image = None
            current_raw_image = get_image_from_cam()
            if current_raw_image is not None:
                raw_image.append(current_raw_image)
                multiple_images_counter +=1
                while multiple_images_counter < num_of_frames:
                    current_raw_image = None
                    current_raw_image = get_image_from_cam()
                    if current_raw_image is not None:
                        raw_image.append(current_raw_image)
                        multiple_images_counter +=1
                else:
                    arm_state_multiple = False
                    save_multiple_images(raw_image)
                    
                    if camera_colored:
                        rgb_image = raw_image[-1].convert("RGB")#-1 means "Last item in list"
                        if rgb_image is None:
                            return None
                        
                        #rgb_image.image_improvement(improvment_pars['color_correction_param'],improvment_pars['contrast_lut'],improvment_pars['gamma_lut'])
                        numpy_image = rgb_image.get_numpy_array()
                        if numpy_image is None:
                            return None
                        img = Image.fromarray(numpy_image, 'RGB').rotate(image_angle)
                    else:#if camera mono               
                        numpy_image = raw_image[-1].get_numpy_array()
                        if numpy_image is None:
                            return None
                        img = Image.fromarray(numpy_image, 'L').rotate(image_angle)

                    if image_flip_v:
                        img = img.transpose(Image.FLIP_LEFT_RIGHT)
                    if image_flip_h:
                        img = img.transpose(Image.FLIP_TOP_BOTTOM)
                            

                    imgTk = ImageTk.PhotoImage(image=img)
                    canvas.itemconfig(cimage,image=imgTk)
                              
                    btn_save["state"] = "active"
                    root.title("Состояние: Пауза")
                    btn_arm.configure(bg = "green")
                    set_camera_pause(cam)
                
        if wbalance_req:
            wbalance_req = False
            cam.BalanceWhiteAuto.set(gx.GxAutoEntry.ONCE)
        if crosschair:
            canvas.tag_lower(cimage)
        else:
            canvas.tag_raise(cimage)
        
    print("closing = ", closing_req)
    cam.close_device()
    root.destroy()

def set_camera_pause(cam):
    print("Camera paused...")
    cam.stream_off()

def set_camera_arm(cam):
    print("Trigger mode LINE0 setting...")
    cam.stream_off()
    cam.TriggerMode.set(gx.GxSwitchEntry.OFF)
    cam.AcquisitionFrameRateMode.set(gx.GxSwitchEntry.OFF)
    cam.TriggerSource.set(gx.GxTriggerSourceEntry.LINE0)
    cam.ExposureTime.set(exposure_arming)
    cam.Gain.set(gain_arming)
    cam.stream_on()

def set_camera_preview(cam):
    #print("Continuous mode setting " + str(fps_preview) + " Hz...")
    print("Preview mode on")
    cam.stream_off()
    #cam.AcquisitionBurstFrameCount.set(1)
    #cam.TriggerSelector.set(gx.GxTriggerSelectorEntry.FRAME_START)
    #cam.AcquisitionStatusSelector.set(gx.GxAcquisitionStatusSelectorEntry.ACQUISITION_TRIGGER_WAIT)
    cam.TriggerDelay.set(0)
    cam.TriggerSource.set(gx.GxTriggerSourceEntry.SOFTWARE)
    #cam.AcquisitionMode.set(gx.GxAcquisitionModeEntry.CONTINUOUS)

    #cam.AcquisitionFrameRateMode.set(gx.GxSwitchEntry.ON)
    cam.AcquisitionFrameRateMode.set(gx.GxSwitchEntry.OFF)
    #cam.AcquisitionFrameRate.set(500)
    if (exposure_preview < 20):
        cam.ExposureTimeMode.set(gx.GxExposureTimeModeEntry.ULTRASHORT)
    else:
        cam.ExposureTimeMode.set(gx.GxExposureTimeModeEntry.STANDARD)
    cam.ExposureTime.set(exposure_preview)
    cam.Gain.set(gain_preview)
    cam.TriggerMode.set(gx.GxSwitchEntry.OFF)
    cam.stream_on()

def set_camera_arm_multiple(cam):
    print("Trigger mode multiple: " + str(num_of_frames) + " frames. Trigger input: LINE0 ...")
    cam.stream_off()
    cam.TriggerSelector.set(gx.GxTriggerSelectorEntry.FRAME_BURST_START)
    cam.AcquisitionBurstFrameCount.set(num_of_frames)

    #cam.AcquisitionFrameRateMode.set(gx.GxSwitchEntry.ON)
    cam.AcquisitionFrameRateMode.set(gx.GxSwitchEntry.OFF)
    cam.AcquisitionFrameRate.set(500)

    if (exposure_arming < 20):
        cam.ExposureTimeMode.set(gx.GxExposureTimeModeEntry.ULTRASHORT)
    else:
        cam.ExposureTimeMode.set(gx.GxExposureTimeModeEntry.STANDARD)
    cam.ExposureTime.set(exposure_arming)
    cam.Gain.set(gain_arming)
    #cam.TriggerSource.set(gx.GxTriggerSourceEntry.LINE0)
    cam.TriggerDelay.set(trigger_delay)
    cam.TriggerMode.set(gx.GxSwitchEntry.OFF)
    cam.stream_on()

def get_image_from_colored_camera(cam, improvement_pars):
    global image_flip_h
    global image_flip_v
    
    try:
        image = cam.data_stream[0].get_image()
        if image.get_status() == gx.GxFrameStatusList.INCOMPLETE:
            return None
        #while image.get_status() == gx.GxFrameStatusList.INCOMPLETE:
        #    image = cam.data_stream[0].get_image()
        #while image is None:
        #    image = cam.data_stream[0].get_image()
    except:
        return None
    
    rgb_image = image.convert("RGB")
    if rgb_image is None:
        return None
    
    rgb_image.image_improvement(improvement_pars['color_correction_param'], improvement_pars['contrast_lut'], improvement_pars['gamma_lut'])
    numpy_image = rgb_image.get_numpy_array()
    if numpy_image is None:
        return None
    img = Image.fromarray(numpy_image, 'RGB').rotate(image_angle)
    if image_flip_v:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if image_flip_h:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    #if image_width > canvas_width:
    #    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    return img

def get_image_from_monochrome_camera(cam):
    global image_flip_h
    global image_flip_v
    
    try:
        raw_image = cam.data_stream[0].get_image()
        if raw_image.get_status() == gx.GxFrameStatusList.INCOMPLETE:
            return None
    except:
        return None
    
    numpy_image = raw_image.get_numpy_array()
    if numpy_image is None:
        return None
    img = Image.fromarray(numpy_image, 'L').rotate(image_angle)
    if image_flip_v:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if image_flip_h:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    return img

def get_image_from_cam():
    current_raw_image = None
    try:
        current_raw_image = cam.data_stream[0].get_image()
        if current_raw_image.get_status() == gx.GxFrameStatusList.INCOMPLETE:
            return None
    except:
        return None
    return current_raw_image

def btn_preview_onClick1():
    print("btn_preview_onClick")
    global play_pause_req
    play_pause_req = True

def btn_arm_onClick1():
    print("btn_arm_onClick")
    #global arm_req
    #arm_req = True
    global arm_req_multiple
    if not arm_req_multiple:
        arm_req_multiple = True

def btn_wbalance_onClick1():
    print("btn_wbalance_onClick")
    global wbalance_req
    wbalance_req = True

def btn_flip_h_onClick1():
    print("btn_flip_h_onClick")
    global image_flip_h
    image_flip_h = not image_flip_h
    
def btn_flip_v_onClick1():
    print("btn_flip_v_onClick")
    global image_flip_v
    image_flip_v = not image_flip_v

def btn_rotate_right_onClick1():
    print("btn_rotate_right_onClick")
    global image_angle
    image_angle += 90
    
def btn_rotate_left_onClick1():
    print("btn_rotate_left_onClick")
    global image_angle
    image_angle -= 90

def btn_save_onClick1():
    print("btn_save_onClick")
    global save_img_req
    global file_save_dir
    file_save_dir = asksaveasfilename(initialfile = 'image.jpg', defaultextension=".jpg",filetypes=[("All Files","*.*"),("jpeg images","*.jpg")])  
    if file_save_dir != "":
        save_img_req = True

def btn_softwareTrig_onClick1():
    print("btn_softwareTrig_onClick")
    global softwareTrig_req
    softwareTrig_req = True

#left mouse button click
def canvas_onClick1(event):
    print ("on canvas clicked at", event.x, event.y)
    global crosschair
    crosschair = not crosschair

#right mouse button click
def canvas_onClick2(event):
    pass

def on_closing():
    global closing_req
    closing_req = True

def save_multiple_images(raw_image):

    destDir = file_save_dir + "/" + default_folder_name 
    i = 0
    if os.path.exists(destDir):
        while os.path.exists(destDir + '_' + str(i)):
            print("folder " + destDir + '_' + str(i) + " exists!")
            i += 1
        destDir = destDir + '_' + str(i)

    os.makedirs(destDir)

    with open(destDir + "/" + "pars.txt", "w") as f:
        f.write("width = " + str(image_width) + "\n")
        f.write("height = " + str(image_height) + "\n")
        f.write("offsetX = " + str(image_offset_X) + "\n")
        f.write("offsetY = " + str(image_offset_Y) + "\n")
        f.write("flipH = " + str(image_flip_h) + "\n")
        f.write("flipV = " + str(image_flip_v) + "\n")
        f.write("angle = " + str(image_angle) + "\n")
        f.write("trigger delay = " + str(trigger_delay) + "\n")
        f.write("gain = " + str(gain_arming) + "\n")
        f.write("exposure = " + str(exposure_arming))

    print("Saving images to " + destDir + " folder...")

    snum = ""
    
    start_timestamp = raw_image[0].get_timestamp()
    
    for i in range(multiple_images_counter):
        print("Frame ID: %d   Height: %d   Width: %d Time: %d"
            % (raw_image[i].get_frame_id(), raw_image[i].get_height(), raw_image[i].get_width(), raw_image[i].get_timestamp()- start_timestamp))
            
        if camera_colored:
            rgb_image = raw_image[i].convert("RGB")#-1 means "Last item in list"
            if rgb_image is None:
                return None
                
            #rgb_image.image_improvement('color_correction_param','contrast_lut', 'gamma_lut')
            numpy_image = rgb_image.get_numpy_array()
            if numpy_image is None:
                return None
            img = Image.fromarray(numpy_image, 'RGB').rotate(0)
            
        else:#if camera mono               
            numpy_image = raw_image[i].get_numpy_array()
            if numpy_image is None:
                return None
            img = Image.fromarray(numpy_image, 'L').rotate(0)



#            img = img.resize((image_height, image_height))
#            img = img.rotate(90)
#            img = img.resize((image_height, image_width))



        if image_flip_v:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if image_flip_h:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)


        num = raw_image[i].get_frame_id()
        if num < 1000:
            snum = "0"   + str(num)
        if num < 100:
            snum = "00" + str(num)
        if num < 10:
            snum = "000"  + str(num)
        
        fname = snum + " T_" + str((raw_image[i].get_timestamp() - start_timestamp)/1000.0) + " us"    
        img.save(destDir + "/" + fname+ ".jpg")
        #name = str(destDir + "/" + fname+ ".jpg")
        #raw = Image.open(name)
        #gif_images.append(raw)
        #img.save(destDir + "/" + fname+ ".bmp")
    print("Saved " + str(num_of_frames) + " images.")
    #with imageio.get_writer('animation.gif',mode='I') as writer:

    #gif_images[0].save(
      #  fp="animation.gif",
      #  save_all=True,
      #  append_images=gif_images[1:],
      #  loop=0,
       # duration=10)
    
    #clip = mp.VideoFileClip("animation.gif").set_duration(10)
    #clip.write_videofile("test222.mp4", fps = 24, preset = 'ultrafast')
    #clip = mp.ImageSequenceClip(gif_images, fps = 60)
    #clip.write_videofile("video.mp4", fps = 60)
    #clip.write_videofile("test222.mp4")


if __name__ == "__main__":
    main()
