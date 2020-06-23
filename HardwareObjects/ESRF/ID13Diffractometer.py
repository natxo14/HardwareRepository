#
#  Project: MXCuBE
#  https://github.com/mxcube.
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

import logging
import gevent
import time

from HardwareRepository.HardwareObjects.GenericDiffractometer import (
    GenericDiffractometer
)
from HardwareRepository.HardwareObjects import sample_centring
from HardwareRepository.BaseHardwareObjects import HardwareObject
from HardwareRepository import HardwareRepository as HWR

__credits__ = ["MXCuBE collaboration"]
__version__ = "2.2."
__status__ = "Draft"

class ID13Diffractometer(GenericDiffractometer):

    # CENTRING_MOTORS_NAME = [
    #     "phi",
    #     "phiz",
    #     "phiy",
    #     "sampx",
    #     "sampy",
    #     "kappa",
    #     "kappa_phi",
    #     "beam_x",
    #     "beam_y",
    #     "zoom",
    # ]
    # This is used if self.centring_motors_list = eval(self.getProperty("centring_motors")) fails
    
    # def __init__(self, *args):
    #     GenericDiffractometer.__init__(self, *args)

    #     # Hardware objects ----------------------------------------------------
    #     self.zoom_motor_hwobj = None
    #     self.omega_reference_motor = None
    #     self.centring_hwobj = None
    #     self.minikappa_correction_hwobj = None 
    def init(self):
        #self.smargon = self.getObjectByRole("smargon")
        #self.connect(self.smargon, "stateChanged", self.smargon_state_changed)

        #self.lightarm_hwobj = self.getObjectByRole("lightarm")
        # self.centring_hwobj = self.getObjectByRole('centring')

        self.px1conf_ho = self.getObjectByRole("px1configuration")
        self.px1env_ho = self.getObjectByRole("px1environment")

        self.pixels_per_mm_x = 0
        self.pixels_per_mm_y = 0

        GenericDiffractometer.init(self)

        self.centring_methods = {
            GenericDiffractometer.CENTRING_METHOD_MANUAL: self.id13_manual_centring,
            GenericDiffractometer.CENTRING_METHOD_AUTO: self.start_automatic_centring,
            GenericDiffractometer.CENTRING_METHOD_MOVE_TO_BEAM: self.start_move_to_beam,
        }

    def get_pixels_per_mm(self):
        self.update_zoom_calibration()
        return GenericDiffractometer.get_pixels_per_mm(self)
    
    def update_zoom_calibration(self):
        """
        """
        if "zoom" not in self.motor_hwobj_dict:
            # not initialized yet
            return

        zoom_motor = self.motor_hwobj_dict["zoom"]

        props = zoom_motor.getCurrentPositionProperties()

        if "pixelsPerMmZ" in props.keys() and "pixelsPerMmY" in props.keys():
            self.pixels_per_mm_x = float(props["pixelsPerMmY"])
            self.pixels_per_mm_y = float(props["pixelsPerMmZ"])
        else:
            self.pixels_per_mm_x = 0
            self.pixels_per_mm_y = 0

        if "beamPositionX" in props.keys() and "beamPositionY" in props.keys():
            self.beam_xc = float(props["beamPositionX"])
            self.beam_yc = float(props["beamPositionY"])

        if 0 not in [self.pixels_per_mm_x, self.pixels_per_mm_y]:
            self.emit(
                "pixelsPerMmChanged", ((self.pixels_per_mm_x, self.pixels_per_mm_y),)
            )
    def get_centred_point_from_coord(self, coord_x, coord_y, return_by_names=True):
        pass
