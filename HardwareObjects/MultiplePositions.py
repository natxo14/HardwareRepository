"""
TITLE
MultiplePositions Hardware Object

DESCRIPTION
This object manages the movement of several motors to predefined positions.

<username> : name of the multiplepositions object
<mode>     : there is two ways of managing the change of predefined positions
              absolute: change the value of a predefined position by another
                        absolute position
              relative: do not change the absolute value of the predefined
                        position but the user value of the motors concerned

<motors>
    <device role="role1" ... :list of motors to be moved to reach a predefined
    <device role="role2" ...  position. the "role" will be used to referenced
        ...                   the motors in the definitions of the predefined
<motors>                      positions

<deltas>                    : for each motor you define the windows used to
    <role1>val1</role1>       determine that a motor as reach a position
    <role2>val2</role2>
    ...
</deltas>

<positions>
    <position>
        <name>      : name of a predefined position. Must be unique in the file
        <role1>val1 : position of the motor "role1" for the predefined position
                     "name"
        <role2>val2 : position of the motor "role2" for the predefined position
                     "name"
        <resoy>8.69565217391e-07</resoy> : for all the position, independant
        <beamx>100</beamx>                 value with keyword can be added,
                                           saved, read ...
    </position>
    ...
</position>


METHOD
    name:           get_state
    input par.:     None
    output par.:    state
    description:    return an and on the state of all the  motor used in the
                    object

    name:           move_to_position
    input par.:     name
    output par.:    None
    description:    move all motors to the predefined position "position"

    name:           get_value
    input par.:     None
    output par.:    position
    description:    return the name of the current predefined position.
                    return None if all motors are not in their psotion

    name:           setNewPositions
    input par.:     name, newPositions
    output par.:    None
    description:    For the position "name", change the motors positions set
                    in "newPositions", a dictionary with motor role as keys
                    and new motor position as values.
                    Save the new values in the xml file

    name:           get_position_key_value
    input par.:     name, key
    output par.:    value
    description:    return the value of the independant "key" field of
                    the predefined position "name"

    name:           setPositionKeyValue
    input par.:     name, key, value
    output par.:    None
    description:    Change in the object and in the xml file the value of the
                    independant field "key" in the predefined position "name"

    name:           getRoles
    input par.:     None
    output par.:    roles[]
    description:    return the list of motor's role used in the objects

    name:           save_data_to_file
    input par.:     None
    output par.:    None    
    description:    save data of beamline pos or calibration to xml file

    name:           cancel_edited_data
    input par.:     None
    output par.:    None    
    description:    to be connected to all "Cancel edited data" event
                    in any brick. It will reload data from xml file
                    and send it back to the rest of bricks

    name:           edit_data
    input par.:     positions_dict {}
    output par.:    None    
    description:    to be connected to all "Data edited" event/signal
                    from any brick. It will update positions dict and
                    send send it back to the rest of bricks through a
                    signal beam_pos_cal_data_changed


SIGNAL
    name:           stateChanged
    parameter:      state
    description:    send the new state of the object when it changes

    name:           no_position
    parameter:      None
    description:    sent when after a position change of any of the motor
                    the object is not in any of the predefined positions

    name:           predefinedPositionChanged
    parameter:      positionName
    description:    sent when after a position change of any of the motor
                    the object has reach a predefined position.
                    The parameter is the name of this position.

    name:           beam_pos_cal_data_changed
    parameter:      positions_dict {},
                    Union : 0 (beam changed), 1 (calib changed), 2 (other)
    description:    sent when after data concerning beam position or
                    camera calibration is edited
                    The parameter is the whole dict of positions
    
    name:           beam_pos_cal_data_saved
    parameter:      None
    description:    sent when data concerning beam position or
                    camera calibration has been saved to xml file
    
    name:           beam_pos_cal_data_cancelled
    parameter:      None
    description:    sent when cancelling changes in data:
                    reload data from file and clear data display

TEMPLATE FOR PARTICULAR CASE OF ZOOM POSITIONS CONFIG FILE:
<equipment class="MultiplePositions">
    <username>VLM Zoom</username>
    <mode>absolute</mode>
    <motors>
        <device role="zoom" hwrid="/berru/zoom"></device>
    </motors>

    <deltas>
        <zoom>0.1</zoom>
    </deltas>

    <positions>
        <position>
            <name>1X</name>
            <zoom>0</zoom>
            <resox>-4.16666666667e-07</resox>
            <resoy>7.35294117647e-07</resoy>
            <beamx>537</beamx>
            <beamy>313</beamy>
        </position>
        <position>
            <name>6X</name>
            <zoom>1</zoom>
            <resox>-5.52486187845e-07</resox>
            <resoy>8.69565217391e-07</resoy>
            <beamx>100</beamx>
            <beamy>100</beamy>
        </position>
    </positions>
</equipment>"""

try:
    from xml.etree import cElementTree  # python2.5
except ImportError:
    import cElementTree

from HardwareRepository.BaseHardwareObjects import Equipment
from HardwareRepository.BaseHardwareObjects import HardwareObjectState
from HardwareRepository import HardwareRepository as HWR
import logging

import copy

class MultiplePositions(Equipment):
    """
    CODING NOTES:
    THIS HWRObject handles access/edition/saving to multiple-positions xml file

    In the PARTICULAR CASE that the xml file holds information about ZOOM motor's
    positions on a diffractometer:
        This avoids data duplication on all the bricks that need access to that xml file

        It will read the file, create self.zoom_positions_dict structure, receive edit data signals
        from bricks, send update data signals to bricks

        Bricks will call methods to:
        - recover/reload data to display in their guis
        - save data in xml file
        - edit the data

        Data will be kept/updated in self.zoom_positions_dict structure
        If data saved, then written in xml file
        if data cancelled, then data reloaded from last saved xml file
    """

    def __init__(self, *args):
        """
        Descrip. :
        """
        Equipment.__init__(self, *args)

        self.motor_obj = None

        self.motor_hwobj_dict = {}
        #{ "motor_name" : motor_hwr_obj }

        self.positions_dict = {}
        # generic case:
        # { "position_name" : { "property0" : val0
        #                      "property1" : val1
        
      
        self.zoom_positions_dict = {}
        # FOR PARTICULAR CASE WHEN MULTIPLE POSITIONS OF A ZOOM MOTOR
        # if "zoom" in self.roles_positions_dict:
        # { "position_name" : { "beam_pos_x" : val, int - pixels
        #                      "beam_pos_y" : val, int - pixels
        #                      "cal_x" : val, int - nm / pixel
        #                      "cal_y" : val, int - nm / pixel
        #                      "light" : val,
        #                      "zoom" : val,
        #                      "zoom_tag" : position_name
        #                     },
        #}

        self.roles = None
        self.deltas = None
        

        self.multipos_file_xml_path = None

    def init(self):
        try:
            self.mode
        except AttributeError:
            self.mode = "absolute"
        
        # init self.motor_hwobj_dict
        # for mot in self["motors"]:
        #     name = mot.getProperty("name")
        #     temp_motor_hwobj = self.getObjectByRole(name)
        #     if temp_motor_hwobj is not None:
        #         self.motor_hwobj_dict[name] = temp_motor_hwobj
        #     print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS motors  name {name} motor {type(temp_motor_hwobj)} - {id(temp_motor_hwobj)}")

        self.roles = self.getRoles()
        for role in self.roles:
            print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS motors  role in self.roles {role} type {type(role)}")
        
        self.deltas = {}
        try:
            # WARNING self.deltas is a LINK to the INTERNAL properties dictionary
            # modifying it modifies the GLOBAL properties, not just the local copy
            # Maybe do self["deltas"].getProperties().copy()?
            self.deltas = self["deltas"].getProperties()
        except BaseException:
            logging.getLogger().error("No deltas.")
        print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS self.deltas {self.deltas} type {type(self.deltas)}")

        #self.roles_positions_dict = {}
        # self.positions = []
        
        #init self.zoom_positions_dict and self.roles_positions_dict
        try:
            positions = self["positions"]
            print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS positions {positions} {type(positions)}")
        except BaseException:
            logging.getLogger().error("No positions.")
        else:
            for position in positions:
                name = position.getProperty("name")
                if name is not None:
                    
                    motpos = position.getProperties()
                    print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS motpos {motpos}")
                    
                    # check if "zoom" exist: PARTICULAR CASE
                    zoom_val = position.getProperty("zoom")
                    if zoom_val is not None:
                        #create zoom position dict
                        pos_x = int(position.getProperty("beamx", 0))
                        pos_y = int(position.getProperty("beamy", 0))
                        cal_x = abs(float(position.getProperty("resox", 0)) * 1e9)
                        cal_y = abs(float(position.getProperty("resoy", 0)) * 1e9)
                        light_val = int(position.getProperty("light", 0))
                        zoom_val = int(position.getProperty("zoom", -1))
                        
                        dict_elem = {"beam_pos_x" : pos_x,
                                    "beam_pos_y" : pos_y,
                                    "cal_x" : cal_x,
                                    "cal_y" : cal_y,
                                    "light" : light_val,
                                    "zoom" : zoom_val,
                                    "zoom_tag" : name
                        }
                        self.zoom_positions_dict[name] = dict_elem
                    
                    
                    # general case
                    self.positions_dict[name] = {}
                    # consider
                    motor_pos = position.getProperties()
                    
                    for role in self.roles:
                        self.positions_dict[name][role] = motor_pos[role]

                    for role in self.roles:
                        temp_motor_hwobj = self.getObjectByRole(role)
                        if temp_motor_hwobj is not None:
                            self.motor_hwobj_dict[role] = temp_motor_hwobj
                    
                    # elem = {}
                    # for role in self.roles:
                    #     print(f"role {role} name {name} motpos {motpos}")
                    #     elem[role] = motpos[role]
                    #self.roles_positions_dict[name] = elem
                    #print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS self.roles_positions_dict - {self.roles_positions_dict}")
                else:
                    logging.getLogger().error("No name for position.")

        for mot in self.motor_hwobj_dict.values():
            print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS - for mot in self.motor_hwobj_dict - name - {mot.name()} mot {id(mot)}")
            self.connect(mot, "valueChanged", self.checkPosition)
            self.connect(mot, "stateChanged", self.stateChanged)

        if HWR.beamline.sample_view is not None:
            print(f"##################@@@@@@@@@@@@@@@@ MULTIPLE POS update_beam_position HWR.beamline.beam not none")
            self.connect(HWR.beamline.sample_view,
                        "beam_position_data_changed",
                        self.beam_position_data_changed
            )
        else:
            print(f"##################@@@@@@@@@@@@@@@@ MULTIPLE POS HWR.beamline.sample_view NONE")
            

        # self.positions = self.read_positions()
        print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS self.positions {self.positions_dict}")
    
    def get_zoom_hwr_obj(self):
        return self.motor_hwobj_dict.get("zoom", None)
    
    def get_zoom_positions(self):
        """
        returns
        tag_dict:
        { 
            "pos_namei" : zoom_valuei,
        }
        """
        zoom_pos_dict = {}
        for pos_name in self.zoom_positions_dict:
            zoom_pos_dict[pos_name] = self.zoom_positions_dict[pos_name]["zoom"]
        
        return zoom_pos_dict
   
    def beam_position_data_changed(self, new_beam_pos_data):
        """
        Slot when beam position data is edited through camera brick / QtGraphicsManager
        """
        print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS - for beam_position_data_changed {new_beam_pos_data}")
        
        current_pos_name = self.get_value()
        if current_pos_name is not None:
            dict_elem = self.zoom_positions_dict[current_pos_name]
            dict_elem["beam_pos_x"] = new_beam_pos_data[0]
            dict_elem["beam_pos_y"] = new_beam_pos_data[1]
        
        self.zoom_positions_dict[current_pos_name] = dict_elem

        self.emit(
            "beam_pos_cal_data_changed",
            0,
        )
    
    def calibration_data_changed(self, new_calibration_data):
        """
        Slot when beam position data is edited through camera brick / QtGraphicsManager
        """
        current_pos_name = self.get_value()
        if current_pos_name is not None:
            dict_elem = self.zoom_positions_dict[current_pos_name]
            dict_elem["cal_x"] = new_calibration_data[0]
            dict_elem["cal_y"] = new_calibration_data[1]
        
        self.zoom_positions_dict[current_pos_name] = dict_elem

        self.emit(
            "beam_pos_cal_data_changed",
            1,
        )

    def edit_data(self, edited_data_elem, data_key=None, who_changed=0):
        """
        Slot when beam position data is edited through camera brick / QtGraphicsManager
        """
        #if no data_key given, use current position
        if data_key is None:
            data_key = self.get_value()
        if data_key is None:
            return

        self.zoom_positions_dict[data_key] = edited_data_elem

        self.emit(
            "beam_pos_cal_data_changed",
            who_changed
        )

    def get_positions_names_list(self):
        return list(self.positions_dict.keys())

    def get_state(self):
        if not self.is_ready():
            return ""

        state = HardwareObjectState.READY
            
        for motor_hwobj in self.motor_hwobj_dict.values():
            if motor_hwobj.get_state() == HardwareObjectState.BUSY:
                state = HardwareObjectState.BUSY
            if motor_hwobj.get_state() in {HardwareObjectState.UNKNOWN,
                                      HardwareObjectState.WARNING,
                                      HardwareObjectState.FAULT,
                                      HardwareObjectState.OFF}:
                return motor_hwobj.get_state()
        
        return state

    def stateChanged(self, state):
        self.emit("stateChanged", (self.get_state(),))
        self.checkPosition()

    def move_to_position(self, name, wait=True):
        """
        move to position with name = name
        """
        print(f"$$$$$$$$$$$$$$$ MULTIPLE POS move_to_position {name} ")
        
        position_props = self.positions_dict.get(name, None)
        
        if position_props is None:
            return

        for role in self.roles:
            role_position = position_props.get(role, None)
            
            if role_position is None:
                continue

            motor = self.motor_hwobj_dict.get(role, None)
            if motor is None:
                continue
        
            motor.set_value(role_position)
            
        if wait:
            [mot.wait_end_of_move(4) for mot in self.motor_hwobj_dict.values() if mot is not None]
        
        print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS - move_to_position - {name} - self {id(self)}")
        self.emit("predefinedPositionChanged", name)
        
    def get_positions(self):
        """
        return the dict of all the positions with all properties
        """
        return copy.deepcopy(self.zoom_positions_dict)
    
    def get_position(self, pos_name):
        """
        return all properties of position with name pos_name as dict
        """
        return self.zoom_positions_dict.get(pos_name, None)

    def get_current_position(self):
        """
        return current position's all properties as dict
        """
        current_position = self.get_value()

        return self.zoom_positions_dict.get(current_position, None)
    
    def get_value(self):
        """
        Returns the name of the current position
        It checks the positions of all the 'role' motors
        If all of them are within +/- delta tolerance, return pos name
        """
        print(f"$$$$$$$$$$$$$$$MULTIPOSHWR get_value self.roles {self.roles}")
        if not self.is_ready():
            return None

        for pos_name, position in self.positions_dict.items():
            find_position = 0

            for role in self.roles:
                pos = position[role]
                mot = self.motor_hwobj_dict.get(role, None)
                
                if mot is not None:
                    motpos = mot.get_value()
                    try:
                        if (
                            motpos < pos + self.deltas[role]
                            and motpos > pos - self.deltas[role]
                        ):
                            find_position += 1
                    except BaseException:
                        continue

                    if find_position > 0:
                        print(f"$$$$$$$$$$$$$$$MULTIPOSHWR get_value findPosition  - {find_position} - motor name {mot.name()} - position {motpos} - ")                
          
            if find_position == len(self.roles):
                return pos_name
        return None

    def checkPosition(self, *args):
        if not self.is_ready():
            print(f"checkPosition not self.is_ready() { self.is_ready()}")
            return None

        pos_name = self.get_value()

        print(f"checkPosition pos_name {pos_name}")
        if pos_name is None:
            self.emit("no_position", (None))
            print(f"$$$$$$$$$$$$$$$MULTIPOSHWR  checkPosition emit(no_position) {pos_name}")
            return None
        else:
            print(f"$$$$$$$$$$$$$$$MULTIPOSHWR  checkPosition emit(predefinedPositionChanged) {pos_name}")
            self.emit("predefinedPositionChanged", (pos_name,))
            return pos_name

    def setNewPositions(self, name, newPositions):
        position = self.__getPositionObject(name)

        if position is None:
            self.checkPosition()
            return

        for role, pos in list(newPositions.items()):
            self.positions_dict[name][role] = pos
            position.setProperty(role, pos)

        self.checkPosition()
        self.commit_changes()

    def get_position_key_value(self, name, key):
        position = self.get_position(name)
        return position[key]
    
    def cancel_edited_data(self):
        self.reload_data_from_xml_file()
        
    def reload_data_from_xml_file(self):
        """
        usefull when, after changing data, cancel changes
        """
        """
        Parse xml file and load dict :

        { "position_name" : { "beam_pos_x" : val,int - pixels  
                             "beam_pos_y" : val,int - pixels
                             "cal_x" : val,int - nm
                             "cal_y" : val,int - nm
                             "light" : val,
                             "zoom" : val,
                            },
        }
        """
        output_dict = {}
        xml_file_tree = cElementTree.parse(self.multipos_file_xml_path)

        xml_tree = xml_file_tree.getroot()
        positions = xml_tree.find("positions")

        pos_list = positions.findall("position")
        
        for pos in pos_list:
            
            if pos.find("beamx") is not None:
                pos_x = self.from_text_to_int(pos.find("beamx").text)
            else:
                pos_x = 0
            if pos.find("beamy") is not None:
                pos_y = self.from_text_to_int(pos.find("beamy").text)
            else:
                pos_y = 0
            if pos.find("resox") is not None:
                cal_x = self.from_text_to_float(pos.find("resox").text, 1e9)
            else:
                cal_x = 0
            if pos.find("resoy") is not None:
                cal_y = self.from_text_to_float(pos.find("resoy").text, 1e9)
            else:
                cal_y = 0
            if pos.find("light") is not None:
                light_val = self.from_text_to_int(pos.find("light").text)
            else:
                light_val = 0
            if pos.find("zoom") is not None:
                zoom_val = self.from_text_to_int(pos.find("zoom").text)
            else:
                zoom_val = -1
            
            dict_elem = {"beam_pos_x" : pos_x,
                        "beam_pos_y" : pos_y,
                        "cal_x" : cal_x,
                        "cal_y" : cal_y,
                        "zoom" : zoom_val,
                        "light" : light_val,
            }
            output_dict[pos.find('name').text] = dict_elem
            
        self.zoom_positions_dict = copy.deepcopy(output_dict)

    def save_data_to_file(self, path):
        
        #open xml file
        xml_file_tree = cElementTree.parse(path)

        xml_tree = xml_file_tree.getroot()
        positions = xml_tree.find("positions")
        
        pos_list = positions.findall("position")

        print(f"save_data_to_file positions_dict {self.zoom_positions_dict} ")
            
        for pos in pos_list:
            pos_name = pos.find('name').text
            print(f"save_data_to_file pos_name {pos_name} ")
            if pos.find('beamx') is not None:
                pos.find('beamx').text = str(self.zoom_positions_dict[pos_name]["beam_pos_x"])
            if pos.find('beamy') is not None:
                pos.find('beamy').text = str(self.zoom_positions_dict[pos_name]["beam_pos_y"])
            if pos.find('resox') is not None:
                pos.find('resox').text = str(self.zoom_positions_dict[pos_name]['cal_x'] * 1e-9)
            if pos.find('resoy') is not None:
                pos.find('resoy').text = str(self.zoom_positions_dict[pos_name]['cal_y'] * 1e-9)
            if pos.find('light') is not None:
                pos.find('light').text = str(self.zoom_positions_dict[pos_name]['light'])
            if pos.find('zoom') is not None:
                pos.find('zoom').text = str(self.zoom_positions_dict[pos_name]['zoom'])
    
        xml_file_tree.write(path)

        self.emit("beam_pos_cal_data_saved", )

    def set_position_key_value(self, name, key, value):

        position = self.zoom_positions_dict.get(name, None)
        if position is not None:
            position[key] = value
        
    def setPositionKeyValue(self, name, key, value):
        # from PyQt5.QtCore import pyqtRemoveInputHook
        # pyqtRemoveInputHook()
        # import pdb
        # pdb.set_trace()

        xml_tree = cElementTree.fromstring(self.xml_source())
        positions = xml_tree.find("positions")

        pos_list = positions.findall("position")
        for pos in pos_list:
            if pos.find("name").text == name:
                if pos.find(key) is not None:
                    position = self.__getPositionObject(name)
                    print(f"position : {position} - value {value} - key {key}")
                    pdb.set_trace()
                    position.setProperty(key, str(value))
                    pdb.set_trace()
                    self.commit_changes()
                    return True
                else:
                    key_el = cElementTree.SubElement(pos, key)
                    key_el.text = value
                    print((cElementTree.tostring(xml_tree)))
                    self.rewrite_xml(cElementTree.tostring(xml_tree))
                    return True

        return False

    def __getPositionObject(self, name):
        for position in self["positions"]:
            if position.getProperty("name") == name:
                return position

        return None

    def get_roles(self):
        return self.roles

    def addPosition(self, el_dict):
        xml_tree = cElementTree.fromstring(self.xml_source())
        positions = xml_tree.find("positions")

        pos = cElementTree.SubElement(positions, "position")

        for key, val in el_dict.items():
            sel = cElementTree.SubElement(pos, key)
            sel.text = val

        self.rewrite_xml(cElementTree.tostring(xml_tree))

    def remPosition(self, name):
        xml_tree = cElementTree.fromstring(self.xml_source())
        positions = xml_tree.find("positions")

        pos_list = positions.findall("position")
        for pos in pos_list:
            if pos.find("name").text == name:
                positions.remove(pos)

        self.rewrite_xml(cElementTree.tostring(xml_tree))

    def addField(self, name, key, val):
        pass

    def remField(self, name, key):
        pass
    
    def from_text_to_int(self, input_str, factor=1):
        if input_str is None:
            return 0
        return abs(int(float(input_str) * factor))

    def from_text_to_float(self, input_str, factor=1):
        if input_str is None:
            return 0
        return abs((float(input_str) * factor))