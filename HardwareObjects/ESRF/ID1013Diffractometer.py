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
from HardwareRepository.BaseHardwareObjects import HardwareObjectState
from HardwareRepository import HardwareRepository as HWR

__credits__ = ["MXCuBE collaboration"]
__version__ = "2.2."
__status__ = "Draft"

class ID1013Diffractometer(GenericDiffractometer):
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
        self.delta_phi = 0.3
        self.calibration_h_mot_delta = 0.2
        self.calibration_v_mot_delta = 0.2
        self.current_calibration_procedure = None
        
        GenericDiffractometer.init(self)


        self.centring_methods = {
            GenericDiffractometer.CENTRING_METHOD_MANUAL: self.id10_manual_centring,
            GenericDiffractometer.CENTRING_METHOD_AUTO: self.start_automatic_centring,
            GenericDiffractometer.CENTRING_METHOD_MOVE_TO_BEAM: self.start_move_to_beam,
        }

        self.update_zoom_calibration()

    def get_pixels_per_mm(self):
        self.update_zoom_calibration()
        return GenericDiffractometer.get_pixels_per_mm(self)
    
    def update_beam_position(self):
        print(f"##################ID10Diffractometer update_beam_position")
        if "zoom" not in self.motor_hwobj_dict:
            # not initialized yet
            return
        zoom_motor = self.motor_hwobj_dict["zoom"]
        props = zoom_motor.get_current_position()
        if props is None:
            # unknow zoom motor position (intermediate or...)
            print(f"##################ID10Diffractometer update_zoom_calibration zoom motor unkwon position")
            return
                
        if "beamx" in props.keys() and "beamy" in props.keys():
            self.beam_position = (int(props["beamx"]), int(props["beamy"]))
        else:
            self.beam_position = (0,0)

        if HWR.beamline.beam is not None:
            print(f"##################ID10Diffractometer update_beam_position HWR.beamline.beam not none - {self.beam_position}")
            HWR.beamline.beam.set_beam_position_on_screen(self.beam_position)
        
        print(f"##################ID10Diffractometer update_beam_position - {self.beam_position} - {props['name']}")
        
    def update_zoom_calibration(self):
        """
        """
        print(f"##################ID10Diffractometer update_zoom_calibration")
        if "zoom" not in self.motor_hwobj_dict:
            # not initialized yet
            return

        zoom_motor = self.motor_hwobj_dict["zoom"]

        print(f"##################ID10Diffractometer zoom_motor {id(zoom_motor)}")
        props = zoom_motor.get_current_position()

        if props is None:
            # unknow zoom motor position (intermediate or...)
            print(f"##################ID10Diffractometer update_zoom_calibration zoom motor unkwon position")
            return
        print(f"##################ID10Diffractometer zoom_motor props {props} - keys {props.keys()}")
        
        if "resox" in props.keys() and "resoy" in props.keys():
            self.pixels_per_mm_x = abs(1.0/float(props["resox"]))/1000.0
            self.pixels_per_mm_y = abs(1.0/float(props["resoy"]))/1000.0
        else:
            self.pixels_per_mm_x = 0
            self.pixels_per_mm_y = 0

        if "beamx" in props.keys() and "beamy" in props.keys():
            self.beam_position = [float(props["beamx"]), float(props["beamy"])]
        else:
            self.beam_position = [0, 0]
        
        if 0 not in [self.pixels_per_mm_x, self.pixels_per_mm_y]:
            print(f"##################ID10Diffractometer emit( \
                pixelsPerMmChanged {self.pixels_per_mm_x} - {self.pixels_per_mm_y} \
                {self.beam_position}")
        
            self.emit(
                "pixelsPerMmChanged", ((self.pixels_per_mm_x, self.pixels_per_mm_y),)
            )
    
    def move_beam_to_clicked_point(
        self, coord_x=None, coord_y=None
    ):
        """
        Descript. :
        Move center of the image to the clicked point
        """
        
        try:
            print(f"##################ID10Diffractometer move_beam_to_clicked_point {coord_x} {coord_y}")
            
            self.emit_progress_message(f"Move to clicked point {coord_x},{coord_y}...")
            self.centring_time = time.time()
            #curr_time = time.strftime("%Y-%m-%d %H:%M:%S")
            
            if coord_x is None and coord_y is None:
                coord_x = self.beam_position[0]
                coord_y = self.beam_position[1]

            motors = self.get_centred_point_from_coord(
                coord_x, coord_y
            )
            print(f"##################ID10Diffractometer move_beam_to_clicked_point - motors - {motors}")
            
            self.move_to_motors_positions(motors)
        except BaseException:
            logging.exception("Diffractometer: Could not complete 2D centring")

    def image_clicked(self, x, y, use_mode=None):
        """
        Descript. :
        """
        print(f"################ GENERIC DIFF image_clicked {x} , {y}")
        if self.use_sample_centring:
            sample_centring.user_click(x, y)
            if use_mode == "centring":
                self.emit("centring_image_clicked", (x, y))
        else:
            self.user_clicked_event.set((x, y))
    
    def id10_manual_centring(self, sample_info=None, wait_result=None):
        """
        """
        centring_points = self.centring_point_number
        phi_range_val = self.delta_phi * (centring_points - 1)

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
            phi_range=phi_range_val,
        )

        self.current_centring_procedure.link(self.centring_done)

    # def centring_done(self, centring_procedure):
    #     """
    #     Descript. :
    #     """
    #     logging.getLogger("HWR").debug("Diffractometer: centring procedure done.")
    #     try:
    #         motor_pos = centring_procedure.get()
    #         if isinstance(motor_pos, gevent.GreenletExit):
    #             raise motor_pos
    #     except BaseException:
    #         logging.exception("Could not complete centring")
    #         self.emit_centring_failed()
    #     else:
    #         logging.getLogger("HWR").debug(
    #             "Diffractometer: centring procedure done. %s" % motor_pos
    #         )

    #         for motor in motor_pos:
    #             position = motor_pos[motor]
    #             logging.getLogger("HWR").debug(
    #                 "   - motor is %s - going to %s" % (motor.name(), position)
    #             )

    #         self.emit_progress_message("Moving sample to centred position...")
    #         self.emit_centring_moving()
    #         try:
    #             self.move_to_motors_positions(motor_pos, wait=True)
    #         except BaseException:
    #             logging.exception("Could not move to centred position")
    #             self.emit_centring_failed()
    #         else:
    #             # done already by px1_center
    #             pass
    #             # if 3 click centring move -180
    #             # if not self.in_plate_mode():
    #             # self.wait_device_ready()
    #             # self.motor_hwobj_dict['phi'].set_value_relative(-180, timeout=None)

    #         if (
    #             self.current_centring_method
    #             == GenericDiffractometer.CENTRING_METHOD_AUTO
    #         ):
    #             self.emit("newAutomaticCentringPoint", motor_pos)
    #         self.centring_time = time.time()
    #         self.emit_centring_successful()
    #         self.emit_progress_message("")
    #         self.ready_event.set()

    def set_calibration_parameters(self, h_motor_delta, v_motor_delta):
        """
        Descript. :
        """
        self.calibration_h_mot_delta = h_motor_delta
        self.calibration_v_mot_delta = v_motor_delta

    def set_centring_parameters(self, centring_point_number, delta_phi):
        """
        Descript. :
        """
        self.centring_point_number = int(centring_point_number)
        self.delta_phi = float(delta_phi)

    def get_centred_point_from_coord(self, coord_x, coord_y, return_by_names=False,):
        """
        Returns a dictionary with motors name ans positions centred.
        It is expected in start_move_to_beam and move_to_beam methods in
        GenericDIffractometer HwObj.

        @return: dict
        """
        beam_pos_x, beam_pos_y = HWR.beamline.beam.get_beam_position_on_screen()
        print(f"################ ID1013 DIFF get_centred_point_from_coord point {coord_x} , {coord_y} - beam_pos {beam_pos_x}, {beam_pos_y}")
        
        self.update_zoom_calibration()

        if None in (self.pixels_per_mm_x, self.pixels_per_mm_y):
            return 0, 0
        
        rmove_x = self.motor_hwobj_dict["phiy"].get_value() + (coord_x - beam_pos_x) / self.pixels_per_mm_x
        rmove_y = self.motor_hwobj_dict["phiz"].get_value() + (coord_y - beam_pos_y) / self.pixels_per_mm_y

        motors_rel_move = {
            "phi": self.centring_phi.get_value(),
            "phiz": float(rmove_y),
            "phiy": float(rmove_x),
            "sampx": self.centring_sampx.get_value(),
            "sampy": self.centring_sampy.get_value(),
        }
        
        print(f"################ ID1013 DIFF get_centred_point_from_coord out motors_rel_move {motors_rel_move}")
        
        return motors_rel_move

    def is_ready(self):
        """
        Detects if device is ready
        """
        #print(f" ################ ID1013 DIFF is_ready:")
        for motor in self.motor_hwobj_dict.values():
            print(f"""################ ID1013 DIFF is_ready: Motor : {motor.name()} state {motor.get_state()}
            - is READY: {motor.get_state() == HardwareObjectState.READY}""")
        all_ready = all(motor.get_state() == HardwareObjectState.READY for motor in self.motor_hwobj_dict.values())
        
        print(f" ################ ID1013 DIFF is_ready: ALL IS READY {all_ready}")
        return all_ready
        
        # return self.current_state == DiffractometerState.tostring(
        #     DiffractometerState.Ready
        # )
    def zoom_motor_predefined_position_changed(self, position_name, offset=None):
        """
        """
        print(f"################ ID1013 DIFF zoom_motor_predefined_position_changed position_name :{position_name}")
        if not position_name:
            return
        
        self.update_zoom_calibration()
        self.update_beam_position()
        self.emit("zoomMotorPredefinedPositionChanged", (position_name, offset))

    def start_manual_calibration(self):
        """
        """
        self.emit_progress_message("Start manual calibration...")
        print(f"ID10DIFFRACTOMETER--start_manual_calibration {self.calibration_h_mot_delta} - {self.calibration_v_mot_delta} ")

        self.current_calibration_procedure = sample_centring.start_calibrate(
                {
                    "horizontal": self.centring_phiy,
                    "vertical": self.centring_phiz,

                },
                self.calibration_h_mot_delta,
                self.calibration_v_mot_delta
            )

        self.current_calibration_procedure.link(self.calibration_done)
    
    def cancel_manual_calibration(self):
        """
        kills the greenlet
        """
        self.current_calibration_procedure.kill()

    def calibration_done(self, calibration_procedure):
        try:
            calibration_points = calibration_procedure.get()
            if isinstance(calibration_points, gevent.GreenletExit):
                print(f"##################ID10Diffractometer - calibration_done - calibration_points is gevent.GreenletExit")
                HWR.beamline.sample_view.stop_calibration()
                raise calibration_points
        
        except BaseException:
            logging.exception("Could not complete calibration")
            raise
        
        print(f"##################ID10Diffractometer - calibration_done - {calibration_points}")
        self.emit("new_calibration_done", (calibration_points,))
