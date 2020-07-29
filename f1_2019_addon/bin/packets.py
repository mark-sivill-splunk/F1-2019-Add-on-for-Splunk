# -*- coding: utf-8 -*-

#
# msivill changes to add encoding at top of source
#


"""F1 2019 UDP Telemetry support package

This package is based on the CodeMasters Forum post documenting the F1 2019 packet format:

    https://forums.codemasters.com/topic/38920-f1-2019-udp-specification/

Compared to the definitions given there, the Python version has the following changes:

(1) In the 'PacketMotionData' structure, the comments for the three m_angularAcceleration{X,Y,Z} fields erroneously
    refer to 'velocity' rather than 'acceleration'. This was corrected.
(2) In the 'CarSetupData' structure, the comment of the m_rearAntiRollBar refer to rear instead of front. This was corrected.
(3) In the Driver IDs table, driver 34 has name "Wilheim Kaufmann".
    This is a typo; whenever this driver is encountered in the game, his name is given as "Wilhelm Kaufmann".
"""

import ctypes
import enum

#########################################################
#                                                       #
#  __________  PackedLittleEndianStructure  __________  #
#                                                       #
#########################################################

class PackedLittleEndianStructure(ctypes.LittleEndianStructure):
    """The standard ctypes LittleEndianStructure, but tightly packed (no field padding), and with a proper repr() function.

    This is the base type for all structures in the telemetry data.
    """
    _pack_ = 1

    def __repr__(self):
        fstr_list = []
        for (fname, ftype) in self._fields_:
            value = getattr(self, fname)
            if isinstance(value, (PackedLittleEndianStructure, int, float, bytes)):
                vstr = repr(value)
            elif isinstance(value, ctypes.Array):
                vstr = "[{}]".format(", ".join(repr(e) for e in value))
            else:
                raise RuntimeError("Bad value {!r} of type {!r}".format(value, type(value)))
            fstr = "{}={}".format(fname, vstr)
            fstr_list.append(fstr)
        return "{}({})".format(self.__class__.__name__, ", ".join(fstr_list))


###########################################
#                                         #
#  __________  Packet Header  __________  #
#                                         #
###########################################

class PacketHeader(PackedLittleEndianStructure):
    """The header for each of the UDP telemetry packets."""
    _fields_ = [
        ('packetFormat'     , ctypes.c_uint16),  # 2019
        ('gameMajorVersion' , ctypes.c_uint8 ),  # Game major version - "X.00"
        ('gameMinorVersion' , ctypes.c_uint8 ),  # Game minor version - "1.XX"
        ('packetVersion'    , ctypes.c_uint8 ),  # Version of this packet type, all start from 1
        ('packetId'         , ctypes.c_uint8 ),  # Identifier for the packet type, see below
        ('sessionUID'       , ctypes.c_uint64),  # Unique identifier for the session
        ('sessionTime'      , ctypes.c_float ),  # Session timestamp
        ('frameIdentifier'  , ctypes.c_uint32),  # Identifier for the frame the data was retrieved on
        ('playerCarIndex'   , ctypes.c_uint8 )   # Index of player's car in the array
    ]


@enum.unique
class PacketID(enum.IntEnum):
    """Value as specified in the PacketHeader.packetId header field, used to distinguish packet types."""

    MOTION        = 0
    SESSION       = 1
    LAP_DATA      = 2
    EVENT         = 3
    PARTICIPANTS  = 4  # 0.2 Hz (once every five seconds)
    CAR_SETUPS    = 5
    CAR_TELEMETRY = 6
    CAR_STATUS    = 7


PacketID.short_description = {
    PacketID.MOTION        : 'Motion',
    PacketID.SESSION       : 'Session',
    PacketID.LAP_DATA      : 'Lap Data',
    PacketID.EVENT         : 'Event',
    PacketID.PARTICIPANTS  : 'Participants',
    PacketID.CAR_SETUPS    : 'Car Setups',
    PacketID.CAR_TELEMETRY : 'Car Telemetry',
    PacketID.CAR_STATUS    : 'Car Status'
}


PacketID.long_description = {
    PacketID.MOTION        : 'Contains all motion data for player\'s car – only sent while player is in control',
    PacketID.SESSION       : 'Data about the session – track, time left',
    PacketID.LAP_DATA      : 'Data about all the lap times of cars in the session',
    PacketID.EVENT         : 'Various notable events that happen during a session',
    PacketID.PARTICIPANTS  : 'List of participants in the session, mostly relevant for multiplayer',
    PacketID.CAR_SETUPS    : 'Packet detailing car setups for cars in the race',
    PacketID.CAR_TELEMETRY : 'Telemetry data for all cars',
    PacketID.CAR_STATUS    : 'Status data for all cars such as damage'
}

#########################################################
#                                                       #
#  __________  Packet ID 0 : MOTION PACKET  __________  #
#                                                       #
#########################################################

class CarMotionData_V1(PackedLittleEndianStructure):
    """This type is used for the 20-element 'carMotionData' array of the PacketMotionData_V1 type, defined below."""
    _fields_ = [
        ('worldPositionX'     , ctypes.c_float),  # World space X position
        ('worldPositionY'     , ctypes.c_float),  # World space Y position
        ('worldPositionZ'     , ctypes.c_float),  # World space Z position
        ('worldVelocityX'     , ctypes.c_float),  # Velocity in world space X
        ('worldVelocityY'     , ctypes.c_float),  # Velocity in world space Y
        ('worldVelocityZ'     , ctypes.c_float),  # Velocity in world space Z
        ('worldForwardDirX'   , ctypes.c_int16),  # World space forward X direction (normalised)
        ('worldForwardDirY'   , ctypes.c_int16),  # World space forward Y direction (normalised)
        ('worldForwardDirZ'   , ctypes.c_int16),  # World space forward Z direction (normalised)
        ('worldRightDirX'     , ctypes.c_int16),  # World space right X direction (normalised)
        ('worldRightDirY'     , ctypes.c_int16),  # World space right Y direction (normalised)
        ('worldRightDirZ'     , ctypes.c_int16),  # World space right Z direction (normalised)
        ('gForceLateral'      , ctypes.c_float),  # Lateral G-Force component
        ('gForceLongitudinal' , ctypes.c_float),  # Longitudinal G-Force component
        ('gForceVertical'     , ctypes.c_float),  # Vertical G-Force component
        ('yaw'                , ctypes.c_float),  # Yaw angle in radians
        ('pitch'              , ctypes.c_float),  # Pitch angle in radians
        ('roll'               , ctypes.c_float)   # Roll angle in radians
    ]


class PacketMotionData_V1(PackedLittleEndianStructure):
    """The motion packet gives physics data for all the cars being driven.

    There is additional data for the car being driven with the goal of being able to drive a motion platform setup.

    N.B. For the normalised vectors below, to convert to float values divide by 32767.0f – 16-bit signed values are
    used to pack the data and on the assumption that direction values are always between -1.0f and 1.0f.

    Frequency: Rate as specified in menus
    Size: 1343 bytes
    Version: 1
    """
    _fields_ = [
        ('header'                 , PacketHeader         ),  # Header
        ('carMotionData'          , CarMotionData_V1 * 20),  # Data for all cars on track
        # Extra player car ONLY data
        ('suspensionPosition'     , ctypes.c_float * 4   ),  # Note: All wheel arrays have the following order:
        ('suspensionVelocity'     , ctypes.c_float * 4   ),  # RL, RR, FL, FR
        ('suspensionAcceleration' , ctypes.c_float * 4   ),  # RL, RR, FL, FR
        ('wheelSpeed'             , ctypes.c_float * 4   ),  # Speed of each wheel
        ('wheelSlip'              , ctypes.c_float * 4   ),  # Slip ratio for each wheel
        ('localVelocityX'         , ctypes.c_float       ),  # Velocity in local space
        ('localVelocityY'         , ctypes.c_float       ),  # Velocity in local space
        ('localVelocityZ'         , ctypes.c_float       ),  # Velocity in local space
        ('angularVelocityX'       , ctypes.c_float       ),  # Angular velocity x-component
        ('angularVelocityY'       , ctypes.c_float       ),  # Angular velocity y-component
        ('angularVelocityZ'       , ctypes.c_float       ),  # Angular velocity z-component
        ('angularAccelerationX'   , ctypes.c_float       ),  # Angular acceleration x-component
        ('angularAccelerationY'   , ctypes.c_float       ),  # Angular acceleration y-component
        ('angularAccelerationZ'   , ctypes.c_float       ),  # Angular acceleration z-component
        ('frontWheelsAngle'       , ctypes.c_float       )   # Current front wheels angle in radians
    ]

##########################################################
#                                                        #
#  __________  Packet ID 1 : SESSION PACKET  __________  #
#                                                        #
##########################################################

class MarshalZone_V1(PackedLittleEndianStructure):
    """This type is used for the 21-element 'marshalZones' array of the PacketSessionData_V1 type, defined below."""
    _fields_ = [
        ('zoneStart' , ctypes.c_float),  # Fraction (0..1) of way through the lap the marshal zone starts
        ('zoneFlag'  , ctypes.c_int8 )   # -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow, 4 = red
    ]


class PacketSessionData_V1(PackedLittleEndianStructure):
    """The session packet includes details about the current session in progress.

    Frequency: 2 per second
    Size: 149 bytes
    Version: 1
    """
    _fields_ = [
        ('header'              , PacketHeader       ),  # Header
        ('weather'             , ctypes.c_uint8     ),  # Weather - 0 = clear, 1 = light cloud, 2 = overcast
                                                        # 3 = light rain, 4 = heavy rain, 5 = storm
        ('trackTemperature'    , ctypes.c_int8      ),  # Track temp. in degrees celsius
        ('airTemperature'      , ctypes.c_int8      ),  # Air temp. in degrees celsius
        ('totalLaps'           , ctypes.c_uint8     ),  # Total number of laps in this race
        ('trackLength'         , ctypes.c_uint16    ),  # Track length in metres
        ('sessionType'         , ctypes.c_uint8     ),  # 0 = unknown, 1 = P1, 2 = P2, 3 = P3, 4 = Short P
                                                        # 5 = Q1, 6 = Q2, 7 = Q3, 8 = Short Q, 9 = OSQ
                                                        # 10 = R, 11 = R2, 12 = Time Trial
        ('trackId'             , ctypes.c_int8      ),  # -1 for unknown, 0-21 for tracks, see appendix
        ('m_formula'           , ctypes.c_uint8     ),  # Formula, 0 = F1 Modern, 1 = F1 Classic, 2 = F2,
                                                        # 3 = F1 Generic
        ('sessionTimeLeft'     , ctypes.c_uint16    ),  # Time left in session in seconds
        ('sessionDuration'     , ctypes.c_uint16    ),  # Session duration in seconds
        ('pitSpeedLimit'       , ctypes.c_uint8     ),  # Pit speed limit in kilometres per hour
        ('gamePaused'          , ctypes.c_uint8     ),  # Whether the game is paused
        ('isSpectating'        , ctypes.c_uint8     ),  # Whether the player is spectating
        ('spectatorCarIndex'   , ctypes.c_uint8     ),  # Index of the car being spectated
        ('sliProNativeSupport' , ctypes.c_uint8     ),  # SLI Pro support, 0 = inactive, 1 = active
        ('numMarshalZones'     , ctypes.c_uint8     ),  # Number of marshal zones to follow
        ('marshalZones'        , MarshalZone_V1 * 21),  # List of marshal zones – max 21
        ('safetyCarStatus'     , ctypes.c_uint8     ),  # 0 = no safety car, 1 = full safety car
                                                        # 2 = virtual safety car
        ('networkGame'         , ctypes.c_uint8     )   # 0 = offline, 1 = online
    ]

###########################################################
#                                                         #
#  __________  Packet ID 2 : LAP DATA PACKET  __________  #
#                                                         #
###########################################################

class LapData_V1(PackedLittleEndianStructure):
    """This type is used for the 20-element 'lapData' array of the PacketLapData_V1 type, defined below."""
    _fields_ = [

        ('lastLapTime'       , ctypes.c_float),  # Last lap time in seconds
        ('currentLapTime'    , ctypes.c_float),  # Current time around the lap in seconds
        ('bestLapTime'       , ctypes.c_float),  # Best lap time of the session in seconds
        ('sector1Time'       , ctypes.c_float),  # Sector 1 time in seconds
        ('sector2Time'       , ctypes.c_float),  # Sector 2 time in seconds
        ('lapDistance'       , ctypes.c_float),  # Distance vehicle is around current lap in metres – could
                                                 # be negative if line hasn’t been crossed yet
        ('totalDistance'     , ctypes.c_float),  # Total distance travelled in session in metres – could
                                                 # be negative if line hasn’t been crossed yet
        ('safetyCarDelta'    , ctypes.c_float),  # Delta in seconds for safety car
        ('carPosition'       , ctypes.c_uint8),  # Car race position
        ('currentLapNum'     , ctypes.c_uint8),  # Current lap number
        ('pitStatus'         , ctypes.c_uint8),  # 0 = none, 1 = pitting, 2 = in pit area
        ('sector'            , ctypes.c_uint8),  # 0 = sector1, 1 = sector2, 2 = sector3
        ('currentLapInvalid' , ctypes.c_uint8),  # Current lap invalid - 0 = valid, 1 = invalid
        ('penalties'         , ctypes.c_uint8),  # Accumulated time penalties in seconds to be added
        ('gridPosition'      , ctypes.c_uint8),  # Grid position the vehicle started the race in
        ('driverStatus'      , ctypes.c_uint8),  # Status of driver - 0 = in garage, 1 = flying lap
                                                 # 2 = in lap, 3 = out lap, 4 = on track
        ('resultStatus'      , ctypes.c_uint8)   # Result status - 0 = invalid, 1 = inactive, 2 = active
                                                 # 3 = finished, 4 = disqualified, 5 = not classified
                                                 # 6 = retired
    ]


class PacketLapData_V1(PackedLittleEndianStructure):
    """The lap data packet gives details of all the cars in the session.

    Frequency: Rate as specified in menus
    Size: 843 bytes
    Version: 1
    """
    _fields_ = [
        ('header'  , PacketHeader   ),  # Header
        ('lapData' , LapData_V1 * 20)   # Lap data for all cars on track
    ]

########################################################
#                                                      #
#  __________  Packet ID 3 : EVENT PACKET  __________  #
#                                                      #
########################################################

class PacketEventData_V1(PackedLittleEndianStructure):
    """This packet gives details of events that happen during the course of a session.

    Frequency: When the event occurs
    Size: 32 bytes
    Version: 1
    """
    _fields_ = [
        ('header'          , PacketHeader     ),  # Header
        ('eventStringCode' , ctypes.c_char * 4),  # Event string code, see below
        # Event details - should be interpreted differently for each type
        ('vehicleIdx'      , ctypes.c_uint8   ),  # Vehicle index of car (valid for events: FTLP, RTMT, TMPT, RCWN)
        ('lapTime'         , ctypes.c_float   )   # Lap time is in seconds (valid for events: FTLP)
    ]


@enum.unique
class EventStringCode(enum.Enum):
    """Value as specified in the PacketEventData_V1.eventStringCode header field, used to distinguish packet types."""
    SSTA = b'SSTA'
    SEND = b'SEND'
    FTLP = b'FTLP'
    RTMT = b'RTMT'
    DRSE = b'DRSE'
    DRSD = b'DRSD'
    TMPT = b'TMPT'
    CHQF = b'CHQF'
    RCWN = b'RCWN'


EventStringCode.short_description = {
    EventStringCode.SSTA : 'Session Started',
    EventStringCode.SEND : 'Session Ended',
    EventStringCode.FTLP : 'Fastest Lap',
    EventStringCode.RTMT : 'Retirement',
    EventStringCode.DRSE : 'DRS enabled',
    EventStringCode.DRSD : 'DRS disabled',
    EventStringCode.TMPT : 'Team mate in pits',
    EventStringCode.CHQF : 'Chequered flag',
    EventStringCode.RCWN : 'Race Winner'
}


EventStringCode.long_description = {
    EventStringCode.SSTA : 'Sent when the session starts',
    EventStringCode.SEND : 'Sent when the session ends',
    EventStringCode.FTLP : 'When a driver achieves the fastest lap',
    EventStringCode.RTMT : 'When a driver retires',
    EventStringCode.DRSE : 'Race control have enabled DRS',
    EventStringCode.DRSD : 'Race control have disabled DRS',
    EventStringCode.TMPT : 'Your team mate has entered the pits',
    EventStringCode.CHQF : 'The chequered flag has been waved',
    EventStringCode.RCWN : 'The race winner is announced'
}

###############################################################
#                                                             #
#  __________  Packet ID 4 : PARTICIPANTS PACKET  __________  #
#                                                             #
###############################################################

class ParticipantData_V1(PackedLittleEndianStructure):
    """This type is used for the 20-element 'participants' array of the PacketParticipantsData_V1 type, defined below."""
    _fields_ = [
        ('aiControlled' , ctypes.c_uint8    ),  # Whether the vehicle is AI (1) or Human (0) controlled
        ('driverId'     , ctypes.c_uint8    ),  # Driver id - see appendix
        ('teamId'       , ctypes.c_uint8    ),  # Team id - see appendix
        ('raceNumber'   , ctypes.c_uint8    ),  # Race number of the car
        ('nationality'  , ctypes.c_uint8    ),  # Nationality of the driver
        ('name'         , ctypes.c_char * 48),  # Name of participant in UTF-8 format – null terminated
                                                # Will be truncated with … (U+2026) if too long
        ('yourTelemetry', ctypes.c_uint8    )   # The player's UDP setting, 0 = restricted, 1 = public
    ]


class PacketParticipantsData_V1(PackedLittleEndianStructure):
    """This is a list of participants in the race.

    If the vehicle is controlled by AI, then the name will be the driver name.
    If this is a multiplayer game, the names will be the Steam Id on PC, or the LAN name if appropriate.
    On Xbox One, the names will always be the driver name, on PS4 the name will be the LAN name if playing a LAN game,
    otherwise it will be the driver name.

    Frequency: Every 5 seconds
    Size: 1104 bytes
    Version: 1
    """
    _fields_ = [
        ('header'        , PacketHeader           ),  # Header
        ('numActiveCars' , ctypes.c_uint8         ),  # Number of active cars in the data – should match number of
                                                      # cars on HUD
        ('participants'  , ParticipantData_V1 * 20)
    ]

#############################################################
#                                                           #
#  __________  Packet ID 5 : CAR SETUPS PACKET  __________  #
#                                                           #
#############################################################

class CarSetupData_V1(PackedLittleEndianStructure):
    """This type is used for the 20-element 'carSetups' array of the PacketCarSetupData_V1 type, defined below."""
    _fields_ = [
        ('frontWing'             , ctypes.c_uint8),  # Front wing aero
        ('rearWing'              , ctypes.c_uint8),  # Rear wing aero
        ('onThrottle'            , ctypes.c_uint8),  # Differential adjustment on throttle (percentage)
        ('offThrottle'           , ctypes.c_uint8),  # Differential adjustment off throttle (percentage)
        ('frontCamber'           , ctypes.c_float),  # Front camber angle (suspension geometry)
        ('rearCamber'            , ctypes.c_float),  # Rear camber angle (suspension geometry)
        ('frontToe'              , ctypes.c_float),  # Front toe angle (suspension geometry)
        ('rearToe'               , ctypes.c_float),  # Rear toe angle (suspension geometry)
        ('frontSuspension'       , ctypes.c_uint8),  # Front suspension
        ('rearSuspension'        , ctypes.c_uint8),  # Rear suspension
        ('frontAntiRollBar'      , ctypes.c_uint8),  # Front anti-roll bar
        ('rearAntiRollBar'       , ctypes.c_uint8),  # Rear anti-roll bar
        ('frontSuspensionHeight' , ctypes.c_uint8),  # Front ride height
        ('rearSuspensionHeight'  , ctypes.c_uint8),  # Rear ride height
        ('brakePressure'         , ctypes.c_uint8),  # Brake pressure (percentage)
        ('brakeBias'             , ctypes.c_uint8),  # Brake bias (percentage)
        ('frontTyrePressure'     , ctypes.c_float),  # Front tyre pressure (PSI)
        ('rearTyrePressure'      , ctypes.c_float),  # Rear tyre pressure (PSI)
        ('ballast'               , ctypes.c_uint8),  # Ballast
        ('fuelLoad'              , ctypes.c_float)   # Fuel load
    ]


class PacketCarSetupData_V1(PackedLittleEndianStructure):
    """This packet details the car setups for each vehicle in the session.

    Note that in multiplayer games, other player cars will appear as blank, you will only be able to see your car setup and AI cars.

    Frequency: 2 per second
    Size: 843 bytes
    Version: 1
    """
    _fields_ = [
        ('header'    , PacketHeader        ),  # Header
        ('carSetups' , CarSetupData_V1 * 20)
    ]

################################################################
#                                                              #
#  __________  Packet ID 6 : CAR TELEMETRY PACKET  __________  #
#                                                              #
################################################################

class CarTelemetryData_V1(PackedLittleEndianStructure):
    """This type is used for the 20-element 'carTelemetryData' array of the PacketCarTelemetryData_V1 type, defined below."""
    _fields_ = [
        ('speed'                   , ctypes.c_uint16    ),  # Speed of car in kilometres per hour
        ('throttle'                , ctypes.c_float     ),  # Amount of throttle applied (0.0 to 1.0)
        ('steer'                   , ctypes.c_float     ),  # Steering (-1.0 (full lock left) to 1.0 (full lock right))
        ('brake'                   , ctypes.c_float     ),  # Amount of brake applied (0 to 1.0)
        ('clutch'                  , ctypes.c_uint8     ),  # Amount of clutch applied (0 to 100)
        ('gear'                    , ctypes.c_int8      ),  # Gear selected (1-8, N=0, R=-1)
        ('engineRPM'               , ctypes.c_uint16    ),  # Engine RPM
        ('drs'                     , ctypes.c_uint8     ),  # 0 = off, 1 = on
        ('revLightsPercent'        , ctypes.c_uint8     ),  # Rev lights indicator (percentage)
        ('brakesTemperature'       , ctypes.c_uint16 * 4),  # Brakes temperature (celsius)
        ('tyresSurfaceTemperature' , ctypes.c_uint16 * 4),  # Tyres surface temperature (celsius)
        ('tyresInnerTemperature'   , ctypes.c_uint16 * 4),  # Tyres inner temperature (celsius)
        ('engineTemperature'       , ctypes.c_uint16    ),  # Engine temperature (celsius)
        ('tyresPressure'           , ctypes.c_float  * 4),  # Tyres pressure (PSI)
        ('surfaceType'             , ctypes.c_uint8  * 4)   # Driving surface, see appendices
    ]


class PacketCarTelemetryData_V1(PackedLittleEndianStructure):
    """This packet details telemetry for all the cars in the race.

    It details various values that would be recorded on the car such as speed, throttle application, DRS etc.

    Frequency: Rate as specified in menus
    Size: 1347 bytes
    Version: 1
    """
    _fields_ = [
        ('header'           , PacketHeader            ),  # Header
        ('carTelemetryData' , CarTelemetryData_V1 * 20),
        ('buttonStatus'     , ctypes.c_uint32         )   # Bit flags specifying which buttons are being
                                                          # pressed currently - see appendices
    ]

#############################################################
#                                                           #
#  __________  Packet ID 7 : CAR STATUS PACKET  __________  #
#                                                           #
#############################################################

class CarStatusData_V1(PackedLittleEndianStructure):
    """This type is used for the 20-element 'carStatusData' array of the PacketCarStatusData_V1 type, defined below.

    There is some data in the Car Status packets that you may not want other players seeing if you are in a multiplayer game.
    This is controlled by the "Your Telemetry" setting in the Telemetry options. The options are:

        Restricted (Default) – other players viewing the UDP data will not see values for your car;
        Public – all other players can see all the data for your car.

    Note: You can always see the data for the car you are driving regardless of the setting.

    The following data items are set to zero if the player driving the car in question has their "Your Telemetry" set to "Restricted":

        fuelInTank
        fuelCapacity
        fuelMix
        fuelRemainingLaps
        frontBrakeBias
        frontLeftWingDamage
        frontRightWingDamage
        rearWingDamage
        engineDamage
        gearBoxDamage
        tyresWear (All four wheels)
        tyresDamage (All four wheels)
        ersDeployMode
        ersStoreEnergy
        ersDeployedThisLap
        ersHarvestedThisLapMGUK
        ersHarvestedThisLapMGUH
    """
    _fields_ = [
        ('tractionControl'         , ctypes.c_uint8    ),  # 0 (off) - 2 (high)
        ('antiLockBrakes'          , ctypes.c_uint8    ),  # 0 (off) - 1 (on)
        ('fuelMix'                 , ctypes.c_uint8    ),  # Fuel mix - 0 = lean, 1 = standard, 2 = rich, 3 = max
        ('frontBrakeBias'          , ctypes.c_uint8    ),  # Front brake bias (percentage)
        ('pitLimiterStatus'        , ctypes.c_uint8    ),  # Pit limiter status - 0 = off, 1 = on
        ('fuelInTank'              , ctypes.c_float    ),  # Current fuel mass
        ('fuelCapacity'            , ctypes.c_float    ),  # Fuel capacity
        ('fuelRemainingLaps'       , ctypes.c_float    ),  # Fuel remaining in terms of laps (value on MFD)
        ('maxRPM'                  , ctypes.c_uint16   ),  # Cars max RPM, point of rev limiter
        ('idleRPM'                 , ctypes.c_uint16   ),  # Cars idle RPM
        ('maxGears'                , ctypes.c_uint8    ),  # Maximum number of gears
        ('drsAllowed'              , ctypes.c_uint8    ),  # 0 = not allowed, 1 = allowed, -1 = unknown
        ('tyresWear'               , ctypes.c_uint8 * 4),  # Tyre wear percentage
        ('actualTyreCompound'      , ctypes.c_uint8    ),  # F1 Modern - 16 = C5, 17 = C4, 18 = C3, 19 = C2, 20 = C1
                                                           # 7 = inter, 8 = wet
                                                           # F1 Classic - 9 = dry, 10 = wet
                                                           # F2 – 11 = super soft, 12 = soft, 13 = medium, 14 = hard
                                                           # 15 = wet
        ('tyreVisualCompound'      , ctypes.c_uint8    ),  # F1 visual (can be different from actual compound)
                                                           # 16 = soft, 17 = medium, 18 = hard, 7 = inter, 8 = wet
                                                           # F1 Classic – same as above
                                                           # F2 – same as above
        ('tyresDamage'             , ctypes.c_uint8 * 4),  # Tyre damage (percentage)
        ('frontLeftWingDamage'     , ctypes.c_uint8    ),  # Front left wing damage (percentage)
        ('frontRightWingDamage'    , ctypes.c_uint8    ),  # Front right wing damage (percentage)
        ('rearWingDamage'          , ctypes.c_uint8    ),  # Rear wing damage (percentage)
        ('engineDamage'            , ctypes.c_uint8    ),  # Engine damage (percentage)
        ('gearBoxDamage'           , ctypes.c_uint8    ),  # Gear box damage (percentage)
        ('vehicleFiaFlags'         , ctypes.c_int8     ),  # -1 = invalid/unknown, 0 = none, 1 = green
                                                           # 2 = blue, 3 = yellow, 4 = red
        ('ersStoreEnergy'          , ctypes.c_float    ),  # ERS energy store in Joules
        ('ersDeployMode'           , ctypes.c_uint8    ),  # ERS deployment mode, 0 = none, 1 = low, 2 = medium
                                                           # 3 = high, 4 = overtake, 5 = hotlap
        ('ersHarvestedThisLapMGUK' , ctypes.c_float    ),  # ERS energy harvested this lap by MGU-K
        ('ersHarvestedThisLapMGUH' , ctypes.c_float    ),  # ERS energy harvested this lap by MGU-H
        ('ersDeployedThisLap'      , ctypes.c_float    )   # ERS energy deployed this lap
    ]


class PacketCarStatusData_V1(PackedLittleEndianStructure):
    """This packet details car statuses for all the cars in the race.

    It includes values such as the damage readings on the car.

    Frequency: Rate as specified in menus
    Size: 1143 bytes
    Version: 1
    """
    _fields_ = [
        ('header'        , PacketHeader         ),  # Header
        ('carStatusData' , CarStatusData_V1 * 20)
    ]

###################################################################
#                                                                 #
#  Appendices: various value enumerations used in the UDP output  #
#                                                                 #
###################################################################

TeamIDs = {
     0 : 'Mercedes',
     1 : 'Ferrari',
     2 : 'Red Bull Racing',
     3 : 'Williams',
     4 : 'Racing Point',
     5 : 'Renault',
     6 : 'Toro Rosso',
     7 : 'Haas',
     8 : 'McLaren',
     9 : 'Alfa Romeo',
    10 : 'McLaren 1988',
    11 : 'McLaren 1991',
    12 : 'Williams 1992',
    13 : 'Ferrari 1995',
    14 : 'Williams 1996',
    15 : 'McLaren 1998',
    16 : 'Ferrari 2002',
    17 : 'Ferrari 2004',
    18 : 'Renault 2006',
    19 : 'Ferrari 2007',
    21 : 'Red Bull 2010',
    22 : 'Ferrari 1976',
    23 : 'ART Grand Prix',
    24 : 'Campos Vexatec Racing',
    25 : 'Carlin',
    26 : 'Charouz Racing System',
    27 : 'DAMS',
    28 : 'Russian Time',
    29 : 'MP Motorsport',
    30 : 'Pertamina',
    31 : 'McLaren 1990',
    32 : 'Trident',
    33 : 'BWT Arden',
    34 : 'McLaren 1976',
    35 : 'Lotus 1972',
    36 : 'Ferrari 1979',
    37 : 'McLaren 1982',
    38 : 'Williams 2003',
    39 : 'Brawn 2009',
    40 : 'Lotus 1978',
    63 : 'Ferrari 1990',
    64 : 'McLaren 2010',
    65 : 'Ferrari 2010'
}


DriverIDs = {
     0 : 'Carlos Sainz',
     1 : 'Daniil Kvyat',
     2 : 'Daniel Ricciardo',
     6 : 'Kimi Räikkönen',
     7 : 'Lewis Hamilton',
     9 : 'Max Verstappen',
    10 : 'Nico Hulkenberg',
    11 : 'Kevin Magnussen',
    12 : 'Romain Grosjean',
    13 : 'Sebastian Vettel',
    14 : 'Sergio Perez',
    15 : 'Valtteri Bottas',
    19 : 'Lance Stroll',
    20 : 'Arron Barnes',
    21 : 'Martin Giles',
    22 : 'Alex Murray',
    23 : 'Lucas Roth',
    24 : 'Igor Correia',
    25 : 'Sophie Levasseur',
    26 : 'Jonas Schiffer',
    27 : 'Alain Forest',
    28 : 'Jay Letourneau',
    29 : 'Esto Saari',
    30 : 'Yasar Atiyeh',
    31 : 'Callisto Calabresi',
    32 : 'Naota Izum',
    33 : 'Howard Clarke',
    34 : 'Wilhelm Kaufmann',
    35 : 'Marie Laursen',
    36 : 'Flavio Nieves',
    37 : 'Peter Belousov',
    38 : 'Klimek Michalski',
    39 : 'Santiago Moreno',
    40 : 'Benjamin Coppens',
    41 : 'Noah Visser',
    42 : 'Gert Waldmuller',
    43 : 'Julian Quesada',
    44 : 'Daniel Jones',
    45 : 'Artem Markelov',
    46 : 'Tadasuke Makino',
    47 : 'Sean Gelael',
    48 : 'Nyck De Vries',
    49 : 'Jack Aitken',
    50 : 'George Russell',
    51 : 'Maximilian Günther',
    52 : 'Nirei Fukuzumi',
    53 : 'Luca Ghiotto',
    54 : 'Lando Norris',
    55 : 'Sérgio Sette Câmara',
    56 : 'Louis Delétraz',
    57 : 'Antonio Fuoco',
    58 : 'Charles Leclerc',
    59 : 'Pierre Gasly',
    62 : 'Alexander Albon',
    63 : 'Nicholas Latifi',
    64 : 'Dorian Boccolacci',
    65 : 'Niko Kari',
    66 : 'Roberto Merhi',
    67 : 'Arjun Maini',
    68 : 'Alessio Lorandi',
    69 : 'Ruben Meijer',
    70 : 'Rashid Nair',
    71 : 'Jack Tremblay',
    74 : 'Antonio Giovinazzi',
    75 : 'Robert Kubica'
}


TrackIDs = {
     0 : 'Melbourne',
     1 : 'Paul Ricard',
     2 : 'Shanghai',
     3 : 'Sakhir (Bahrain)',
     4 : 'Catalunya',
     5 : 'Monaco',
     6 : 'Montreal',
     7 : 'Silverstone',
     8 : 'Hockenheim',
     9 : 'Hungaroring',
    10 : 'Spa',
    11 : 'Monza',
    12 : 'Singapore',
    13 : 'Suzuka',
    14 : 'Abu Dhabi',
    15 : 'Texas',
    16 : 'Brazil',
    17 : 'Austria',
    18 : 'Sochi',
    19 : 'Mexico',
    20 : 'Baku (Azerbaijan)',
    21 : 'Sakhir Short',
    22 : 'Silverstone Short',
    23 : 'Texas Short',
    24 : 'Suzuka Short'
}


NationalityIDs = {
     1 : 'American',
     2 : 'Argentinian',
     3 : 'Australian',
     4 : 'Austrian',
     5 : 'Azerbaijani',
     6 : 'Bahraini',
     7 : 'Belgian',
     8 : 'Bolivian',
     9 : 'Brazilian',
    10 : 'British',
    11 : 'Bulgarian',
    12 : 'Cameroonian',
    13 : 'Canadian',
    14 : 'Chilean',
    15 : 'Chinese',
    16 : 'Colombian',
    17 : 'Costa Rican',
    18 : 'Croatian',
    19 : 'Cypriot',
    20 : 'Czech',
    21 : 'Danish',
    22 : 'Dutch',
    23 : 'Ecuadorian',
    24 : 'English',
    25 : 'Emirian',
    26 : 'Estonian',
    27 : 'Finnish',
    28 : 'French',
    29 : 'German',
    30 : 'Ghanaian',
    31 : 'Greek',
    32 : 'Guatemalan',
    33 : 'Honduran',
    34 : 'Hong Konger',
    35 : 'Hungarian',
    36 : 'Icelander',
    37 : 'Indian',
    38 : 'Indonesian',
    39 : 'Irish',
    40 : 'Israeli',
    41 : 'Italian',
    42 : 'Jamaican',
    43 : 'Japanese',
    44 : 'Jordanian',
    45 : 'Kuwaiti',
    46 : 'Latvian',
    47 : 'Lebanese',
    48 : 'Lithuanian',
    49 : 'Luxembourger',
    50 : 'Malaysian',
    51 : 'Maltese',
    52 : 'Mexican',
    53 : 'Monegasque',
    54 : 'New Zealander',
    55 : 'Nicaraguan',
    56 : 'North Korean',
    57 : 'Northern Irish',
    58 : 'Norwegian',
    59 : 'Omani',
    60 : 'Pakistani',
    61 : 'Panamanian',
    62 : 'Paraguayan',
    63 : 'Peruvian',
    64 : 'Polish',
    65 : 'Portuguese',
    66 : 'Qatari',
    67 : 'Romanian',
    68 : 'Russian',
    69 : 'Salvadoran',
    70 : 'Saudi',
    71 : 'Scottish',
    72 : 'Serbian',
    73 : 'Singaporean',
    74 : 'Slovakian',
    75 : 'Slovenian',
    76 : 'South Korean',
    77 : 'South African',
    78 : 'Spanish',
    79 : 'Swedish',
    80 : 'Swiss',
    81 : 'Thai',
    82 : 'Turkish',
    83 : 'Uruguayan',
    84 : 'Ukrainian',
    85 : 'Venezuelan',
    86 : 'Welsh'
}


# These surface types are from physics data and show what type of contact each wheel is experiencing.
SurfaceTypes = {
     0 : 'Tarmac',
     1 : 'Rumble strip',
     2 : 'Concrete',
     3 : 'Rock',
     4 : 'Gravel',
     5 : 'Mud',
     6 : 'Sand',
     7 : 'Grass',
     8 : 'Water',
     9 : 'Cobblestone',
    10 : 'Metal',
    11 : 'Ridged'
}


@enum.unique
class ButtonFlag(enum.IntEnum):
    """Bit-mask values for the 'button' field in Car Telemetry Data packets."""
    CROSS             = 0x0001
    TRIANGLE          = 0x0002
    CIRCLE            = 0x0004
    SQUARE            = 0x0008
    D_PAD_LEFT        = 0x0010
    D_PAD_RIGHT       = 0x0020
    D_PAD_UP          = 0x0040
    D_PAD_DOWN        = 0x0080
    OPTIONS           = 0x0100
    L1                = 0x0200
    R1                = 0x0400
    L2                = 0x0800
    R2                = 0x1000
    LEFT_STICK_CLICK  = 0x2000
    RIGHT_STICK_CLICK = 0x4000


ButtonFlag.description = {
    ButtonFlag.CROSS             : "Cross or A",
    ButtonFlag.TRIANGLE          : "Triangle or Y",
    ButtonFlag.CIRCLE            : "Circle or B",
    ButtonFlag.SQUARE            : "Square or X",
    ButtonFlag.D_PAD_LEFT        : "D-pad Left",
    ButtonFlag.D_PAD_RIGHT       : "D-pad Right",
    ButtonFlag.D_PAD_UP          : "D-pad Up",
    ButtonFlag.D_PAD_DOWN        : "D-pad Down",
    ButtonFlag.OPTIONS           : "Options or Menu",
    ButtonFlag.L1                : "L1 or LB",
    ButtonFlag.R1                : "R1 or RB",
    ButtonFlag.L2                : "L2 or LT",
    ButtonFlag.R2                : "R2 or RT",
    ButtonFlag.LEFT_STICK_CLICK  : "Left Stick Click",
    ButtonFlag.RIGHT_STICK_CLICK : "Right Stick Click"
}

##################################
#                                #
#  Decode UDP telemetry packets  #
#                                #
##################################

# Map from (packetFormat, packetVersion, packetId) to a specific packet type.
HeaderFieldsToPacketType = {
    (2019, 1, 0) : PacketMotionData_V1,
    (2019, 1, 1) : PacketSessionData_V1,
    (2019, 1, 2) : PacketLapData_V1,
    (2019, 1, 3) : PacketEventData_V1,
    (2019, 1, 4) : PacketParticipantsData_V1,
    (2019, 1, 5) : PacketCarSetupData_V1,
    (2019, 1, 6) : PacketCarTelemetryData_V1,
    (2019, 1, 7) : PacketCarStatusData_V1
}

class UnpackError(Exception):
    pass

def unpack_udp_packet(packet: bytes) -> PackedLittleEndianStructure:
    """Convert raw UDP packet to an appropriately-typed telemetry packet.

    Args:
        packet: the contents of the UDP packet to be unpacked.

    Returns:
        The decoded packet structure.

    Raises:
        UnpackError if a problem is detected.
    """
    actual_packet_size = len(packet)

    header_size = ctypes.sizeof(PacketHeader)

    if actual_packet_size < header_size:
        raise UnpackError("Bad telemetry packet: too short ({} bytes).".format(actual_packet_size))

    header = PacketHeader.from_buffer_copy(packet)
    key = (header.packetFormat, header.packetVersion, header.packetId)

    if key not in HeaderFieldsToPacketType:
        raise UnpackError("Bad telemetry packet: no match for key fields {!r}.".format(key))

    packet_type = HeaderFieldsToPacketType[key]

    expected_packet_size = ctypes.sizeof(packet_type)

    if actual_packet_size != expected_packet_size:
        raise UnpackError("Bad telemetry packet: bad size for {} packet; expected {} bytes but received {} bytes.".format(
            packet_type.__name__, expected_packet_size, actual_packet_size))

    return packet_type.from_buffer_copy(packet)

#########################################################################
#                                                                       #
#  Verify packet sizes if this module is executed rather than imported  #
#                                                                       #
#########################################################################

if __name__ == "__main__":

    # Check all the packet sizes.

    assert ctypes.sizeof(PacketMotionData_V1)       == 1343
    assert ctypes.sizeof(PacketSessionData_V1)      ==  149
    assert ctypes.sizeof(PacketLapData_V1)          ==  843
    assert ctypes.sizeof(PacketEventData_V1)        ==   32
    assert ctypes.sizeof(PacketParticipantsData_V1) == 1104
    assert ctypes.sizeof(PacketCarSetupData_V1)     ==  843
    assert ctypes.sizeof(PacketCarTelemetryData_V1) == 1347
    assert ctypes.sizeof(PacketCarStatusData_V1)    == 1143
