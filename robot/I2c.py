#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import math
import random
import time
import datetime
import threading
from luma.core import cmdline, error
from luma.core.render import canvas
from luma.core.virtual import viewport, snapshot, range_overlap
from luma.core.sprite_system import framerate_regulator
from PIL import ImageFont
from robot import config, utils, constants

Driver = 'sh1106'

def display_settings(args):
    """
    Display a short summary of the settings.

    :rtype: str
    """
    iface = ''
    display_types = cmdline.get_display_types()
    if args.display not in display_types['emulator']:
        iface = 'Interface: {}\n'.format(args.interface)

    lib_name = cmdline.get_library_for_display_type(args.display)
    if lib_name is not None:
        lib_version = cmdline.get_library_version(lib_name)
    else:
        lib_name = lib_version = 'unknown'

    import luma.core
    version = 'luma.{} {} (luma.core {})'.format(
        lib_name, lib_version, luma.core.__version__)

    return 'Version: {}\nDisplay: {}\n{}Dimensions: {} x {}\n{}'.format(
        version, args.display, iface, args.width, args.height, '-' * 60)

def get_device():
    """
    Create device from command-line arguments and return it.
    """
    parser = cmdline.create_parser(description='luma.examples arguments')
    args = parser.parse_args("")
    args.display = Driver

    print(display_settings(args))
    # create device
    try:
        device = cmdline.create_device(args)
    except error.Error as e:
        parser.error(e)

    return device

def make_font(name, size):
    font_path = constants.getFont(name)
    return ImageFont.truetype(font_path, size)

class I2c(threading.Thread):
    threadLock = threading.Lock()
    def __init__(self):
        threading.Thread.__init__(self)
        self.device = get_device()
        self.lastText = None
        self.lastTextX = 0
        self.lastTextShowFrame = 0
        self.endTextAfterFrame = False
        self.running = True

    def recordSay(self, text):
        I2c.threadLock.acquire()
        self.lastText = text
        I2c.threadLock.release()
        self.lastTextShowFrame = math.floor(14 / 5 * len(text) + 10) # 持续显示时间
        self.endTextAfterFrame = False
        self.lastTextX = 0

    def run(self):
        sz = 22
        fontEye = make_font("wenquanyi.ttf", sz)
        fontTxt = make_font("wenquanyi.ttf", 14)
        sq = self.device.width * 2
        virtualEye = viewport(self.device, sq, sq)
        virtualEye.set_position((0, 0))
        regulator = framerate_regulator(fps=30)

        isEmotion = False
        emoType = 0
        emoTime = 0
        frame = 0
        while True:
            I2c.threadLock.acquire()
            if not self.running:
                I2c.threadLock.release()
                break
            I2c.threadLock.release()
            with regulator:
                frame = frame + 1
                now = datetime.datetime.now()
                today_date = now.strftime("%Y年%m月%d日")
                today_time = now.strftime("%H:%M:%S")

                if random.random() * 100 < 5:
                    isEmotion = True
                    emoType = math.floor(random.random() * 6)
                    emoTime = random.random() * 4 + 2
                    frame = 0

                with canvas(virtualEye) as eye:
                    try:
                        I2c.threadLock.acquire()
                        if self.lastText != None:
                            # 显示上次说的内容
                            eye.text((self.lastTextX, 0), self.lastText, font=fontEye, align="center", fill="white")
                            self.lastTextX -= 5
                            if self.lastTextX < -len(self.lastText) * (20 + 2):
                                self.endTextAfterFrame = True # 显示过一轮，开始等待结束
                                self.lastTextX = self.device.width
                            if self.endTextAfterFrame:
                                self.lastTextShowFrame -= 1
                            if self.lastTextShowFrame <= 0:
                                self.lastText = None
                        else:
                            text = "0.0"
                            if isEmotion:
                                text = [">.<", "•̀ㅂ•́", "≧▽≦", "´ㅂ`", "￣▽￣", "^∇^"][emoType]
                                if frame > emoTime:
                                    isEmotion = False
                                    frame = 0
                            elif frame % (30) < (28):
                                pass
                            else:
                                text = "-.-"
                            x = math.floor((self.device.width - eye.textsize(text, fontEye)[0]) / 2)
                            eye.text((x, 0), text, font=fontEye, align="center", fill="white")
                        
                        I2c.threadLock.release()
                        
                        eye.text((0, 28 + 4), today_date, font=fontTxt, align="center", fill="white")
                        eye.text((0, 28 + 4 + 14 + 4), today_time, font=fontTxt, align="center", fill="white")
                    
                    except Exception as e:
                        logger.error("I2C显示出错！ {}".format(e))
                        
    def terminate(self):
        I2c.threadLock.acquire()
        self.running = False
        I2c.threadLock.release()