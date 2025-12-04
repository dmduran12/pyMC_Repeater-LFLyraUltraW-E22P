import threading
import time
import logging
from periphery import GPIO

logger = logging.getLogger("GPIOWrapper")

class PeripheryDevice:
    def __init__(self, pin, direction, initial=None):
        self.pin = pin
        self._closed = False
        try:
            self._gpio = GPIO(pin, direction)
            if direction == "out" and initial is not None:
                self._gpio.write(initial)
        except Exception as e:
            logger.error(f"Failed to open GPIO {pin}: {e}")
            self._gpio = None

    def close(self):
        if not self._closed and self._gpio:
            try:
                self._gpio.close()
            except Exception:
                pass
            self._closed = True
            self._gpio = None

    @property
    def value(self):
        if self._gpio:
            return self._gpio.read()
        return False

class DigitalOutputDevice(PeripheryDevice):
    def __init__(self, pin, active_high=True, initial_value=False, **kwargs):
        super().__init__(pin, "out", initial=initial_value)
        self.active_high = active_high
        
    def on(self):
        if self._gpio:
            self._gpio.write(True if self.active_high else False)
        
    def off(self):
        if self._gpio:
            self._gpio.write(False if self.active_high else True)

class DigitalInputDevice(PeripheryDevice):
    def __init__(self, pin, pull_up=False, **kwargs):
        super().__init__(pin, "in")
        # Note: periphery doesn't easily support setting internal pulls via cdev/sysfs 
        # on all platforms. We assume external pulls or device tree config.
        
class Button(DigitalInputDevice):
    def __init__(self, pin, pull_up=True, bounce_time=None, **kwargs):
        super().__init__(pin, pull_up=pull_up)
        self.pull_up = pull_up
        self.when_activated = None
        self.when_deactivated = None
        self._stop_event = threading.Event()
        self._thread = None
        
        # Configure edge
        if self._gpio:
            try:
                # pull_up=True -> Active Low -> Falling edge
                # pull_up=False -> Active High -> Rising edge
                self.edge = "falling" if pull_up else "rising"
                self._gpio.edge = self.edge
                logger.debug(f"Configured GPIO {pin} edge to {self.edge}")
            except Exception as e:
                logger.warning(f"Failed to set edge on GPIO {pin}: {e}")
        
        self._start_poll_thread()
        
    def _start_poll_thread(self):
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name=f"GPIO-{self.pin}-Poll")
        self._thread.start()
        
    def _poll_loop(self):
        while not self._stop_event.is_set():
            if not self._gpio:
                time.sleep(1)
                continue
                
            try:
                # Poll with timeout
                if self._gpio.poll(0.1):
                    # Event detected
                    # Check current value to confirm/debounce
                    val = self._gpio.read()
                    
                    # Active High (pull_up=False): Activated when True
                    # Active Low (pull_up=True): Activated when False
                    is_active = val if not self.pull_up else not val
                    
                    if is_active and self.when_activated:
                        # logger.debug(f"GPIO {self.pin} activated")
                        self.when_activated()
                    elif not is_active and self.when_deactivated:
                        self.when_deactivated()
                        
            except Exception as e:
                logger.error(f"GPIO {self.pin} poll error: {e}")
                time.sleep(1)
                
    def close(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        super().close()
