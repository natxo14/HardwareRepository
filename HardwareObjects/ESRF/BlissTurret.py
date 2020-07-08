from HardwareRepository.BaseHardwareObjects import HardwareObject
from HardwareRepository.BaseHardwareObjects import HardwareObjectState

from bliss.config import static

import time
import gevent
from gevent import Timeout

class BlissTurret(HardwareObject):
    
    def __init__(self, name):
        HardwareObject.__init__(self, name)

    def init(self):
        self.username = self.turret_name

        print(f"##########BLISSTURRET init self.positions : {self.username}")

        cfg = static.get_config()
        self.turret = cfg.get(self.turret_name)
        self.connect(self.turret, "position", self.position_changed)
        self.connect(self.turret, "mode", self.mode_changed)
      
    def connectNotify(self, signal):
        if signal == "positionChanged":
            self.emit("positionChanged", (self.get_value(),))
        elif signal == "modeChanged":
            self.emit("modeChanged", (self.get_mode(),))
    
    def position_changed(self, new_position):
        # print self.name(), absolutePosition
        self.emit("positionChanged", (new_position,))

    def mode_changed(self, new_mode):
        self.emit("modeChanged", (new_mode,))

    def set_mode(self, mode):
        self.turret.mode = mode
    
    def get_mode(self):
        return self.turret.mode

    def get_value(self):
        return self.turret.position
    
    def set_value(self, position):
        self.turret.position = position
    
    def get_turret_mnemonic(self):
        return self.turret_name

    def update_values(self):
        self.emit("positionChanged", (self.get_value(),))
        self.emit("modeChanged", (self.get_mode(),))
    
    def get_state(self):
        return HardwareObjectState.READY

    def wait_end_of_move(self, timeout=None):
        """
        Descript. : waits till the motor stops
        """
        with gevent.Timeout(timeout, False):
            time.sleep(0.1)
            while self.get_state() == HardwareObjectState.BUSY:
                time.sleep(0.1)

