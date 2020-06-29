# encoding: utf-8
#
#  Project: MXCuBE
#  https://github.com/mxcube
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

"""
BeamDefiner ESRF implementation class - methods to define the size and shape of
the beam.
"""

__copyright__ = """ Copyright © 2019 by the MXCuBE collaboration """
__license__ = "LGPLv3+"


from HardwareRepository.HardwareObjects.abstract.AbstractBeam import (
    AbstractBeam,
    BeamShape,
)
from HardwareRepository import HardwareRepository as HWR


class ESRFBeam(AbstractBeam):
    """ Beam ESRF implementation """

    def __init__(self, name):
        AbstractBeam.__init__(self, name)
        self._aperture = None
        self._slits = {}
        self._complex = None
        self._definer_type = None
        print(f"#####################3 ESRFBeam __init__()")
        
    def init(self):
        print(f"#####################3 ESRFBeam init()")
        """ Initialize hardware """
        AbstractBeam.init(self)
        self._aperture = self.getObjectByRole("aperture")
        _bliss_obj = self.getObjectByRole("bliss")
        _slits = self.getProperty("slits")
        if _slits:
            for name in _slits.split():
                _key, _val = name.split(":")
                self._slits.update({_key: _bliss_obj.__getattribute__(_val)})
        self._complex = self.getObjectByRole("complex")
        self._definer_type = self.getProperty("definer")
        beam_position = self.getProperty("beam_position")
        if beam_position:
            self._beam_position_on_screen = tuple(map(float, beam_position.split()))

        if self._aperture:
            self._aperture.connect("valueChanged", self._emit_beam_info_change)
            self._aperture.connect("stateChanged", self._emit_beam_info_change)
        
        beam_size = self.getProperty("beam_size")
        if beam_size:
            self._beam_width = float(beam_position.split()[0])
            self._beam_height = float(beam_position.split()[1])


    def _emit_beam_info_change(self, *args, **kwargs):
        self.emit_beam_info_change()

    def _get_aperture_size(self):
        """ Get the size and the label of the aperture in place.
        Returns:
            (float, str): Size [mm], label.
        """
        _size = self._aperture.get_value().value[1]
        try:
            _label = self._aperture.get_value().value[1]
        except AttributeError:
            _label = str(_size)

        return _size / 1000.0, _label

    def _get_complex_size(self):
        """ Get the size and the name of the definer in place.
        Returns:
            (float, str): Size [mm], label.
        """
        _size = self._complex.get_value()
        _name = self._complex.get_current_position_name()
        return _size, _name

    def _get_slits_size(self):
        """ Get the size of the slits in place.
        Returns:
            (dict): {"width": float, "heigth": float}.
        """
        beam_size = {}
        for _key, _val in self._slits:
            beam_size.update({_key: abs(_val.position)})
        return beam_size

    def get_value(self):
        """ Get the size (width and heigth) of the beam and its shape.
            The size is in mm.
        Retunrs:
            (tuple): Dictionary (width, heigth, shape, name), with types
                               (float, float, Enum, str)
        """        
        _shape = BeamShape.UNKNOWN
        _beamsize_dict = {}
        if self._aperture:
            _size, _name = self._get_aperture_size()
            _beamsize_dict.update({_name: [_size]})
            _shape = BeamShape.ELIPTICAL

        if self._complex:
            _size, _name = self._get_complex_size()
            _beamsize_dict.update({_name: [_size]})
            _shape = BeamShape.ELIPTICAL

        if self._slits:
            _beamsize_dict.update({"slits": self._get_slits_size().values()})

        # find which device has the minimum size
        try:
            _val = min(_beamsize_dict.values())
            _key = [k for k, v in _beamsize_dict.items() if v == _val]

            _name = _key[0]
            self.beam_width = _val[0]

            if "slits" in _key:
                self.beam_height = _val[1]
                _shape = BeamShape.RECTANGULAR
            else:
                self.beam_height = _val[0]
        except ValueError:
            print("No beam defining device")
            return None, None, _shape, "none"

        return self.beam_width, self.beam_height, _shape, _name

    def get_available_size(self):
        """ Get the available predefined beam definer configuration.
        Returns:
            (dict): apertures {name: dimension} or
                    slits {"width": motor object, "heigth", motor object} or
                    complex definer {name: dimension}.
        """
        _type = "enum"
        if self._definer_type in (self._aperture, "aperture"):
            # get list of the available apertures
            aperture_list = self._aperture.predefined_positions
            return {"type": [_type], "values": aperture_list}

        if self._definer_type in (self._complex, "complex"):
            return {"type": [_type], "values": self._complex.size_list}

        if self._definer_type in (self._slits, "slits"):
            # get the list of the slits motors range
            _low_w, _high_w = self._slits["width"].get_limits()
            _low_h, _high_h = self._slits["height"].get_limits()
        return {
            "type": ["range", "range"],
            "values": [_low_w, _high_w, _low_h, _high_h],
        }

        return None

    def _set_slits_size(self, size=None):
        """ Move the slits to the desired position.
        Args:
            size (list): Width, heigth [mm].
        Raises:
            RuntimeError: Size out of the limits.
               TypeError: Invalid size
        """
        w_lim = self._slits["width"].get_limits()
        h_lim = self._slits["heigth"].get_limits()
        try:
            if min(w_lim) > size[0] > max(w_lim):
                raise RuntimeError("Size out of the limits")
            if min(h_lim) > size[1] > max(h_lim):
                raise RuntimeError("Size out of the limits")
            self._slits["width"].set_value(size[0])
            self._slits["heigth"].set_value(size[1])
        except TypeError:
            raise TypeError("Invalid size")

    def _set_aperture_size(self, size=None):
        """ Move the aperture to the desired size.
        Args:
            size (str): The position name.
        """
        self._aperture.set_value(int(size))

    def _set_complex_size(self, size=None):
        """ Move the complex definer to the desired size.
        Args:
            size (str): The position name.
        """
        self._complex.set_value(size)

    def _set_value(self, size=None):
        """Set the beam size
        Args:
            size (list): Width, heigth or
                  (str): Aperture or complex definer name.
        Raises:
            RuntimeError: Beam definer not configured
                          Size out of the limits.
        """

        if self._definer_type in (self._slits, "slits"):
            self._set_slits_size(size)

        if self._definer_type in (self._aperture, "aperture"):
            self._set_aperture_size(size)

        if self._definer_type in (self._complex, "complex"):
            self._set_complex_size(size)

    def get_beam_position_on_screen(self):
        if self._beam_position_on_screen == (0, 0):
            try:
                self._beam_position_on_screen = HWR.beamline.diffractometer.get_beam_position()
            except AttributeError:
                self._beam_position_on_screen = (
                    HWR.beamline.sample_view.camera.get_width() / 2,
                    HWR.beamline.sample_view.camera.get_height() / 2,
                )
        return self._beam_position_on_screen

    def set_beam_position_on_screen(self, beam_x_y):
        """Set the beam position
        Returns:
            beam_x_y (tuple): Position (x, y) [pixel]
        """
        self._beam_position_on_screen = beam_x_y

    ##AJOUTER get_beam_size | get_beam_shape
    def get_beam_shape(self):
        """
        Returns:
            beam_shape: Enum BeamShape
        """
        self.evaluate_beam_info()
        return self._beam_shape

    def get_beam_size(self):
        """
        Returns:
            (tuple): two floats
        """
        self.evaluate_beam_info()
        return self._beam_width, self._beam_height

    def evaluate_beam_info(self):
        """
        Method called if aperture, slits or focusing has been changed
        Returns: dictionary, {size_x: 0.1, size_y: 0.1, shape: BeamShape enum}
        """
        self._beam_info_dict["size_x"] = self._beam_width
        self._beam_info_dict["size_y"] = self._beam_height
        self._beam_info_dict["shape"] = self._beam_shape

        return self._beam_info_dict