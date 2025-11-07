import sys
import os
from src.camera import CameraControl, Camera
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer  
from PyQt6.QtGui import QIntValidator, QPixmap, QImage, QIcon , QPen , QPainter , QColor , QTransform 
from threading import Thread
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
    QSizePolicy,
    QScrollArea
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
    workerEnd = pyqtSignal(bool)
    
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

            if len(self.camera.rawImages) > 10:
                self._process_images()
                
        except Exception as e:
            print(f"Error in trigger worker {self.cameraIndex}: {e}")
        finally:
            self._cleanup()
            self.stopTrigger()


    def _process_images(self):
        try:
            for i, rawImage in enumerate(self.camera.rawImages):
                if i > 0:
                    self.camera.timestamps.append(int(rawImage.get_timestamp() - self.camera.timestamps[0]) / 1000)
                else:
                    self.camera.timestamps.append(rawImage.get_timestamp())
                self.camera.images.append(self.camera.getImage(self.camera.convertRawImage(rawImage)))
            
            if self.camera.timestamps:
                self.camera.timestamps[0] = 0.0
                
            print(f"Camera {self.cameraIndex+1} recorded: {len(self.camera.rawImages)} frames")
            dirPath = self.checkDir()
            Thread(target=self.camera.saveImages , args=(dirPath ,) , daemon=True).start()
            
        except Exception as e:
            print(f"Error processing images: {e}")

    def _cleanup(self):
        try:
            
            self.camera.defaultSettings()
            self.camera.FramesCaptured = 0
            
            self.workerEnd.emit(True)
        except Exception as e:
            self.workerEnd.emit(False)

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
            return False
        return True

    def stopTrigger(self):
        if not self.camera.isTriggered:
            return
            
        print(f"Stopping camera {self.cameraIndex+1} trigger...")
        self.camera.isTriggered = False
        self.camera.defaultSettings()

        self.wait()
        
        print(f"Camera {self.cameraIndex+1} trigger stopped")

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
        frameViewerWidget = FrameViewer(len(self.cameraControl.cameras))

        self.stackedWidget.addWidget(mainWidget)
        self.stackedWidget.addWidget(frameViewerWidget)

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
            triggerWorker.workerEnd.connect(lambda success, idx=i: self._onTriggerWorkerFinished(success, idx))
            self.triggerWorkers.append(triggerWorker)
            
            settings_frame = self.settingsWindow.cameraSettingsFrames[i]
            settings_frame.playButton.clicked.connect(lambda checked, idx=i: self._toggleCameraRecording(checked, idx))
            settings_frame.applyButton.clicked.connect(lambda checked, idx=i: self._applyCameraSettings(idx))
            settings_frame.triggerButton.clicked.connect(lambda checked , idx = i : self._toggleCameraTrigger(checked , idx))
            settings_frame.triggerSourceChanged.connect(triggerWorker._onTriggerSourceChange)
            settings_frame.captureModeButtonGroup.buttonClicked.connect(lambda btn , idx = i : self._toggleCaptureMode(btn , idx))

    def _toggleCameraTrigger(self, checked, index: int):
        try:
            triggerWorker = self.triggerWorkers[index]
            if checked:
                settingsFrame = self.settingsWindow.cameraSettingsFrames[index]
                settingsFrame.captureModeButtonGroup.button(1).setChecked(True)
                success = triggerWorker.startTrigger()
                if not success:
                    self.settingsWindow.cameraSettingsFrames[index].triggerButton.setChecked(False)
            else:
                triggerWorker.stopTrigger()
        except Exception as e:
            self.settingsWindow.cameraSettingsFrames[index].triggerButton.setChecked(False)

    def _onImageReady(self, cameraIndex: int, pixmap: QPixmap):
        self.imageLayout.updateImage(cameraIndex, pixmap)

    def _onTriggerWorkerFinished(self, success: bool, cameraIndex: int):
        QTimer.singleShot(0, lambda: self._update_trigger_ui(cameraIndex, success))


    def _update_trigger_ui(self, cameraIndex: int, success: bool):
        settings_frame = self.settingsWindow.cameraSettingsFrames[cameraIndex]
        settings_frame.triggerButton.setChecked(False)
        
        if success and settings_frame.playButton.isChecked():
            self._toggleCameraRecording(True, cameraIndex)

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

    def _showFrameViewer(self):
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


class FrameViewer(QWidget):
    def __init__(self, camerasAmount: int):
        super().__init__()
        self.camerasAmount = camerasAmount
        self.cameraAttributes = []
        self.cameraSelectedIndex = -1
        self.currentFrameIndex = 0
        self.isPlaying = False
        self.playDirection = 1 
        self.frameWidgets = []

        self.setStyleSheet("""QPushButton {
                                font-size : 14px;
                                border : 1px solid;
                                font-family : monospace;
                           }
                           QPushButton:checked {
                                border: 2px solid green;
                                background-color: #e0ffe0;
                
                            }""")
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

        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(10, 10, 10, 10)

        self.leftWidget = QWidget()
        leftLayout = QVBoxLayout(self.leftWidget)
        mainLayout.addWidget(self.leftWidget)

        self.rightWidget = QWidget()
        self.rightWidget.setFixedWidth(300)
        self.rightWidget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.colors['surface']};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        mainLayout.addWidget(self.rightWidget)
        self.stackedWidget = QStackedWidget()
        leftLayout.addWidget(self.stackedWidget)

        self.allFramesWidget = QWidget()
        self.allFramesLayout = QVBoxLayout(self.allFramesWidget)
        self.allFramesLayout.setSpacing(15)
        self.allFramesLayout.setContentsMargins(10, 10, 10, 10)
        
        
        self.singleFrameWidget = QWidget()
        self.singleFrameLayout = QVBoxLayout(self.singleFrameWidget)
        self.singleFrameLayout.setContentsMargins(20, 20, 20, 20)

        self.stackedWidget.addWidget(self.allFramesWidget)
        self.stackedWidget.addWidget(self.singleFrameWidget)
        self.stackedWidget.setCurrentIndex(0)

        self._initViewLayout()
        self._initControlLayout()

    def _initViewLayout(self):
        for i in range(self.camerasAmount):
            frameWidget = QWidget()
            frameLayout = QVBoxLayout(frameWidget)
            frameLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cameraLabel = QLabel(f"Camera {i+1}")
            cameraLabel.setFixedHeight(30)

            imageLabel = QLabel()

            infoLabel = QLabel("Frame : None\nTime : None")
            infoLabel.setFixedHeight(30)

            frameLayout.addWidget(cameraLabel)
            frameLayout.addWidget(imageLabel)
            frameLayout.addWidget(infoLabel)
            self.allFramesLayout.addWidget(frameWidget)

            self.frameWidgets.append(frameWidget)

            self.cameraAttributes.append({
                "imageLabel" : imageLabel,
                "infoLabel" : infoLabel,
                "images" : [],
                "timestamps" : [],
                "currentIndex" : 0,
            })

    def _initControlLayout(self):
        mainControlLayout = QVBoxLayout(self.rightWidget)
        cameraSelectionLayout = QVBoxLayout()
        cameraSelectionLayout.setAlignment(Qt.AlignmentFlag.AlignJustify)
        allCamerasSelectedButton = QPushButton("All cameras")
        allCamerasSelectedButton.setCheckable(True)
        allCamerasSelectedButton.setChecked(True)
        cameraSelectionLayout.addWidget(allCamerasSelectedButton)

        self.cameraSelectionButtonGroup = QButtonGroup()
        self.cameraSelectionButtonGroup.setExclusive(True)
        self.cameraSelectionButtonGroup.addButton(allCamerasSelectedButton)
        mainControlLayout.addLayout(cameraSelectionLayout)

        navLayout = QVBoxLayout(self.rightWidget)

        navFrameLayout = QHBoxLayout()
        mainControlLayout.addLayout(navLayout)
        navLayout.addLayout(navFrameLayout)

        self.prevButton = QPushButton("◄")
        self.prevButton.setEnabled(True)
        self.nextButton = QPushButton("►")
        self.nextButton.setEnabled(True)

        navFrameLayout.addWidget(self.prevButton)
        navFrameLayout.addWidget(self.nextButton)


        navVideoLayout = QHBoxLayout()
        navLayout.addLayout(navVideoLayout)
        
        

        for i in range(self.camerasAmount):
            cameraSelectionButton = QPushButton(f"Camera {i+1}")
            cameraSelectionButton.setCheckable(True)
            self.cameraSelectionButtonGroup.addButton(cameraSelectionButton , i)
            cameraSelectionLayout.addWidget(cameraSelectionButton)

        self.cameraSelectionButtonGroup.buttonClicked.connect(self._onCameraSelection)

    def _onCameraSelection(self , button:QPushButton):
        buttonId = self.cameraSelectionButtonGroup.id(button)
        self.cameraSelectedIndex = buttonId
        if  buttonId == -2:
            for frameWidget in self.frameWidgets:
                self.allFramesLayout.addWidget(frameWidget)
            self.stackedWidget.setCurrentIndex(0)
        else:
            frameWidget = self.frameWidgets[buttonId]
            self.clearLayout(self.singleFrameLayout)
            self.singleFrameLayout.addWidget(frameWidget)
            self.stackedWidget.setCurrentIndex(1)
    
    def clearLayout(self , layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left: 
            self._prevButton()
            event.accept()
        elif event.key() == Qt.Key.Key_Right:
            self._nextButton()
            event.accept()
        elif event.key() == Qt.Key.Key_Space:
            self._toggleVideo()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _prevButton(self,):
        pass

    def _nextButton(self,) :
        pass

    def _toggleVideo(self):
        pass


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()