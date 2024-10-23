from gpiozero import TrafficLights
from gpiozero.threads import GPIOThread


class TrafficLight(TrafficLights):
    def __init__(self, red=None, amber=None, green=None, *,
                 pwm=False, initial_value=False, yellow=None,
                 pin_factory=None):
        super().__init__(red, amber, green, pwm=pwm, initial_value=initial_value, yellow=yellow, pin_factory=pin_factory)
        self._blink_thread = None
        self.when_light_change = None  # 回调函数,什么颜色的灯亮几秒，when_light_change(color, seconds)

    def start(self, red_seconds=10, amber_seconds=3, green_seconds=10, background=True):
        self._blink_thread = GPIOThread(self._run, (red_seconds, amber_seconds, green_seconds))
        self._blink_thread.start()
        if not background:
            self._blink_thread.join()
            self._blink_thread = None

    def stop(self):
        if getattr(self, '_blink_thread', None):
            self._blink_thread.stop()
        self._blink_thread = None

    def _run(self, red_seconds, amber_seconds, green_seconds):
        if green_seconds <= 4:
            raise ValueError('green_seconds must be greater than 4')
        while True:
            # 红灯逻辑
            self.red.on()
            if self.when_light_change is not None:
                self.when_light_change('red', red_seconds)
            if self._blink_thread.stopping.wait(red_seconds):
                pass
            self.red.off()

            # 绿灯逻辑
            self.green.on()
            if self.when_light_change is not None:
                self.when_light_change('green', green_seconds)
            if self._blink_thread.stopping.wait(green_seconds-3):
                pass
            for _ in range(3):
                if self._blink_thread.stopping.wait(0.5):
                    pass
                self.green.on()
                if self._blink_thread.stopping.wait(0.5):
                    pass
                self.green.off()

            # 黄灯逻辑
            self.amber.on()
            if self.when_light_change is not None:
                self.when_light_change('amber', amber_seconds)
            if self._blink_thread.stopping.wait(amber_seconds):
                pass
            self.amber.off()
