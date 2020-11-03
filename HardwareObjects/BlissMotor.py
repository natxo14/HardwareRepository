# encoding: utf-8
#
#  Project: MXCuBE
#  https://github.com/mxcube.
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
#  You should have received a copy of the GNU General Lesser Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.
"""
Example xml file:
<device class="BlissMotor">
  <username>Detector Distance</username>
  <actuator_name>dtox</actuator_name>
  <tolerance>1e-2</tolerance>
</device>
"""

import time
import gevent
from gevent import Timeout
import logging

import enum
from bliss.config import static
from HardwareRepository.HardwareObjects.abstract.AbstractMotor import AbstractMotor
from HardwareRepository.BaseHardwareObjects import HardwareObjectState

__copyright__ = """ Copyright © 2019 by the MXCuBE collaboration """
__license__ = "LGPLv3+"


@enum.unique
class BlissMotorStates(enum.Enum):
    """"
    MOVING  : 'Axis is moving'
    READY   : 'Axis is ready to be moved (not moving ?)'
    FAULT   : 'Error from controller'
    LIMPOS  : 'Hardware high limit active'
    LIMNEG  : 'Hardware low limit active'
    HOME    : 'Home signal active'
    OFF     : 'Axis power is off'
    DISABLED: 'Axis cannot move (must be enabled - not ready ?)'
    """

    MOVING = 0
    READY = 1
    FAULT = 2
    LIMPOS = 3
    LIMNEG = 4
    HOME = 5
    OFF = 6
    DISABLED = 7
    UNKNOWN = 8
    INCLOSEDLOOPWINDOW = 9


class BlissMotor(AbstractMotor):
    """Bliss Motor implementation"""

    SPECIFIC_STATES = BlissMotorStates
    SPECIFIC_TO_HWR_STATE = {
        "MOVING": HardwareObjectState.BUSY,
        "READY": HardwareObjectState.READY,
        "FAULT": HardwareObjectState.FAULT,
        "LIMPOS": HardwareObjectState.READY,
        "LIMNEG": HardwareObjectState.READY,
        "INCLOSEDLOOPWINDOW": HardwareObjectState.READY,
        "HOME": HardwareObjectState.READY,
        "OFF": HardwareObjectState.OFF,
        "DISABLED": HardwareObjectState.OFF,
        "UNKNOWN": HardwareObjectState.UNKNOWN,
    }

    def __init__(self, name):
        AbstractMotor.__init__(self, name)
        self.motor_obj = None

    def init(self):
        """Initialise the motor"""
        AbstractMotor.init(self)
        cfg = static.get_config()
        self.motor_obj = cfg.get(self.actuator_name)
        self.update_state(self.get_state())

        self.connect(self.motor_obj, "position", self.update_value)
        self.connect(self.motor_obj, "state", self._update_state)
        self.connect(self.motor_obj, "move_done", self._update_state_move_done)
        print("motor position_________", self.motor_obj, self.motor_obj.position)
        # init state - HardwareObjectState - to match motor's one
        #from PyQt5.QtCore import pyqtRemoveInputHook
        #pyqtRemoveInputHook()
        #import pdb
        #pdb.set_trace()

    def _state2enum(self, state):
        """Translate the state to HardwareObjectState and BlissMotorStates
        Args:
           state (string): state
        Returns:
           (tuple): (HardwareObjectState, BlissMotorStates)
        """
        try:
            _specific_state = BlissMotorStates[state]
        except (AttributeError, KeyError):
            _specific_state = BlissMotorStates.UNKNOWN

        _state = self.SPECIFIC_TO_HWR_STATE.get(state, HardwareObjectState.UNKNOWN)
        return _state, _specific_state
        
    def get_state(self):
        """Get the motor HardwareObjectState state.
        Returns:
            (enum 'HardwareObjectState'): Motor state.
        """
        state = HardwareObjectState.UNKNOWN
        for stat in self.motor_obj.state.current_states_names:
            if stat in HardwareObjectState.__members__:
                # if stat has direct translation on HardwareObjectState
                # return it . HardwareObjectState are mutual exclusive
                return HardwareObjectState[stat]
            if stat == "DISABLED":
                # we need to treat DISABLED before any other auxillary state
                return HardwareObjectState.OFF
            if stat == "MOVING":
                return HardwareObjectState.BUSY
            else:
                # translate first state from the 'current_states_names' list
                state = self._state2enum(stat)[0]
        return state

    def get_specific_state(self):
        """Get the motor state.
        Returns:
            TODO: make this clear
            Before (list): Motor states as list of BlissMotorStates enum
            get_specific_state used by HardwareObjectMixin: no list in that code

            Now : only one state from list: preconize 'error' status to return
        """
        state = self.motor_obj.state.current_states_names
        state_list = []
        state_list.append(self._state2enum(state[0])[1])
        if len(state) > 1:
            for _state in state[1:]:
                state_list.append(self._state2enum(_state)[1])
        
        if BlissMotorStates.FAULT in state_list:
            return BlissMotorStates.FAULT
        elif BlissMotorStates.OFF in state_list:
            return BlissMotorStates.OFF
        elif BlissMotorStates.DISABLED in state_list:
            return BlissMotorStates.DISABLED
        else:
            return state_list[0]

    def _update_state(self, bliss_state=None):
        logging.getLogger().info(f"""BLISSMOTOR {self.actuator_name} _update_state  - signal from BLISS : "state" . Param: {bliss_state}""")
        """Check if the state has changed. Emits signal stateChanged.
        Args:
            state (enum AxisState): state from a BLISS motor
        """
        if isinstance(bliss_state, bool):
            # It seems like the current version of BLISS gives us a boolean
            # at first and last event, True for ready and False for moving
            state = HardwareObjectState.READY if bliss_state else HardwareObjectState.BUSY
        else:
            # state comming from bliss (with current_states_names attribute)
            try:
                state = self.get_state()
            except (AttributeError, KeyError):
                state = HardwareObjectState.UNKNOWN
        self._specific_state = self.get_specific_state()
        self.update_state(state)

    def _update_state_move_done(self, bliss_state=None):
        # TODO : DELETE THIS (and connection with bliss motor signal)
        # THIS IS A COPY OF _update_state
        # this function created to tell from move_done and state bliss signals
        # debugging why takes so much time to update bliss motor status after the movement
        logging.getLogger().info(f"""BLISSMOTOR {self.actuator_name} _update_state_move_done - signal from BLISS "move_done" . Param: {bliss_state} . Calling _update_state""")
        self._update_state(bliss_state)
        # if isinstance(bliss_state, bool):
        #     # It seems like the current version of BLISS gives us a boolean
        #     # at first and last event, True for ready and False for moving
        #     state = HardwareObjectState.READY if bliss_state else HardwareObjectState.BUSY
        # else:
        #     # state comming from bliss (with current_states_names attribute)
        #     try:
        #         state = self.get_state()
        #     except (AttributeError, KeyError):
        #         state = HardwareObjectState.UNKNOWN
        # self._specific_state = self.get_specific_state()
        # self.update_state(state)

    def get_value(self):
        """Read the motor position.
        Returns:
            float: Motor position.
        """
        return self.motor_obj.position

    def get_limits(self):
        """Returns motor low and high limits.
        Returns:
            (tuple): two floats tuple (low limit, high limit).
        """
        # no limit = None, but None is a problematic value
        # for some GUI components (like MotorSpinBox), so
        # instead we return very large value.

        _low, _high = self.motor_obj.limits
        _low = _low if _low else -1e6
        _high = _high if _high else 1e6
        self._nominal_limits = (_low, _high)
        return self._nominal_limits

    def get_velocity(self):
        """Read motor velocity.
        Returns:
            (float): velocity [unit/s]
        """
        self._velocity = self.motor_obj.velocity
        return self._velocity

    def _set_value(self, value):
        """Move motor to absolute value.
        Args:
            value (float): target value
        """
        self.motor_obj.move(value, wait=False)

    def abort(self):
        """Stop the motor movement"""
        self.motor_obj.stop(wait=False)

    def name(self):
        """Get the motor name. Should be removed when GUI ready"""
        return self.actuator_name
    
    # def update_value(self, value=None):
    #     """Check if the value has changed. Emits signal valueChanged.
    #     Args:
    #         value (float): value
    #     """

    #     AbstractMotor.update_value(value)
    #     self.emit("valueChanged", (value,))

    def wait_end_of_move(self, timeout=None):
        """
        Descript. : waits till the motor stops
        """
        
        with gevent.Timeout(timeout, False):
            time.sleep(0.1)
            while self.get_state() == HardwareObjectState.BUSY:
                time.sleep(0.1)
