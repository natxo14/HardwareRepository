from HardwareRepository.BaseHardwareObjects import HardwareObject
from bliss.config import static

class BlissVolpi(HardwareObject):
    
    def __init__(self, name):
        #AbstractMotor.__init__(self, name)
        HardwareObject.__init__(self, name)
        
    def init(self):
        self.username = self.volpi_name
        self.default_value = self.default_value
        if self.default_value is None:
            self.default_value = 15

        cfg = static.get_config()
        self.volpi = cfg.get(self.volpi_name)
        self.connect(self.volpi, "intensity", self.intensity_changed)
    
        self.set_value(self.default_value)
    # def connectNotify(self, signal):
    #     if signal == "intensityChanged":
    #         self.emit("intensityChanged", (self.get_value(),))

    def set_value(self, intensity):
        """set volpi to new value."""
        print(f" BLISS VOLPI set_value : {intensity}")
        self.volpi.intensity = intensity

    def get_value(self):
        """get volpi intensity value."""
        return self.volpi.intensity
    
    # def update_values(self):
    #     self.emit("intensityChanged", (self.get_value(),))

    def intensity_changed(self, new_intensity):
        if new_intensity != self.volpi.intensity:
            self.emit("intensityChanged", (new_intensity,))
