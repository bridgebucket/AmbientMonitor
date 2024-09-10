import sys, configparser, os, cv2
import numpy as np
from PIL import ImageGrab
from PyQt5.QtCore import * 
from PyQt5.QtGui import * 
from PyQt5.QtWidgets import *
from colorama import init as colorama_init
from colorama import Fore, Style

## Creating or loading settings.ini
config = configparser.ConfigParser()
try:
    f = open("settings.ini", "x")
    try:
        f.write("[Settings]\ncontrast = 1.0\nbrightness = 0\nscale_factor = 0.14\nblur_amount = 119\n\n[SettingsBetter]\nreactivity = 0.1\nmsUpdate = 50\nreach = 1\ndarkenbg = 125")
        print(f"{Fore.BLUE}settings.ini{Style.RESET_ALL} was {Fore.RED}not{Style.RESET_ALL} found, so creating a new one.")
    except:
        print(f"{Fore.RED}ERROR!{Style.RESET_ALL} Something went wrong when writing to settings.ini")
    finally:
        f.close()
except FileExistsError:
    print(f"{Fore.BLUE}settings.ini{Style.RESET_ALL} exists, loading settings...")
finally:
    config.read('settings.ini')
    if 'SettingsBetter' in config and 'Settings' in config:
            reactivity = config.getfloat('SettingsBetter', 'reactivity')
            msUpdate = config.getint('SettingsBetter', 'msUpdate')
            reach = config.getint('SettingsBetter', 'reach')
            darkenbg = config.getint('SettingsBetter', 'darkenbg')

            contrast_level = config.getfloat('Settings', 'contrast')
            brightness_level = config.getfloat('Settings', 'brightness')
            image_scale_factor = config.getfloat('Settings', 'scale_factor')
            blur_amount = config.getint('Settings', 'blur_amount')

# while True:
#     oldornew = int(input(f"{Fore.CYAN}1{Style.RESET_ALL} Will use the new style ambient monitor\n{Fore.CYAN}2{Style.RESET_ALL} Will use the old style ambient monitor\n"))
#     if oldornew != 1 and oldornew != 2:
#         print(f"{Fore.RED}Must type either '1' or '2' to select an option.{Style.RESET_ALL}")
#     else:
#         break
# while True:
#     leftorright = int(input(f"{Fore.CYAN}1{Style.RESET_ALL} Will spawn on left-most monitor\n{Fore.CYAN}2{Style.RESET_ALL} Will spawn on right-most monitor\n"))
#     if leftorright != 1 and leftorright != 2:
#         print(f"{Fore.RED}Must type either '1' or '2' to select an option.{Style.RESET_ALL}")
#     else:
#         break


#### This piece of code up here will get added back once I implement a right sided version of
#### this script. In it's current state, I think it works great for the left monitor though.
#### I will also need to add the original version of this script (the one i forked from).

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('The ambience of the left')
        self.setWindowOpacity(1)
        self.setGeometry(-1920, -1080, 1920, 1080)              # In an ideal world, this works. I hope for forgiveness.

        self.setAttribute(Qt.WA_TranslucentBackground)          # This removes the frame from the window and enables transparency. To compensate 
        self.setWindowFlag(Qt.FramelessWindowHint)              # for loss of close button, I set a hotkey later for closing the window.
        
        self.timer = QTimer(self)                               #
        self.timer.timeout.connect(self.update_gradient)        # Updates the ambient color every msUpdate milliseconds
        self.timer.start(msUpdate)                              #

        self.color = (0, 0, 0)                                  #
        self.last_color = None                                  #
        self.target_color = (0, 0, 0)                           # This variable allows for smooth transition between two colors when it changes
        self.gradient_pixmap = QPixmap(self.size())             #
        self.gradient_pixmap.fill(QColor(0, 0, 0, 0))           # Sets the window to a transparent color initially
        self.label = QLabel(self)                               #
        self.label.setPixmap(self.gradient_pixmap)              #
        self.label.resize(self.size())                          #
        self.label.show()                                       #

    def capture_color(self):
        bbox = (0, 0, 1, 550)                                     # x1, y1, x2, y2
        img = ImageGrab.grab(bbox)                              # In an ideal world, this grabs the entire strip of pixels off the side of
        self.target_color = img.getpixel((0, 549))                # the screen. We do not live in an ideal world.

    def interpolate_color(self, current_color, target_color, factor):
        return (
            int(current_color[0] + (target_color[0] - current_color[0]) * factor),
            int(current_color[1] + (target_color[1] - current_color[1]) * factor),
            int(current_color[2] + (target_color[2] - current_color[2]) * factor)
        )
    
    def update_color(self):
        factor = reactivity
        self.color = self.interpolate_color(self.color, self.target_color, factor)

    def generate_gradient(self):
        width = self.width()
        height = self.height()
        gradient = np.zeros((height, width, 4), dtype=np.uint8)

        for x in range(width):
            factor = (x / width) ** reach
            gradient[:, x] = [
                int(self.color[0] * factor),                    # red
                int(self.color[1] * factor),                    # green
                int(self.color[2] * factor),                    # blue
                darkenbg                                        # alpha
            ]

        return gradient

    def add_noise(self, gradient, noise_level=4):
        noise = np.random.randint(-noise_level, noise_level, gradient.shape, dtype=np.int8)
        noisy_gradient = np.clip(gradient.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return noisy_gradient

    def update_gradient(self):
        self.capture_color()
        self.update_color()

        if self.color != self.last_color:               # Set to update only if the color has changed
            gradient = self.generate_gradient()
            noisy_gradient = self.add_noise(gradient)
            image = QImage(noisy_gradient.data, noisy_gradient.shape[1], noisy_gradient.shape[0], noisy_gradient.strides[0], QImage.Format_RGBA8888)
            self.gradient_pixmap = QPixmap.fromImage(image)
            self.label.setPixmap(self.gradient_pixmap)
            self.last_color = self.color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.gradient_pixmap)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec_())
