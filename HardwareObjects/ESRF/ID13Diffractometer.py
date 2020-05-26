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
    
    def __init__(self, *args):
        GenericDiffractometer.__init__(self, *args)

        # Hardware objects ----------------------------------------------------
        self.zoom_motor_hwobj = None
        self.omega_reference_motor = None
        self.centring_hwobj = None
        self.minikappa_correction_hwobj = None 