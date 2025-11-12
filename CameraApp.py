import sys
import os
from src.camera import CameraControl, Camera
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer  ,QDateTime
from PyQt6.QtGui import QIntValidator, QPixmap, QImage, QIcon , QPen , QPainter , QColor , QTransform 
from threading import Thread
from enum import Enum
import numpy as np
import cv2
from PyQt6.QtWidgets import (
    QFrame,
    QApplication,
    QLabel,
    QLineEdit,
    QMainWindow,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QButtonGroup,
    QPushButton,
    QStackedWidget,
    QComboBox,
    QMessageBox,
    QGroupBox,
    QSizePolicy,
    QScrollArea,
    QFileDialog,
)

class CameraSettingsFrame(QWidget):
    triggerSourceChanged = pyqtSignal(str)
    def __init__(self, camera: Camera):
        super().__init__()
        self.settingsSlidersDict: dict[str, dict[QSlider, type]] = {}
        self.dependentSliders:dict[str , QSlider] = {}
        self.sliderRanges = {}
        self.camera = camera
        self.mainLayout = QVBoxLayout(self)

        self._initCameraTriggerLayout()
        self._initCameraControlLayout()
        self._initSliderLayout()

    def _initCameraTriggerLayout(self):
        triggerLayout = QVBoxLayout()
        triggerLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mainLayout.addLayout(triggerLayout)
    
        self.triggerButton = QPushButton("Trigger Button")
        self.triggerButton.setStyleSheet("font-size: 16px; font-family: monospace; padding: 5px;")
        self.triggerButton.setCheckable(True)
        triggerLayout.addWidget(self.triggerButton)

        triggerSourceLayout = QHBoxLayout()
        triggerSourceLabel = QLabel("Trigger Source")
        triggerSourceLabel.setStyleSheet("font-size : 16px")
        triggerSourceLayout.addWidget(triggerSourceLabel)

        triggerSourceList = self.camera.TriggerSource.get_range()
        triggerSources = [value["symbolic"] for value in triggerSourceList]
        self.TriggerSource = triggerSources[0]
        triggerSourceCombobox = QComboBox()
        triggerSourceCombobox.addItems(triggerSources)
        triggerSourceLayout.addWidget(triggerSourceCombobox)
        triggerSourceCombobox.currentTextChanged.connect(self.triggerSourceChanged.emit)
        triggerLayout.addLayout(triggerSourceLayout)

    def _initCameraControlLayout(self):
        cameraControlLayout = QHBoxLayout()
        cameraControlLayout.setAlignment(Qt.AlignmentFlag.AlignJustify)
        self.mainLayout.addLayout(cameraControlLayout)
        
        self.playButton = QPushButton()
        self.playButtonIcons = {False: QIcon("assets/play_button.png"), True: QIcon("assets/pause_button.png")}
        self.playButton.setCheckable(True)
        self.playButton.clicked.connect(self._togglePlayButton)
        self.playButton.setFixedSize(30,30)
        self.playButton.setIcon(self.playButtonIcons[False])
        self.playButton.setChecked(False)
        cameraControlLayout.addWidget(self.playButton)

        self.crosshairButton = QPushButton()
        crosshairIcon = QIcon("assets/crosshair.png")
        self.crosshairButton.clicked.connect(lambda checked: self.camera.switch_crosshair())
        self.crosshairButton.setIcon(crosshairIcon)
        self.crosshairButton.setFixedSize(30,30)
        cameraControlLayout.addWidget(self.crosshairButton)

        self.whiteBalanceButton = QPushButton()
        whiteBalanceIcon = QIcon("assets/white_balance.png")
        self.whiteBalanceButton.clicked.connect(lambda checked: self.camera.switch_white_balance())
        self.whiteBalanceButton.setIcon(whiteBalanceIcon)
        self.whiteBalanceButton.setFixedSize(30,30)
        cameraControlLayout.addWidget(self.whiteBalanceButton)

        self.rotateRightButton = QPushButton()
        rotateRightIcon = QIcon("assets/rotate_to_right.png")
        self.rotateRightButton.clicked.connect(lambda checked: self.camera.rotate_image_right())
        self.rotateRightButton.setIcon(rotateRightIcon)
        self.rotateRightButton.setFixedSize(30,30)
        cameraControlLayout.addWidget(self.rotateRightButton)

        self.rotateLeftButton = QPushButton()
        rotateLeftIcon = QIcon("assets/rotate_to_left.png")
        self.rotateLeftButton.clicked.connect(lambda checked: self.camera.rotate_image_left())
        self.rotateLeftButton.setIcon(rotateLeftIcon)
        self.rotateLeftButton.setFixedSize(30,30)
        cameraControlLayout.addWidget(self.rotateLeftButton)

        self.flipVerButton = QPushButton()
        flipVerIcon = QIcon("assets/flip_v.png")
        self.flipVerButton.clicked.connect(lambda checked: self.camera.flip_image_vertically())
        self.flipVerButton.setIcon(flipVerIcon)
        self.flipVerButton.setFixedSize(30,30)
        cameraControlLayout.addWidget(self.flipVerButton)

        self.flipHorButton = QPushButton()
        flipHorIcon = QIcon("assets/flip_h.png")
        self.flipHorButton.clicked.connect(lambda checked: self.camera.flip_image_horizontally())
        self.flipHorButton.setIcon(flipHorIcon)
        self.flipHorButton.setFixedSize(30,30)
        cameraControlLayout.addWidget(self.flipHorButton)


        captureModeLayout = QHBoxLayout()
        captureModeLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mainLayout.addLayout(captureModeLayout)

        self.captureModeButtonGroup = QButtonGroup()
        previewModeButton = QPushButton("Preview mode")
        previewModeButton.setCheckable(True)
        previewModeButton.setChecked(True)
        captureModeLayout.addWidget(previewModeButton)
        self.captureModeButtonGroup.addButton(previewModeButton , 0)

        triggerModeButton = QPushButton("Trigger mode")
        triggerModeButton.setCheckable(True)
        captureModeLayout.addWidget(triggerModeButton)
        self.captureModeButtonGroup.addButton(triggerModeButton , 1)


        colorModeLayout = QHBoxLayout()
        colorModeLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mainLayout.addLayout(colorModeLayout)

        self.colorModeButtonGroup = QButtonGroup()
        colorButton = QPushButton("Color")
        colorButton.setEnabled(self.camera.supportColorFormat)
        colorButton.setCheckable(self.camera.supportColorFormat)
        colorModeLayout.addWidget(colorButton)
        self.colorModeButtonGroup.addButton(colorButton, 0)

        monoButton = QPushButton("Mono")
        monoButton.setEnabled(self.camera.supportMonoFormat)
        monoButton.setCheckable(self.camera.supportMonoFormat)
        colorModeLayout.addWidget(monoButton)
        self.colorModeButtonGroup.addButton(monoButton , 1)

        if self.camera.colored:
            colorButton.setChecked(True)
        else:
            monoButton.setChecked(True)

        self.colorModeButtonGroup.buttonPressed.connect(self._switchColorMode)

    def _initSliderLayout(self):
        for setting in self.camera.settings:
            if hasattr(self.camera, setting):
                hLayout = QHBoxLayout()
                label = QLabel(setting)

                slider = QSlider(Qt.Orientation.Horizontal)
                entry = QLineEdit()
                entry.setFixedWidth(60)

                attr = getattr(self.camera, setting)
                try:
                    slider_range = attr.get_range()
                    value = int(attr.get())
                    if isinstance(attr.get(), int):
                        dataType = int
                    else:
                        dataType = float
                except:
                    if setting == "FramesQuantity":
                        slider_range = {"max": 1000, "min": 10, "inc": 1}
                        value = self.camera.FramesQuantity
                        dataType = int

                if setting == "ExposureTime" and self.camera.type != "MER":
                    slider_range["min"] = 1

                slider.setRange(int(slider_range["min"]), int(slider_range["max"]))

                step = int(slider_range["inc"])
                if step == 0:
                    step = 1
                slider.setSingleStep(step)
                
                self.settingsSlidersDict[setting] = {slider: dataType}
                slider.setValue(value)
                slider.valueChanged.connect(lambda val, ent=entry: self._onSliderChange(val, ent))

                if setting in ["Width" , "Height" , "OffsetX" , "OffsetY"]:
                    self.dependentSliders[setting] = slider
                    self.sliderRanges[setting] = slider_range
                    slider.valueChanged.connect(lambda value , stng = setting : self._onDependentSettingsChange(value , stng))
 
                validator = QIntValidator()
                entry.setValidator(validator)
                entry.setText(str(value))
                entry.returnPressed.connect(lambda sldr=slider, ntry=entry: self._onEntryChange(sldr, ntry))

                hLayout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
                hLayout.addWidget(slider, alignment=Qt.AlignmentFlag.AlignCenter)
                hLayout.addWidget(entry, alignment=Qt.AlignmentFlag.AlignRight)
                self.mainLayout.addLayout(hLayout)
        
        applyButtonLayout = QVBoxLayout()
        applyButtonLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.applyButton = QPushButton("Apply Settings")
        self.applyButton.setCheckable(False)  
        applyButtonLayout.addWidget(self.applyButton)
        self.mainLayout.addLayout(applyButtonLayout)

    def _onDependentSettingsChange(self ,value ,  setting:str):
        match setting:
            case "OffsetX":
                self._adjustResolutionSettings(value , "Width")
            case "OffsetY":
                self._adjustResolutionSettings(value , "Height")
            case "Width":
                self._adjustOffsetX(value)
            case "Height":
                self._adjustOffsetY(value)
    
    def _adjustOffsetX(self , value:int):
        widthRange = self.sliderRanges["Width"]
        widthMax = widthRange["max"]

        adjustment = widthMax - value

        offsetXSlider = self.dependentSliders["OffsetX"]
        if adjustment > 0:
            offsetXSlider.setMaximum(adjustment)

    def _adjustOffsetY(self , value):
        heightRange = self.sliderRanges["Height"]
        heightMax = heightRange["max"]

        adjustment = heightMax - value

        offsetYSlider = self.dependentSliders["OffsetY"]
        if adjustment > 0:
            offsetYSlider.setMaximum(adjustment)

    def _adjustResolutionSettings(self , value , setting:str):
        sliderRange = self.sliderRanges[setting]
        maximum = sliderRange["max"]
        minimum = sliderRange["min"]
        adjustment = maximum - value

        slider = self.dependentSliders[setting]
        if adjustment <= minimum:
            slider.setMinimum(minimum)
        else:
            slider.setMaximum(adjustment)
    


    def _onSliderChange(self, value, entry: QLineEdit):
        entry.setText(str(value))
    
    def _onEntryChange(self, slider: QSlider, entry: QLineEdit):
        text = entry.text()
        if not text:
            return

        value = int(text)
        minimum = slider.minimum()
        maximum = slider.maximum()
        step = slider.singleStep()

        if value <= minimum:
            value = minimum
        elif value >= maximum:
            value = maximum
        else:
            if step > 0 and value % step != 0:
                normalized_value = (value - minimum) / step
                value = minimum + round(normalized_value) * step
        slider.setValue(value)

    def getPreset(self):
        preset = {}
        for setting, sliderDict in self.settingsSlidersDict.items():
            for slider, dataType in sliderDict.items():
                value = slider.value()
                step = slider.singleStep()
                offset = value % step
                if offset != 0 :
                    value = value - offset
                    slider.setValue(value)
                preset[setting] = dataType(value)
        return preset

    def _togglePlayButton(self, checked):
        self.playButton.setIcon(self.playButtonIcons[checked])

    def _switchColorMode(self, button: QPushButton):
        for modeButton in self.colorModeButtonGroup.buttons():
            if button == modeButton:
                button.setChecked(True)
            else:
                button.setChecked(False)
        if button.isChecked():
            if self.colorModeButtonGroup.id(button) == 0 :
                self.camera.colored = True
            else:
                self.camera.colored = False

class SettingsWindow(QWidget):
    def __init__(self, parent, cameras: list[Camera]):
        super().__init__(parent)
        self.setMinimumHeight(680)
        self.cameraSettingsFrames: list[CameraSettingsFrame] = []
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stackedWidget = QStackedWidget()
        self.cameraDisplaySelectionGroup = QButtonGroup()
        self.cameraSettingsSelectionGroup = QButtonGroup()
        self.cameras = cameras

        self.cameraDisplaySelectionGroup.setExclusive(True)
        self.cameraSettingsSelectionGroup.setExclusive(True)

        self._initCameraDisplayLayout()
        self._initCameraSettingsLayout()
        self._initFrameViewerLayout()
        
        if cameras:
            self.stackedWidget.setCurrentIndex(0)
            self.cameraSettingsSelectionGroup.button(0).setChecked(True)

        self.setStyleSheet("""
            QPushButton {
                border: 1px solid gray;
                padding: 5px;
                background-color: #f0f0f0;
                border-radius : 50%;
            }
            QPushButton:checked {
                border: 2px solid green;
                background-color: #e0ffe0;
                
            }
            QComboBox {
                font-size: 16px;
                padding: 5px;
                border: 2px solid #cccccc;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png); 
                width: 12px;
                height: 12px;
            }
            QComboBox QListView {
                font-size: 14px;
                background-color: #f0f0f0;
                selection-background-color: #a0a0a0;
            }
            QLabel {
                font-size: 11px;
             }
        """)
    
    def _initCameraDisplayLayout(self):
        cameraDisplaySelectionLayout = QVBoxLayout()
        cameraDisplaySelectionLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.allCameraDisplayButton = QPushButton("All Cameras")
        self.allCameraDisplayButton.setCheckable(True)
        self.allCameraDisplayButton.setChecked(True)

        self.cameraDisplaySelectionGroup.addButton(self.allCameraDisplayButton, -1)
        self.allCameraDisplayButton.clicked.connect(self._onAllCameraDisplayClick)
        cameraDisplaySelectionLayout.addWidget(self.allCameraDisplayButton)

        for i in range(len(self.cameras)):
            displayCameraButton = QPushButton("Camera {}".format(i+1))
            displayCameraButton.setCheckable(True)
            self.cameraDisplaySelectionGroup.addButton(displayCameraButton, i)
            cameraDisplaySelectionLayout.addWidget(displayCameraButton)

        self.mainLayout.addLayout(cameraDisplaySelectionLayout)

    def _initCameraSettingsLayout(self):
        cameraSettingsSelectionLayout = QHBoxLayout()
        cameraSettingsSelectionLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        for i, camera in enumerate(self.cameras):
            showCameraSettingsButton = QPushButton("Camera {} Settings".format(i+1))
            showCameraSettingsButton.setCheckable(True)
            self.cameraSettingsSelectionGroup.addButton(showCameraSettingsButton, i)
            cameraSettingsSelectionLayout.addWidget(showCameraSettingsButton)

            cameraSettingsFrame = CameraSettingsFrame(camera)
            self.cameraSettingsFrames.append(cameraSettingsFrame)
            self.stackedWidget.addWidget(cameraSettingsFrame)
        self.mainLayout.addLayout(cameraSettingsSelectionLayout)
        self.mainLayout.addWidget(self.stackedWidget)
        
        self.cameraSettingsSelectionGroup.buttonClicked.connect(self._onCameraSettingsClicked)

    def _initFrameViewerLayout(self):
        frameViewerLayout = QVBoxLayout()
        frameViewerLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frameViewerButton = QPushButton()
        self.frameViewerButton.setIcon(QIcon("assets/video_editor.png"))
        frameViewerLayout.addWidget(self.frameViewerButton)
        self.mainLayout.addLayout(frameViewerLayout)

    def _onCameraSettingsClicked(self, button):
        index = self.cameraSettingsSelectionGroup.id(button)
        self.stackedWidget.setCurrentIndex(index)

    def _onAllCameraDisplayClick(self, checked):
        if checked:
            for button in self.cameraDisplaySelectionGroup.buttons():
                if button != self.allCameraDisplayButton:
                    button.setChecked(False)

class TriggerWorker(QThread):
    workerEnd = pyqtSignal()
    
    def __init__(self, camera: Camera, cameraIndex: int):
        super().__init__()
        self.camera = camera
        self.cameraIndex = cameraIndex
        self.dir = f"output/Camera{cameraIndex+1}"
        self.triggerSource = "Software"

    def run(self):
        
        try:
            if self.triggerSource == "Software":
                self.camera.TriggerSoftware.send_command()

            while self.camera.isTriggered:
                rawImage = self.camera.getRawImage()  
                if rawImage is None:
                    continue
                    
                if self.camera.type == "MER" and self.camera.FramesCaptured == 0:
                    self.camera.TriggerMode.set("OFF")

                self.camera.rawImages.append(rawImage)
                
                if self.camera.FramesCaptured + 1 >= self.camera.FramesQuantity:
                    break
                    
                self.camera.FramesCaptured += 1

            if len(self.camera.rawImages) >= 10:
                self._process_images()
                
        except Exception as e:
            print(f"Error in trigger worker {self.cameraIndex}: {e}")
        finally:
            self.stopTrigger()


    def _process_images(self):
        try:
            for i, rawImage in enumerate(self.camera.rawImages):
                if i > 0:
                    self.camera.timestamps.append(int(rawImage.get_timestamp() - self.camera.timestamps[0]) / 1000)
                else:
                    self.camera.timestamps.append(rawImage.get_timestamp())
                numpyImage = self.camera.convertRawImage(rawImage)
                self.camera.numpyImages.append(numpyImage)

                self.camera.images.append(self.camera.getImage(numpyImage))
            
            if self.camera.timestamps:
                self.camera.timestamps[0] = 0.0
                
            print(f"Camera {self.cameraIndex+1} recorded: {len(self.camera.rawImages)} frames")
            dirPath = self.checkDir()
            Thread(target=self.camera.saveImages , args=(dirPath ,) , daemon=True).start()
            
        except Exception as e:
            print(f"Error processing images: {e}")


    
    def startTrigger(self):
        try:
            if self.isRunning():
                print(f"Camera {self.cameraIndex+1} thread is already running!")
                return False
            self.camera.isTriggered = True
            
            self.camera.rawImages.clear()
            self.camera.images.clear()
            self.camera.timestamps.clear()
            self.camera.FramesCaptured = 0

            self.camera.cam.stream_off()

            self.camera.triggerSettings(self.triggerSource)

            self.camera.cam.stream_on()

            print(self.camera)

            print(f"Camera {self.cameraIndex+1} Trigger Started")
            self.start()
        except Exception as e:
            print(f"Error starting trigger: {e}")

    def stopTrigger(self):
        if not self.camera.isTriggered:
            return
        self.camera.isTriggered = False
        print(f"Stopping camera {self.cameraIndex+1} trigger...")
        self.camera.defaultSettings()
        self.camera.FramesCaptured = 0
        
        print(f"Camera {self.cameraIndex+1} trigger stopped")
        self.workerEnd.emit()
        self.wait()

    def _onTriggerSourceChange(self, triggerSource: str):
        self.triggerSource = triggerSource


    def checkDir(self ) -> str:
        dirPath = self.dir + "/"
        i = 0
        if not os.path.exists(self.dir):
            print(f"Directory ---> {str(self.dir)} does not exist")
            os.makedirs(self.dir)
        while os.path.exists(dirPath + "_" + str(i)):
            i += 1
        destPath = dirPath  + "_" + str(i)
        print(f"Results directory ---> {destPath}")
        os.makedirs(destPath)

        return destPath

class ImageWorker(QThread):
    imageReady = pyqtSignal(int, QPixmap)  
    
    def __init__(self, camera: Camera, cameraIndex: int):
        super().__init__()
        self.camera = camera
        self.cameraIndex = cameraIndex
        self.is_running = True
        
    def run(self):
        self.camera.cam.stream_on()
        self.is_running = True
        while self.is_running:
            try:
                rawImage = self.camera.getRawImage()
                if rawImage is None:
                    self.msleep(10)
                    continue

                numpyImage = self.camera.convertRawImage(rawImage)
                pixmap = self.numpyToPixmap(numpyImage)
                if self.camera.crosshairEnabled:
                    pixmap = self.addCrosshair(pixmap)
                if self.camera.imageAngle != 0 :
                    pixmap = self.rotateImage(pixmap , self.camera.imageAngle)
                if self.camera.flipHorEnabled or self.camera.flipVerEnabled:
                    pixmap = self.flipImage(pixmap)
                if pixmap:
                    self.imageReady.emit(self.cameraIndex, pixmap)
                self.msleep(10)
            except Exception as e:
                self.msleep(100)
    
    def stop(self):
        self.is_running = False
        self.wait()


    def numpyToPixmap(self, numpyImage):
        try:
            if numpyImage is None:
                return None
                
            if numpyImage.ndim == 2:
                height, width = numpyImage.shape
                bytes_per_line = width
                q_image = QImage(numpyImage.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
            elif numpyImage.ndim == 3 and numpyImage.shape[2] == 3:
                height, width, channels = numpyImage.shape
                bytes_per_line = 3 * width
                q_image = QImage(numpyImage.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            else:
                print(f"Unsupported image format: {numpyImage.shape}")
                return None
                
            return QPixmap.fromImage(q_image)
        except Exception as e:
            print(f"Error converting numpy to pixmap: {e}")
            return None

    def addCrosshair(self , pixmap:QPixmap):
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor(255 , 0 , 0))
        pen.setWidth(3)
        painter.setPen(pen)

        width = pixmap.width()
        height = pixmap.height()
        x = int(width/2)
        y = int(height/2)

        painter.drawLine(0 , y , width , y)
        painter.drawLine(x , 0 , x , height)
        painter.end()

        return pixmap

    def rotateImage(self , pixmap:QPixmap , angle):
        return pixmap.transformed(QTransform().rotate(angle))
    
    def flipImage(self , pixmap:QPixmap):
        flipped_image = QImage(pixmap).mirrored(horizontal=self.camera.flipHorEnabled , vertical=self.camera.flipVerEnabled)
        return pixmap.fromImage(flipped_image)
    
class ImageWindow(QVBoxLayout):
    def __init__(self, parent, cameras: list[Camera]):
        super().__init__(parent)
        self.displayImagesLabels: list[QLabel] = []
        self.displayWidgets = []
        self.fpsLabels:list[QLabel] = []
        self.cameras = cameras

        self.stackedWidget = QStackedWidget()
        self.stackedWidget.setStyleSheet("border : 1px solid ; ")
        self.addWidget(self.stackedWidget)

        self.allCamerasWidget = QWidget()
        self.allCamerasLayout = QVBoxLayout(self.allCamerasWidget)
        self.stackedWidget.addWidget(self.allCamerasWidget)

        self.singleCameraWidget = QWidget()
        self.singleCameraLayout = QVBoxLayout(self.singleCameraWidget)
        self.stackedWidget.addWidget(self.singleCameraWidget)
        
        for i in range(len(cameras)):
            cameraWidget = QWidget()
            cameraWidget.setStyleSheet("""
                QWidget {
                    background-color: #252525;
                    border: 2px solid #444444;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            cameraLayout = QVBoxLayout(cameraWidget)

            cameraLabel = QLabel(f"Camera {i+1}")
            cameraLabel.setStyleSheet("""
                QLabel {
                    color: #FF9800;
                    font-weight: bold;
                    background-color: #333333;
                    padding: 2px 6px;
                    border-radius: 3px;
                    border: 1px solid #444444;
                }
            """)

            cameraLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cameraLabel.setMaximumHeight(20)


            imageLabel = QLabel()
            imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            imageLabel.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #3c3c3c, stop: 1 #2b2b2b);
                    border: 2px solid #555555;
                    border-radius: 6px;
                    min-height: 150px;
                }
            """)
            imageLabel.setMinimumSize(200, 150)

            fpsLabel = QLabel("FPS : 24.0")
            fpsLabel.setMaximumHeight(20)
            fpsLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fpsLabel.setStyleSheet("""
                QLabel {
                    color: #FF9800;
                    font-weight: bold;
                    background-color: #333333;
                    padding: 2px 6px;
                    border-radius: 3px;
                    border: 1px solid #444444;
                }
            """)


            cameraLayout.addWidget(cameraLabel)
            cameraLayout.addWidget(imageLabel)
            cameraLayout.addWidget(fpsLabel)

            self.fpsLabels.append(fpsLabel)
            self.displayImagesLabels.append(imageLabel)
            self.displayWidgets.append(cameraWidget)
            self.allCamerasLayout.addWidget(cameraWidget)

        self.setDisplayMode("All", 0)

    def setDisplayMode(self, mode: str, cameraIndex: int):
        if mode == "All":
            for widget in self.displayWidgets:
                self.allCamerasLayout.addWidget(widget)
            self.stackedWidget.setCurrentIndex(0)
        elif mode == "Single" and 0 <= cameraIndex < len(self.displayImagesLabels):
            self.clearLayout(self.singleCameraLayout)
            self.singleCameraLayout.addWidget(self.displayWidgets[cameraIndex])
            self.stackedWidget.setCurrentIndex(1)

    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)



    def updateImage(self, camera_index: int, pixmap: QPixmap):
        if 0 <= camera_index < len(self.displayImagesLabels):
            scaled_pixmap = pixmap.scaled(
                self.displayImagesLabels[camera_index].size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.displayImagesLabels[camera_index].setPixmap(scaled_pixmap)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1280, 720)
        self.cameraControl = CameraControl()
        self.imageWorkers = [] 
        self.triggerWorkers = []

        self.stackedWidget = QStackedWidget()
        mainWidget = QWidget()
        self.frameViewer = FrameViewer(len(self.cameraControl.cameras))
        self.frameViewer.cameraAppButton.clicked.connect(self._showCameraApp)

        self.stackedWidget.addWidget(mainWidget)
        self.stackedWidget.addWidget(self.frameViewer)

        layout = QHBoxLayout(mainWidget)

        leftWidget = QWidget()
        leftWidget.setMinimumSize(400, 720)
        self.imageLayout = ImageWindow(leftWidget, self.cameraControl.cameras)

        rightWidget = QWidget()
        rightWidget.setFixedWidth(300)

        layout.addWidget(leftWidget)
        layout.addWidget(rightWidget)
        self.settingsWindow = SettingsWindow(rightWidget, self.cameraControl.cameras)

        self.settingsWindow.allCameraDisplayButton.clicked.connect(lambda checked: self.imageLayout.setDisplayMode("All", 0))
        self.settingsWindow.cameraDisplaySelectionGroup.buttonClicked.connect(lambda button: self.imageLayout.setDisplayMode("Single", self.settingsWindow.cameraDisplaySelectionGroup.id(button)))
        
        self.settingsWindow.frameViewerButton.clicked.connect(self._showFrameViewer)
        self._initCameraWorkers()

        self.setCentralWidget(self.stackedWidget)
        self.stackedWidget.setCurrentIndex(0)
        self.setWindowTitle("Camera Application")

    def _initCameraWorkers(self):
        for i, camera in enumerate(self.cameraControl.cameras):
            imageWorker = ImageWorker(camera, i)
            imageWorker.imageReady.connect(self._onImageReady)
            self.imageWorkers.append(imageWorker)

            triggerWorker = TriggerWorker(camera, i )
            triggerWorker.workerEnd.connect(lambda idx=i: self._onTriggerWorkerFinished(idx))
            self.triggerWorkers.append(triggerWorker)
            
            settings_frame = self.settingsWindow.cameraSettingsFrames[i]
            settings_frame.playButton.clicked.connect(lambda checked, idx=i: self._toggleCameraRecording(checked, idx))
            settings_frame.applyButton.clicked.connect(lambda checked, idx=i: self._applyCameraSettings(idx))
            settings_frame.triggerButton.clicked.connect(lambda checked , idx = i : self._toggleCameraTrigger(checked , idx))
            settings_frame.triggerSourceChanged.connect(triggerWorker._onTriggerSourceChange)
            settings_frame.captureModeButtonGroup.buttonClicked.connect(lambda btn , idx = i : self._toggleCaptureMode(btn , idx))

    def startCameraTrigger(self, cameraIndex:int):
        triggerWorker = self.triggerWorkers[cameraIndex]
        imageWorker = self.imageWorkers[cameraIndex]
        imageWorker.stop()
        settingsFrame = self.settingsWindow.cameraSettingsFrames[cameraIndex]
        settingsFrame.captureModeButtonGroup.button(1).setChecked(True)
        success = triggerWorker.startTrigger()
        if not success:
            self.settingsWindow.cameraSettingsFrames[cameraIndex].triggerButton.setChecked(False)

    def _toggleCameraTrigger(self, checked, cameraIndex: int):
        try:
            triggerWorker = self.triggerWorkers[cameraIndex]
            if checked:
                imageWorker = self.imageWorkers[cameraIndex]
                imageWorker.stop()
                settingsFrame = self.settingsWindow.cameraSettingsFrames[cameraIndex]
                settingsFrame.captureModeButtonGroup.button(1).setChecked(True)
                triggerWorker.startTrigger()
            else:
                triggerWorker.stopTrigger()
        except Exception as e:
            self.settingsWindow.cameraSettingsFrames[cameraIndex].triggerButton.setChecked(False)

    def _onImageReady(self, cameraIndex: int, pixmap: QPixmap):
        self.imageLayout.updateImage(cameraIndex, pixmap)

    def _onTriggerWorkerFinished(self,  cameraIndex: int):
        images = self.cameraControl.cameras[cameraIndex].numpyImages
        timestamps = self.cameraControl.cameras[cameraIndex].timestamps
        if len(images) >= 10:
            self.frameViewer.load_camera_data(cameraIndex , images , timestamps)
            self._showFrameViewer()
        QTimer.singleShot(0, lambda: self._update_trigger_ui(cameraIndex))


    def _update_trigger_ui(self, cameraIndex: int):
        settings_frame = self.settingsWindow.cameraSettingsFrames[cameraIndex]
        settings_frame.triggerButton.setChecked(False)
        
        if settings_frame.playButton.isChecked():
            self._toggleCameraRecording(True , cameraIndex)


    def _toggleCaptureMode(self , button:QPushButton , camerIndex:int ):
        def switchMode(camera:Camera , mode:str):
            if mode == "preview":
                camera.previewMode()
            elif mode =="trigger":
                camera.triggerMode()
            
        settingsFrame = self.settingsWindow.cameraSettingsFrames[camerIndex]
        camera = self.cameraControl.cameras[camerIndex]
        if  settingsFrame.captureModeButtonGroup.id(button) == 0 :
            switchMode(camera , "preview")
        else:
            switchMode(camera , "trigger")



    def _toggleCameraRecording(self, checked: bool, cameraIndex: int):
        try:
            worker = self.imageWorkers[cameraIndex]
            if checked and not worker.isRunning():
                worker.start()
                print(f"Camera {cameraIndex + 1} recording")
            elif not checked and worker.isRunning():
                worker.stop()
                print(f"Camera {cameraIndex + 1} stopped")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle camera capture: {str(e)}")

    def _applyCameraSettings(self, cameraIndex: int):
        try:
            camera = self.cameraControl.cameras[cameraIndex]
            settingsPane = self.settingsWindow.cameraSettingsFrames[cameraIndex]
            fpsLabel = self.imageLayout.fpsLabels[cameraIndex]
            preset = settingsPane.getPreset()
            
            triggerPreset = preset.copy()
            defaultPreset = preset.copy()
            defaultPreset["FrameRate"] = float(24)
            previewPreset = defaultPreset.copy()
            previewPreset["ExposureTime"] = float(40000)

            camera.presetManager.changePreset("default", defaultPreset)
            camera.presetManager.changePreset("preview", previewPreset)
            camera.presetManager.changePreset("trigger", triggerPreset)
            print(f"Applying preset for camera {cameraIndex + 1}: {triggerPreset}")

            camera.cam.stream_off()
            camera.applyPreset(triggerPreset)
            camera.cam.stream_on()

            fpsLabel.setText(str(camera.CurrentFrameRate.get()))
            
            settingsPane.captureModeButtonGroup.button(1).setChecked(True)
            QMessageBox.information(self, "Success", "Settings applied successfully!")
            
        except Exception as e:
            print(f"Error applying camera settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {str(e)}")
            self.settingsWindow.cameraSettingsFrames[cameraIndex].playButton.click()

    def _showCameraApp(self):
        self.stackedWidget.widget(0).setFocus()
        self.stackedWidget.setCurrentIndex(0)

    def _showFrameViewer(self):
        self.stackedWidget.widget(1).setFocus()
        self.stackedWidget.setCurrentIndex(1)

    def closeEvent(self, event):
        for worker in self.imageWorkers:
            if worker and worker.isRunning():
                worker.stop()
                worker.wait()
        for triggerWorker in self.triggerWorkers:
            if triggerWorker and triggerWorker.isRunning():
                triggerWorker.stop()
                triggerWorker.wait()
        for camera in self.cameraControl.cameras:
            camera.close()
        event.accept()


class VideoDirection(Enum):
    forward = 1
    backward = -1

class FrameWorker(QThread):
    frame_ready = pyqtSignal(int, QPixmap, str) 
    
    def __init__(self, camera_index, cam_attributes):
        super().__init__()
        self.camera_index = camera_index
        self.cam_attributes = cam_attributes
        self.is_running = False
        self.video_direction = VideoDirection.forward
        self.current_index = 0
        self.target_fps = 10
        self.frame_delay_ms = 1000 // self.target_fps
        self.last_frame_time = 0

    def run(self):
        self.is_running = True
        while self.is_running:
            if not self.cam_attributes or not self.cam_attributes["images"]:
                self.msleep(16)  
                continue
                
            current_time = QDateTime.currentMSecsSinceEpoch()
            if current_time - self.last_frame_time < self.frame_delay_ms:
                self.msleep(1)  
                continue
                
            self.last_frame_time = current_time
            self._process_frame()

    def _process_frame(self):
        images = self.cam_attributes["images"]
        timestamps = self.cam_attributes["timestamps"]
        
        if not images or self.current_index >= len(images):
            return
            
        if self.video_direction == VideoDirection.forward:
            self.current_index = (self.current_index + 1) % len(images)
        else:
            self.current_index = (self.current_index - 1) % len(images)
        
        frame = images[self.current_index]
        timestamp = timestamps[self.current_index]
        
        pixmap = self._numpy_to_pixmap(frame)
        if pixmap:
            scaled_pixmap = self._get_scaled_pixmap(pixmap)
            info_text = f"Frame: {self.current_index}\nTime: {timestamp}"
            self.frame_ready.emit(self.camera_index, scaled_pixmap, info_text)

    def _numpy_to_pixmap(self, numpy_image):
        if numpy_image is None:
            return None
            
        try:
            if numpy_image is None:
                return None
                
            if numpy_image.ndim == 2:
                height, width = numpy_image.shape
                bytes_per_line = width
                q_image = QImage(numpy_image.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
            elif numpy_image.ndim == 3 and numpy_image.shape[2] == 3:
                height, width, channels = numpy_image.shape
                bytes_per_line = 3 * width
                q_image = QImage(numpy_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            return QPixmap.fromImage(q_image)
            
        except Exception as e:
            print(f"Error converting numpy to pixmap: {e}")
            return None

    def _get_scaled_pixmap(self, pixmap):
        label_size = self.cam_attributes["imageLabel"].size()
        if (hasattr(self, '_cached_size') and 
            hasattr(self, '_cached_pixmap') and
            self._cached_size == label_size and
            self._cached_pixmap is not None):
            return self._cached_pixmap
            
        scaled_pixmap = pixmap.scaled(
            label_size, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self._cached_size = label_size
        self._cached_pixmap = scaled_pixmap
        return scaled_pixmap

    def change_video_direction(self, direction: VideoDirection):
        self.video_direction = direction

    def set_fps(self, fps):
        self.target_fps = max(1, min(30, fps))  
        self.frame_delay_ms = 1000 // self.target_fps

    def stop(self):
        self.is_running = False
        self.wait(500) 


class FrameViewer(QWidget):
    def __init__(self, cameras_amount: int):
        super().__init__()
        self.cameras_amount = cameras_amount
        self.camera_attributes = []
        self.frame_workers = []
        self.camera_selected_index = -2 
        self.is_playing = False
        
        self._setupStyles()
        self._setupUi()
        self._setup_workers()

    def _setupStyles(self):
        self.colors = {
            'primary': '#4361ee',
            'secondary': '#3a0ca3', 
            'accent': '#f72585',
            'warning': '#f8961e',
            'background': '#ffffff',
            'surface': '#f8f9fa',
            'text_primary': '#212529',
            'border': '#dee2e6'
        }
        
        self.setStyleSheet(f"""
            QPushButton {{
                font-size: 14px;
                border: 1px solid {self.colors['border']};
                font-family: monospace;
                padding: 8px 12px;
                border-radius: 5px;
                background-color: {self.colors['background']};
            }}
            QPushButton:checked {{
                border: 2px solid {self.colors['primary']};
                background-color: #e0ffe0;
            }}
            QPushButton:hover {{
                background-color: {self.colors['surface']};
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {self.colors['border']};
                height: 8px;
                background: {self.colors['surface']};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {self.colors['primary']};
                border: 1px solid {self.colors['border']};
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }}
        """)

    def _setupUi(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.left_widget = QWidget()
        left_layout = QVBoxLayout(self.left_widget)
        main_layout.addWidget(self.left_widget)

        self.right_widget = QWidget()
        self.right_widget.setFixedWidth(300)
        self.right_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.colors['surface']};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        main_layout.addWidget(self.right_widget)
        self.stacked_widget = QStackedWidget()
        left_layout.addWidget(self.stacked_widget)

        self.all_frames_widget = QWidget()
        self.all_frames_layout = QVBoxLayout(self.all_frames_widget)
        self.all_frames_layout.setContentsMargins(10, 10, 10, 10)

        self.single_frame_widget = QWidget()
        self.single_frame_layout = QVBoxLayout(self.single_frame_widget)
        self.single_frame_layout.setContentsMargins(10,10,10,10)

        self.stacked_widget.addWidget(self.all_frames_widget)
        self.stacked_widget.addWidget(self.single_frame_widget)
        self.stacked_widget.setCurrentIndex(0)

        self._initViewLayout()
        self._initControlLayout()

    def _initViewLayout(self):
        self.frame_widgets = []

        for i in range(self.cameras_amount):
            frame_widget = QWidget()
            
            frame_layout = QVBoxLayout(frame_widget)
            frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            camera_label = QLabel(f"Camera {i+1}")
            camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            camera_label.setFixedHeight(25)
            camera_label.setStyleSheet(f"font-weight: bold; color: {self.colors['text_primary']};")

            image_label = QLabel()
            image_label.setPixmap(QPixmap("assets/no_image.png"))
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setMinimumSize(320, 240)
            image_label.setSizePolicy(QSizePolicy.Policy.Expanding , QSizePolicy.Policy.Expanding)
            image_label.setStyleSheet(f"border: 1px solid {self.colors['border']}; background-color: black;")

            info_label = QLabel("Frame: None\nTime: None")
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_label.setFixedHeight(40)
            info_label.setStyleSheet(f"color: {self.colors['text_primary']};")

            frame_layout.addWidget(camera_label)
            frame_layout.addWidget(image_label)
            frame_layout.addWidget(info_label)

            self.all_frames_layout.addWidget(frame_widget)
            self.frame_widgets.append(frame_widget)

            self.camera_attributes.append({
                "imageLabel": image_label,
                "infoLabel": info_label,
                "images": [],
                "timestamps": [],
                "currentIndex": 0,
            })

    def _setup_workers(self):
        for i in range(self.cameras_amount):
            worker = FrameWorker(i, self.camera_attributes[i])
            worker.frame_ready.connect(self._on_frame_ready)
            self.frame_workers.append(worker)

    def _initControlLayout(self):
        main_control_layout = QVBoxLayout(self.right_widget)
        main_control_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_control_layout.setSpacing(15)

        camera_group = QGroupBox("Camera Selection")
        camera_group.setAlignment(Qt.AlignmentFlag.AlignTop)
        camera_layout = QVBoxLayout(camera_group)
        
        self.camera_selection_group = QButtonGroup()
        self.camera_selection_group.setExclusive(True)

        all_cameras_btn = QPushButton("All Cameras")
        all_cameras_btn.setCheckable(True)
        all_cameras_btn.setChecked(True)
        self.camera_selection_group.addButton(all_cameras_btn, -2)
        camera_layout.addWidget(all_cameras_btn)

        for i in range(self.cameras_amount):
            camera_btn = QPushButton(f"Camera {i+1}")
            camera_btn.setCheckable(True)
            self.camera_selection_group.addButton(camera_btn, i)
            camera_layout.addWidget(camera_btn)

        main_control_layout.addWidget(camera_group)

        fps_group = QGroupBox("Playback Speed")
        fps_group.setAlignment(Qt.AlignmentFlag.AlignTop)
        fps_layout = QVBoxLayout(fps_group)
        
        fps_control_layout = QHBoxLayout()
        fps_label = QLabel("FPS:")
        self.fps_value_label = QLabel("10")
        
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 30)
        self.fps_slider.setValue(10)
        self.fps_slider.valueChanged.connect(self._on_fps_changed)
        
        fps_control_layout.addWidget(fps_label)
        fps_control_layout.addWidget(self.fps_slider)
        fps_control_layout.addWidget(self.fps_value_label)
        fps_layout.addLayout(fps_control_layout)
        
        main_control_layout.addWidget(fps_group)

        nav_group = QGroupBox("Navigation")
        nav_group.setAlignment(Qt.AlignmentFlag.AlignTop)
        nav_layout = QVBoxLayout(nav_group)

        frame_nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("◄")
        self.prev_button.clicked.connect(self._prev_frame)
        self.next_button = QPushButton("►")
        self.next_button.clicked.connect(self._next_frame)
        
        frame_nav_layout.addWidget(self.prev_button)
        frame_nav_layout.addWidget(self.next_button)
        nav_layout.addLayout(frame_nav_layout)

        video_nav_layout = QHBoxLayout()
        self.video_direction_group = QButtonGroup()
        
        self.video_backward_btn = QPushButton("◄◄")
        self.video_backward_btn.setCheckable(True)
        
        self.toggle_video_btn = QPushButton("Play")
        self.toggle_video_btn.setCheckable(True)
        self.toggle_video_btn.clicked.connect(self._toggle_video)
        
        self.video_forward_btn = QPushButton("►►")
        self.video_forward_btn.setCheckable(True)
        self.video_forward_btn.setChecked(True)
        
        self.video_direction_group.addButton(self.video_backward_btn, 0)
        self.video_direction_group.addButton(self.video_forward_btn, 1)
        self.video_direction_group.buttonClicked.connect(self._on_video_direction_changed)
        
        video_nav_layout.addWidget(self.video_backward_btn)
        video_nav_layout.addWidget(self.toggle_video_btn)
        video_nav_layout.addWidget(self.video_forward_btn)
        nav_layout.addLayout(video_nav_layout)

        main_control_layout.addWidget(nav_group)

        self.camera_selection_group.buttonClicked.connect(self._on_camera_selection)


        export_group = QGroupBox("Export")
        export_group.setAlignment(Qt.AlignmentFlag.AlignTop)
        export_layout = QVBoxLayout(export_group)
        
        self.export_button = QPushButton("Export Video")
        self.export_button.clicked.connect(self.exportVideo)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        export_layout.addWidget(self.export_button)
        main_control_layout.addWidget(export_group)


        deleteButtonLayout = QVBoxLayout()
        deleteButtonLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        deleteImagesButton = QPushButton("Delete Images")
        deleteImagesButton.clicked.connect(self._deleteImages)
        deleteButtonLayout.addWidget(deleteImagesButton)
        main_control_layout.addLayout(deleteButtonLayout)


        cameraAppLayout = QVBoxLayout()
        cameraAppLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cameraAppButton = QPushButton()
        self.cameraAppButton.setIcon(QIcon("assets/camera.png"))
        cameraAppLayout.addWidget(self.cameraAppButton)
        main_control_layout.addLayout(cameraAppLayout)

        

    def _on_frame_ready(self, camera_index, pixmap, info_text):
        if camera_index < len(self.camera_attributes):
            cam_attr = self.camera_attributes[camera_index]
            cam_attr["imageLabel"].setPixmap(pixmap)
            cam_attr["infoLabel"].setText(info_text)

    def _on_camera_selection(self, button):
        button_id = self.camera_selection_group.id(button)
        self.camera_selected_index = button_id
        
        if button_id == -2:  
            self.clear_layout(self.all_frames_layout)
            for widget in self.frame_widgets:
                self.all_frames_layout.addWidget(widget)
            self.stacked_widget.setCurrentIndex(0)
        else:  
            self._show_single_camera(button_id)

    def _show_single_camera(self, camera_index):
        self.clear_layout(self.single_frame_layout)
        if camera_index < len(self.frame_widgets):
            self.single_frame_layout.addWidget(self.frame_widgets[camera_index])
        self.stacked_widget.setCurrentIndex(1)

    def _on_fps_changed(self, value):
        self.fps_value_label.setText(str(value))
        for worker in self.frame_workers:
            worker.set_fps(value)

    def _on_video_direction_changed(self, button):
        button_id = self.video_direction_group.id(button)
        direction = VideoDirection.backward if button_id == 0 else VideoDirection.forward
        for worker in self.frame_workers:
            worker.change_video_direction(direction)

    def _prev_frame(self):
        self._step_frame(VideoDirection.backward)

    def _next_frame(self):
        self._step_frame(VideoDirection.forward)

    def _step_frame(self, direction):
        if self.is_playing:
            self._toggle_video(False)
            self.toggle_video_btn.setChecked(False)

        if self.camera_selected_index == -2:
            for i, cam_attr in enumerate(self.camera_attributes):
                self._update_frame_manual(cam_attr, direction, i)
        else: 
            cam_attr = self.camera_attributes[self.camera_selected_index]
            self._update_frame_manual(cam_attr, direction, self.camera_selected_index)

    def _update_frame_manual(self, cam_attr, direction, worker_index):
        images = cam_attr["images"]
        timestamps = cam_attr["timestamps"]
        
        if not images:
            return
            
        current_index = cam_attr["currentIndex"]
        new_index = (current_index + direction.value) % len(images)
        cam_attr["currentIndex"] = new_index
        
        worker = self.frame_workers[worker_index]
        pixmap = worker._numpy_to_pixmap(images[new_index])
        if pixmap:
            scaled_pixmap = worker._get_scaled_pixmap(pixmap)
            cam_attr["imageLabel"].setPixmap(scaled_pixmap)
            cam_attr["infoLabel"].setText(f"Frame: {new_index}\nTime: {timestamps[new_index]}")

    def _toggle_video(self, checked):
        self.is_playing = checked
        
        if checked:
            self.toggle_video_btn.setText("Pause")
            for worker in self.frame_workers:
                if not worker.isRunning():
                    worker.start()
        else:
            self.toggle_video_btn.setText("Play")
            for worker in self.frame_workers:
                worker.stop()

    def load_camera_data(self, camera_index, images, timestamps):
        if 0 <= camera_index < len(self.camera_attributes):
            self.camera_attributes[camera_index]["images"] = images
            self.camera_attributes[camera_index]["timestamps"] = timestamps
            self.camera_attributes[camera_index]["currentIndex"] = 0
            
            if images:
                worker = self.frame_workers[camera_index]
                pixmap = worker._numpy_to_pixmap(images[0])
                if pixmap:
                    scaled_pixmap = worker._get_scaled_pixmap(pixmap)
                    self.camera_attributes[camera_index]["imageLabel"].setPixmap(scaled_pixmap)
                    self.camera_attributes[camera_index]["infoLabel"].setText(
                        f"Frame: 0\nTime: {timestamps[0]}"
                    )
            
            self.update_export_button_state()

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self._prev_frame()
            event.accept()
        elif event.key() == Qt.Key.Key_Right:
            self._next_frame()
            event.accept()
        elif event.key() == Qt.Key.Key_Space:
            self.toggle_video_btn.click()
            event.accept()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        for worker in self.frame_workers:
            worker.stop()
        event.accept()
    
    def exportVideo(self):
        def save_video(images: list, fps: int, output_file: str):
            if not images or len(images) == 0:
                return False

            try:
                if images[0].ndim == 2:  
                    height, width = images[0].shape
                    is_color = False
                else:  
                    height, width, channels = images[0].shape
                    is_color = True

                fourcc_codes = ['mp4v', 'avc1', 'X264', 'MJPG']
                video_writer = None
                
                for codec in fourcc_codes:
                    try:
                        fourcc = cv2.VideoWriter_fourcc(*codec)
                        video_writer = cv2.VideoWriter(output_file, fourcc, fps, (width, height), isColor=is_color)
                        if video_writer.isOpened():
                            print(f"Using codec: {codec}")
                            break
                        else:
                            video_writer = None
                    except Exception as e:
                        print(f"Codec {codec} failed: {e}")
                        video_writer = None

                if video_writer is None:
                    print("Cannot initialize any video codec.")
                    return False

                for i, image in enumerate(images):
                    try:
                        if image.ndim == 2: 
                            if image.dtype != np.uint8:
                                image = np.uint8(image)
                            frame = image
                        else: 
                            if image.shape[2] == 3:
                                frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                            else:
                                frame = image[:, :, :3]
                                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        
                        video_writer.write(frame)
                        
                        if i % 10 == 0:
                            print(f"Written {i+1}/{len(images)} frames")
                            
                    except Exception as e:
                        print(f"Error writing frame {i}: {e}")
                        continue

                video_writer.release()
                print(f"Video successfully saved to: {output_file}")
                
            except Exception as e:
                print(f"Error in video export: {e}")
                if 'video_writer' in locals() and video_writer is not None:
                    video_writer.release()

        fps = self.fps_slider.value()
        exported_count = 0
        
        if self.camera_selected_index == -2:  
            cameras_to_export = range(len(self.camera_attributes))
        else:  
            cameras_to_export = [self.camera_selected_index]

        for i in cameras_to_export:
            attr = self.camera_attributes[i]
            images = attr["images"]
            
            if not images or len(images) == 0:
                QMessageBox.warning(self, "Export Error", 
                                  f"No images available for Camera {i+1}")
                continue

            default_dir = f"output/Camera{i+1}"
            os.makedirs(default_dir, exist_ok=True)
            default_filename = f"camera{i+1}_frames{len(images)}_fps{fps}.mp4"
            default_path = os.path.join(default_dir, default_filename)

            output_file, selected_filter = QFileDialog.getSaveFileName(
                self,
                f"Export Video - Camera {i+1}",
                default_path,
                "MP4 files (*.mp4);;All files (*)"
            )
            
            if not output_file:
                continue  

            if not output_file.lower().endswith('.mp4'):
                output_file += '.mp4'


            


            thread = Thread(target=save_video, 
                          args=(images, fps, output_file),
                          daemon=True)
            thread.start()
            
            exported_count += 1

        if exported_count == 0:
            QMessageBox.information(self, "Export", "No videos were exported.")


    def _deleteImages(self):
        def handleDeleting(attr):
            attr["images"].clear()
            attr["timestamps"].clear()
            attr["imageLabel"].setPixmap(QPixmap("assets/no_image.png"))
            attr["infoLabel"].setText("Frame : None\nTime : None")

        if self.camera_selected_index == -2:
            for attr in self.camera_attributes:
                handleDeleting(attr)
        else:
            attr = self.camera_attributes[self.camera_selected_index]
            handleDeleting(attr)

    def update_export_button_state(self):
        has_data = False
        for attr in self.camera_attributes:
            if attr["images"] and len(attr["images"]) > 0:
                has_data = True
                break
        
        self.export_button.setEnabled(has_data)
        
        if has_data:
            self.export_button.setToolTip("Export captured frames to MP4 video")
        else:
            self.export_button.setToolTip("No frame data available for export")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()