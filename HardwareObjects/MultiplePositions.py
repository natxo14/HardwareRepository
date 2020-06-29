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
    <poisition>
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

    name:           moveToPosition
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

TEMPLATE
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
        <position>
            <name>12X</name>
            <zoom>2</zoom>
            <resox>0.0000004</resox>
            <resoy>0.0000004</resoy>
            <beamx>200</beamx>
            <beamy>200</beamy>
        </position>
    </positions>
</equipment>"""

try:
    from xml.etree import cElementTree  # python2.5
except ImportError:
    import cElementTree

from HardwareRepository.BaseHardwareObjects import Equipment
from HardwareRepository.BaseHardwareObjects import HardwareObjectState
import logging


class MultiplePositions(Equipment):
    def init(self):
        try:
            self.mode
        except AttributeError:
            self.mode = "absolute"

        motors = self["motors"]

        self.motor_hwobj_list = []
        #print(f"@@@@@@@@@@@@@@@@@@@@@@ motors {motors} {type(motors)} is None - {motors is None} - {motors.objectsNames()}")
        for mot in motors:
                name = mot.getProperty("name")
                temp_motor_hwobj = self.getObjectByRole(name)
                if temp_motor_hwobj is not None:
                    self.motor_hwobj_list.append(temp_motor_hwobj)
                print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS motors  name {name} motor {type(temp_motor_hwobj)} - {id(temp_motor_hwobj)}")

        #self.roles = motors.getRoles()
        self.roles = self.getRoles()
        tmp = self.getObjectByRole("zoom")
        print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS tmp {tmp} {type(tmp)}")
        self.deltas = {}
        try:
            # WARNING self.deltas is a LINK to the INTERNAL properties dictionary
            # modifying it modifies the GLOBAL properties, not just the local copy
            # Maybe do self["deltas"].getProperties().copy()?
            self.deltas = self["deltas"].getProperties()
        except BaseException:
            logging.getLogger().error("No deltas.")

        self.roles_positions = {}
        self.positions = {}
        self.positions_names_list = []
        try:
            positions = self["positions"]
            print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS positions {positions} {type(positions)}")
        except BaseException:
            logging.getLogger().error("No positions.")
        else:
            for position in positions:
                name = position.getProperty("name")
                #print(f"name {name}")
                if name is not None:
                    self.positions_names_list.append(name)
                    self.roles_positions[name] = {}

                    motpos = position.getProperties()
                    motroles = list(motpos.keys())
                    print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS motpos {motpos}")
                    #print(f"motroles {motroles}")

                    for role in self.roles:
                        #print(f"role {role}")
                        self.roles_positions[name][role] = motpos[role]
                        print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS self.roles_positions[{name}][{role}] - {self.roles_positions[name][role]}")
                else:
                    logging.getLogger().error("No name for position.")

        self.motors = {}
        #print(f"@@@@@@@@@@@@@@@@@@@@@@  motors {type(motors)}")
        ##print(f"@@@@@@@@@@@@@@@@@@@@@@  self.roles {self.roles}")
        #for mot in self["motors"]:
        for mot in self.motor_hwobj_list:
            print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS - for mot in self.motor_hwobj_list - name - {mot.name} mot {id(mot)}")
            #self.motors[mot.getMotorMnemonic()] = mot
            self.connect(mot, "moveDone", self.checkPosition)
            self.connect(mot, "valueChanged", self.checkPosition)
            self.connect(mot, "stateChanged", self.stateChanged)

        #for key, value in self.roles_positions.items():
            #print(f"key {key} value {value}")
            #for key2, value2 in value.items():
        #print(f"$$$$$$$$$$$$$$$ self.roles_positions {self.roles_positions} ")
        self.positions = self.get_positions()

    def get_positions(self):
        positions = []
        try:
            for el in self["positions"]:
                positions.append(
                    {
                        "name": el.getProperty("name"),
                        "zoom": el.getProperty("zoom"),
                        "beamx": el.getProperty("beamx"),
                        "beamy": el.getProperty("beamy"),
                        "resox": el.getProperty("resox"),
                        "resoy": el.getProperty("resoy"),
                        "resox": el.getProperty("resox"),
                        "resoy": el.getProperty("resoy"),
                    }
                )
        except IndexError:
            pass
        return positions 

    def get_positions_names_list(self):
        return self.positions_names_list

    def get_state(self):
        if not self.is_ready():
            return ""

        state = "READY"
        print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS - get_state - {len(self.motor_hwobj_list)}")
            
        for mot in self.motor_hwobj_list:
            print(f"@@@@@@@@@@@@@@@@ MULTIPLE POS - for mot in self.motor_hwobj_list - mot {id(mot)}")
            if mot.get_state() == HardwareObjectState.BUSY:
                state = "MOVING"
            elif mot.get_state() in {HardwareObjectState.UNKNOWN,
                                      HardwareObjectState.WARNING,
                                      HardwareObjectState.FAULT,
                                      HardwareObjectState.OFF}:
                return "UNUSABLE"

        return state

    def stateChanged(self, state):
        self.emit("stateChanged", (self.get_state(),))
        self.checkPosition()

    def moveToPosition(self, name, wait=False):
        #print(f"$$$$$$$$$$$$$$$ moveToPosition {name} ")

        move_list = []
        for role in self.roles:
            device = self.getObjectByRole(role)
            pos = self.roles_positions[name][role]
            move_list.append((device, pos))
        #print(f"$$$$$$$$$$$$$$$ moveToPosition  move_list {move_list} ")
        for mot, pos in move_list:
            if mot is not None:
                #print(f"$$$$$$$$$$$$$$$ moveToPosition  mot.set_value(pos) {mot} {pos} ")
                mot.set_value(pos)

        if wait:
            [mot.waitEndOfMove() for mot, pos in move_list if mot is not None]
        """
        for mne,pos in self.roles_positions[name].items():
        self.motors[mne].set_value(pos)
        """
    def get_positions(self):
        """
        return the dictionary of all the positions with all properties
        """
        return self.positions

    def get_current_position(self):
        """
        return current position's all properties
        """
        current_position = self.get_value()
        return self.positions.get(current_position)

    def get_value(self):
        """
        Returns the name of the current position
        It checks the positions of all the 'role' motors
        If all of them are within +/- delta tolerance, return pos name
        """
        #print(f"$$$$$$$$$$$$$$$MULTIPOSHWR get_value ")
        if not self.is_ready():
            #print(f"$$$$$$$$$$$$$$$MULTIPOSHWR get_value - not self.is_ready() ")
            return None

        for posName, position in self.roles_positions.items():
            findPosition = 0

            for role in self.roles:
                #print(f"$$$$$$$$$$$$$$$MULTIPOSHWR get_value  - role {role} ")
                pos = position[role]
                role_str = "\"" + str(role) + "\""
                mot = self.getObjectByRole(role)
                #print(f"$$$$$$$$$$$$$$$MULTIPOSHWR mot  - {type(mot)} -")
                
                #print(f"$$$$$$$$$$$$$$$MULTIPOSHWR get_value  - pos {pos} -")
                if mot is not None:
                    motpos = mot.get_value()
                    #print(f"$$$$$$$$$$$$$$$MULTIPOSHWR get_value  - motpos {motpos} -")
                    try:
                        if (
                            motpos < pos + self.deltas[role]
                            and motpos > pos - self.deltas[role]
                        ):
                            findPosition += 1
                    except BaseException:
                        continue

            if findPosition == len(self.roles):
                return posName

        return None

    def checkPosition(self, *args):
        if not self.is_ready():
            #print(f"checkPosition not self.is_ready() { self.is_ready()}")
            return None

        posName = self.get_value()

        if posName is None:
            self.emit("no_position", ())
            return None
        else:
            self.emit("predefinedPositionChanged", (posName,))
            #print(f"checkPosition emit(predefinedPositionChanged) {posName}")
            return posName

    def setNewPositions(self, name, newPositions):
        position = self.__getPositionObject(name)

        if position is None:
            self.checkPosition()
            return

        for role, pos in list(newPositions.items()):
            self.roles_positions[name][role] = pos
            position.setProperty(role, pos)

        self.checkPosition()
        self.commit_changes()

    def get_position_key_value(self, name, key):
        position = self.__getPositionObject(name)

        if position is None:
            return None

        return position.getProperty(key)

    def setPositionKeyValue(self, name, key, value):
        xml_tree = cElementTree.fromstring(self.xml_source())
        positions = xml_tree.find("positions")

        pos_list = positions.findall("position")
        for pos in pos_list:
            if pos.find("name").text == name:
                if pos.find(key) is not None:
                    position = self.__getPositionObject(name)
                    position.setProperty(key, str(value))
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


"""
        xml_tree = cElementTree.fromstring(self.xml_source())
        for elt in xml_tree.findall(".//position"):
           if elt.find("name").text=="12X":
             new_elt = cElementTree.Element("bidule")
             new_elt.text = "HELLO"
             elt.append(new_elt)
        self.rewrite_xml(cElementTree.tostring(xml_tree))
"""
