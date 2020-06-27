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

class ID10Diffractometer(GenericDiffractometer):
    """
    Descript. :
    """
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

         # Internal values -----------------------------------------------------
        self.pixels_per_mm_x = 0
        self.pixels_per_mm_y = 0
        self.centring_point_number = 3
        self.delta_phi = 0.1

        GenericDiffractometer.init(self)

        self.centring_methods = {
            GenericDiffractometer.CENTRING_METHOD_MANUAL: self.id10_manual_centring,
            GenericDiffractometer.CENTRING_METHOD_AUTO: self.start_automatic_centring,
            GenericDiffractometer.CENTRING_METHOD_MOVE_TO_BEAM: self.start_move_to_beam,
        }

    def get_pixels_per_mm(self):
        self.update_zoom_calibration()
        return GenericDiffractometer.get_pixels_per_mm(self)
    
    def update_zoom_calibration(self):
        """
        """
        print(f"ID10Diffractometer update_zoom_calibration")
        if "zoom" not in self.motor_hwobj_dict:
            # not initialized yet
            return

        zoom_motor = self.motor_hwobj_dict["zoom"]

        props = zoom_motor.get_current_position()

        if "resox" in props.keys() and "resoy" in props.keys():
            self.pixels_per_mm_x = float(props["resox"])
            self.pixels_per_mm_y = float(props["resoy"])
        else:
            self.pixels_per_mm_x = 0
            self.pixels_per_mm_y = 0

        if "beamx" in props.keys() and "beamy" in props.keys():
            self.beam_xc = float(props["beamx"])
            self.beam_yc = float(props["beamy"])

        if 0 not in [self.pixels_per_mm_x, self.pixels_per_mm_y]:
            self.emit(
                "pixelsPerMmChanged", ((self.pixels_per_mm_x, self.pixels_per_mm_y),)
            )

    def id10_manual_centring(self, sample_info=None, wait_result=None):
        """
        """
        centring_points = self.centring_point_number
        centring_phi_incr = self.delta_phi

        self.emit_progress_message("Manual N click centring...")
        logging.getLogger("HWR").debug(
            f"   starting manual {centring_points} click centring.\
             phiy is {str(self.centring_phiy)}"
        )
                
        self.current_centring_procedure = sample_centring.start(
            {
                "phi": self.centring_phi,
                "phiy": self.centring_phiy,
                "sampx": self.centring_sampx,
                "sampy": self.centring_sampy,
                "phiz": self.centring_phiz,
            },
            self.pixels_per_mm_x,
            self.pixels_per_mm_y,
            self.beam_position[0],
            self.beam_position[1],
            n_points=centring_points,
            phi_incr=centring_phi_incr,
        )

        self.current_centring_procedure.link(self.centring_done)

    def centring_done(self, centring_procedure):
        """
        Descript. :
        """
        logging.getLogger("HWR").debug("Diffractometer: centring procedure done.")
        try:
            motor_pos = centring_procedure.get()
            if isinstance(motor_pos, gevent.GreenletExit):
                raise motor_pos
        except BaseException:
            logging.exception("Could not complete centring")
            self.emit_centring_failed()
        else:
            logging.getLogger("HWR").debug(
                "Diffractometer: centring procedure done. %s" % motor_pos
            )

            for motor in motor_pos:
                position = motor_pos[motor]
                logging.getLogger("HWR").debug(
                    "   - motor is %s - going to %s" % (motor.name(), position)
                )

            self.emit_progress_message("Moving sample to centred position...")
            self.emit_centring_moving()
            try:
                self.move_to_motors_positions(motor_pos, wait=True)
            except BaseException:
                logging.exception("Could not move to centred position")
                self.emit_centring_failed()
            else:
                # done already by px1_center
                pass
                # if 3 click centring move -180
                # if not self.in_plate_mode():
                # self.wait_device_ready()
                # self.motor_hwobj_dict['phi'].set_value_relative(-180, timeout=None)

            if (
                self.current_centring_method
                == GenericDiffractometer.CENTRING_METHOD_AUTO
            ):
                self.emit("newAutomaticCentringPoint", motor_pos)
            self.centring_time = time.time()
            self.emit_centring_successful()
            self.emit_progress_message("")
            self.ready_event.set()

        self.current_centring_procedure.link(self.centring_done)

    def set_centring_parameter(self, centring_point_number, delta_phi):
        self.centring_point_number = centring_point_number
        self.delta_phi = delta_phi

    def get_centred_point_from_coord(self, coord_x, coord_y, return_by_names=True):
        pass
