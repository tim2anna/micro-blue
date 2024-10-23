#!/usr/bin/env python3

from time import time, sleep, localtime
from threading import Lock
from gpiozero.threads import GPIOThread
from RPi import GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


# 依次为：0-9, a-z, blank, dash, star
_SEGMENTS = bytearray(b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x77\x7C\x39\x5E\x79\x71\x3D\x76\x0F\x1E\x75\x38\x37\x54\x5C\x73\x67\x50\x49\x78\x3E\x1C\x7E\x64\x6E\x5A\x00\x40\x63')

"""
数码管的七段位置如下，8位数据从低位到高位依次为：A、B、C、D、E、F、G、DP。
例如：0的段码为00111111，转换16进制为0x3F。
      A
     ---
  F |   | B
     -G-
  E |   | C
     ---
      D

用法：
import time
from micro_blue.gpiozero_lib.tm1637 import TM1637
tm = TM1637(21, 20)
tm.show('1234')
time.sleep(1)
tm.show('5678')
time.sleep(1)
tm.show('90-*')
time.sleep(1)
tm.show('abcd')
time.sleep(1)
tm.show('efgh')
time.sleep(1)
tm.show('ijkl')
time.sleep(1)
tm.show('mnop')
time.sleep(1)
tm.show('qrst')
time.sleep(1)
tm.show('uvwx')
time.sleep(1)
tm.show('yz  ')
time.sleep(1)
tm.show('-999')
time.sleep(1)
tm.scroll('micro-blue-room')
time.sleep(1)
tm.temperature(24)
time.sleep(1)
tm.clock()
"""


class TM1637(object):
    I2C_COMM1 = 0x40  # 写显存数据命令: 0b01000000
    I2C_COMM2 = 0xC0  # 设置地址命令：0b11000000
    I2C_COMM3 = 0x88  # 控制显示命令：0b10001000

    def __init__(self, clk, dio, brightness=1.0):
        self.clk_pin = clk  # 时钟信号引脚
        self.dio_pin = dio  # 数据输入输出引脚
        self.brightness = brightness  # 明亮度
        # 引脚初始化
        GPIO.setup(self.clk_pin, GPIO.OUT)
        GPIO.setup(self.dio_pin, GPIO.OUT)
        # 线程
        self._display_thread = None
        self._display_lock = Lock()

    def br(self):
        """ 多条命令封装实现换行效果 """
        self.stop()
        self.start()

    def set_segments(self, segments, pos=0):
        self.start()
        self.write_byte(self.I2C_COMM1)  # 写入命令1：写显存数据
        self.br()
        # todo: pos的写法待验证
        self.write_byte(self.I2C_COMM2 | pos)  # 写入命令2：设置地址
        for seg in segments:
            self.write_byte(seg)
        self.br()
        # todo: 明暗度这里有问题
        self.write_byte(self.I2C_COMM3 + int(self.brightness))  # 写入命令3：显示控制，明暗度
        self.stop()

    def start(self):
        """ 开始条件：待确认 """
        GPIO.output(self.clk_pin, GPIO.HIGH)
        GPIO.output(self.dio_pin, GPIO.HIGH)
        GPIO.output(self.dio_pin, GPIO.LOW)
        GPIO.output(self.clk_pin, GPIO.LOW)

    def stop(self):
        """ 结束条件：clk为高电位，dio由低电位变为高电位 """
        GPIO.output(self.clk_pin, GPIO.LOW)
        GPIO.output(self.dio_pin, GPIO.LOW)
        GPIO.output(self.clk_pin, GPIO.HIGH)
        GPIO.output(self.dio_pin, GPIO.HIGH)

    def write_byte(self, b):
        # 写入二进制数据：8个bit
        for i in range(8):
            GPIO.output(self.clk_pin, GPIO.LOW)
            if b & 0x01:
                GPIO.output(self.dio_pin, GPIO.HIGH)
            else:
                GPIO.output(self.dio_pin, GPIO.LOW)
            b = b >> 1
            GPIO.output(self.clk_pin, GPIO.HIGH)

        # wait for ACK
        GPIO.output(self.clk_pin, GPIO.LOW)
        GPIO.output(self.dio_pin, GPIO.HIGH)
        GPIO.output(self.clk_pin, GPIO.HIGH)
        GPIO.setup(self.dio_pin, GPIO.IN)
        GPIO.setup(self.dio_pin, GPIO.OUT)

    @classmethod
    def encode_char(cls, char):
        """ 转换单个支付0-9, a-z, space, dash or star为段编码 """
        o = ord(char)
        if o == 32:
            return _SEGMENTS[36]  # space:空格
        if o == 42:
            return _SEGMENTS[38]  # star/degrees:星号
        if o == 45:
            return _SEGMENTS[37]  # dash:破折号
        if 65 <= o <= 90:
            return _SEGMENTS[o-55]  # uppercase A-Z: 大写字母A到Z
        if 97 <= o <= 122:
            return _SEGMENTS[o-87]  # lowercase a-z：小写字母a到z
        if 48 <= o <= 57:
            return _SEGMENTS[o-48]  # 0-9
        raise ValueError("Character out of range: {:d} '{:s}'".format(o, chr(o)))

    @classmethod
    def encode_string(cls, string):
        """Convert an up to 4 character length string containing 0-9, a-z,
        space, dash, star to an array of segments, matching the length of the
        source string."""
        segments = bytearray(len(string))
        for i in range(len(string)):
            segments[i] = cls.encode_char(string[i])
        return segments

    def number(self, num):
        """ 显示-999~9999的数字 """
        num = max(-999, min(num, 9999))
        string = '{0:>4d}'.format(num)
        self.set_segments(self.encode_string(string))

    def show(self, string, colon=False):
        """ 显示4位的字符串(0~9,a-z,A-Z,space,dash,star) """
        segments = self.encode_string(string)
        if colon:
            point_data = 0x80
        else:
            point_data = 0x00
        results = []
        for segment in segments:
            results.append(segment + point_data)
        self.set_segments(results)

    def scroll(self, string, delay=0.25):
        """ 滚动显示 """
        segments = string if isinstance(string, list) else self.encode_string(string)
        data = [0] * 8
        data[4:0] = list(segments)
        for i in range(len(segments) + 5):
            self.set_segments(data[0 + i:4 + i])
            sleep(delay)

    def clock(self):
        """ 显示时间 """
        while True:
            t = localtime()
            sleep(1 - time() % 1)
            d0 = str(t.tm_hour // 10)
            d1 = str(t.tm_hour % 10)
            d2 = str(t.tm_min // 10)
            d3 = str(t.tm_min % 10)

            self.show(f'{d0}{d1}{d2}{d3}', colon=True)
            if self._display_thread.stopping.wait(0.5):
                pass
            self.show(f'{d0}{d1}{d2}{d3}', colon=False)
            if self._display_thread.stopping.wait(0.5):
                pass

    def clear(self):
        if getattr(self, '_display_thread', None):
            self._display_thread.stop()
        self._display_thread = None

    def countdown(self, seconds, background=True):
        """ 倒计时 """
        self.clear()
        self._display_thread = GPIOThread(self._countdown, (seconds,))
        self._display_thread.start()
        if not background:
            self._display_thread.join()
            self._display_thread = None

    def _countdown(self, seconds):
        for i in range(seconds, 0, -1):
            self.number(i)
            if self._display_thread.stopping.wait(1):
                pass
        # 倒计时结束显示0，并清理线程
        self.number(0)
        self._display_thread = None

    def temperature(self, num):
        """ 显示温度，呈现效果为：37*C
        :param num: 温度范围-9~99；小于-9：显示lo；大于99：显示hi
        """
        if num < -9:
            self.show('lo')  # low
        elif num > 99:
            self.show('hi')  # high
        else:
            string = '{0: >2d}*C'.format(num)
            self.set_segments(self.encode_string(string))
