# -*- coding: utf-8 -*-

#
# The MIT License (MIT)
# Copyright (c) 2019 Mark Sivill, Splunk Inc
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

#
# Entry point for collecting F1 2019 game data, by using https://pypi.org/project/f1-2019-telemetry/
# to capture the  data into python classes then using https://github.com/rinatz/ctypes_json to
# convert python classes into JSON
# 


import socket
import platform
import os
import json
import calendar

from datetime import datetime

from packets import unpack_udp_packet

from udp_packet_tracker import udp_packet_tracker


from ctypes import Structure, c_bool, c_int, c_float, c_char,  c_char_p, c_wchar, c_wchar_p
from ctypes_json import CDataJSONEncoder


class f1_2019_shared:

    def __init__(self, udp_port, output_event, log_error, log_warn, log_info, log_debug):

        #
        # logging functions all take a string as an argument
        #
        self.log_error = log_error
        self.log_warn = log_warn
        self.log_info = log_info
        self.log_debug = log_debug

        self.log_info("Starting modular input")

        #
        # output_event is a function which takes the following arguments to write event
        #
        # data - string
        # stanza - string
        # time - string ( in seconds, can use decimals for milli/micro seconds)
        # host - string
        # index - string
        # source - string
        # sourcetype - string
        self.output_event = output_event

        if self.__is_udp_port_valid( udp_port ) == False :
            error_message = "UDP port number must be a number above zero, current value is " + udp_port
            self.log_error(error_message)
            raise ValueError(error_message)

        self.udp_port = str(udp_port)

        # sourcetypes precursor
        pre_sourcetype = "codemasters:f1:2019:"

        # dictionary for looking up sourcetype for given packetId 
        self.packetTypesDict = {
            0: pre_sourcetype + "motion:",
            1: pre_sourcetype + "session:",
            2: pre_sourcetype + "lap:",
            3: pre_sourcetype + "event:",
            4: pre_sourcetype + "participants:",
            5: pre_sourcetype + "car_setups:",
            6: pre_sourcetype + "car_telemetry:",
            7: pre_sourcetype + "car_status:"
        }

        # work out hostname
        self.hostname="unknown"
        try:
            self.hostname = self.__generate_hostname()
        except Exception as e:
            self.log_error("Error generating host on start up - " + str(e))

        self.log_info("Modular input using host " + self.hostname)

        # set up udp packet tracker to monitor late packets
        self.udp_packet_tracker = udp_packet_tracker()
        
    #
    # main function that waits for UDP packets then processes them
    #
    def collect_data(self):

        # bind to udp port
        udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        udp_socket.bind(('', int(self.udp_port) ))
        self.log_info("Modular input now listening on port " + self.udp_port)

        first_collection_received = False

        #
        # keep looping waiting for udp
        #
        while 1:

            # get data and sending IP address from udp
            udp_packet = udp_socket.recvfrom(2048)

            # show if data has been received for first time on this udp port
            if first_collection_received == False:   
                first_collection_received = True
                self.log_info("Modular input received first piece of data")

            # get binary data from udp
            try:
                packet = unpack_udp_packet(udp_packet[0])
            except Exception as e:
                self.log_error("Error unpacking UDP packet - " + str(e))
                continue

            # create source field based on sending IP address ( from udp data ) and port
            try:
                source = ":".join([ udp_packet[1][0], self.udp_port ])
            except Exception as e:
                self.log_error("Error generating source - " + str(e))
                continue

            #
            # check for late packets
            #

            # key to lookup last time information
            late_udp_packet_key = "".join([
                 str(packet.header.packetId),
                 str(packet.header.sessionUID),
                 str(packet.header.packetVersion),
                 source
                 ])

            #
            # process/send data if UDP packet is not late arriving
            #
            if self.udp_packet_tracker.is_packet_late(late_udp_packet_key, packet.header.sessionTime) == False:

                # convert binary object into JSON
                try:
                    data = json.dumps(packet, cls=CDataJSONEncoder)
                except Exception as e:
                    self.log_error("Error converting packet to JSON - " + str(e) + ". Packet - " + packet)
                    continue

                # get modular input local timezone friendly timestamp
                formatted_local_timestamp = datetime.now().strftime("%s.%f")[:-3]

                # create sourcetype based on packedId and packetVersion         
                try:
                    sourcetype = self.__generate_sourcetype(packet.header.packetId,packet.header.packetVersion)
                except Exception as e:
                    self.log_error("Error generating sourcetype - " + str(e))
                    continue

                self.output_event(data, formatted_local_timestamp, self.hostname, source, sourcetype)


        self.log_info("Modular input finished listening on port " + self.udp_port)

    #
    # work out source type using packetId and packetVersion
    # return error sourre type if not found
    #
    def __generate_sourcetype(self,packetId,packetVersion):

        sourcetype_lookup = self.packetTypesDict.get(packetId)

        if sourcetype_lookup is not None:
            return sourcetype_lookup + str(packetVersion)
        else:
            raise ValueError( "Unable to find packetId " + str(packetId) ) 

    #
    # determine the local hostname where the modular input is located
    #
    def __generate_hostname(self):
        
        # choice 1
        socket_fqdn = None
        try:
            socket_fqdn = socket.getfqdn()
            if len(socket_fqdn) == 0:
                socket_fqdn = None    
        except Exception as e:
            self.log_info("Unable to determine hostname using socket.getfqdn " + str(e))
            socket_fqdn = None

        # choice 2
        platform_uname = None
        try:
            platform_uname = platform.uname()[1]    # returns '' is nothing found (network name)
            if len(platform_uname) == 0:
                platform_uname = None    
        except Exception as e:
            self.log_info("Unable to determine hostname using platform.uname " + str(e))
            platform_uname = None            

        # choice 3
        os_uname = None
        try:
            os_uname = os.uname()[1] 
            if len(os_uname) == 0:
                os_uname = None    
        except Exception as e:
            self.log_info("Unable to determine hostname using os.uname " + str(e) )
            os_uname = None     

        # choice 4
        socket_ip_address = None
        try:
            socket_hostname = socket.gethostname()
            socket_ip_address = socket.gethostbyname(socket_hostname)
            if len(socket_ip_address) == 0:
                socket_ip_address = None    
        except Exception as e:
            self.log_info("Unable to determine hostname using socket.gethostname and socket.gethostbyname " + str(e))
            socket_ip_address = None         
        
        self.log_info("Detected hostnames socket_fqdn=%s platform_uname=%s os_uname=%s socket_ip_address=%s" % ( str(socket_fqdn or ''), str(platform_uname or ''), str(os_uname or ''), str(socket_ip_address or '') ) )

        if socket_fqdn is not None:
            return socket_fqdn

        if platform_uname is not None:
            return platform_uname

        if os_uname is not None:
            return os_uname

        if socket_ip_address is not None:
            return socket_ip_address

        return "unknown"

    #
    # check is number and above 0
    #
    def __is_udp_port_valid(self, udp_port):

        # check  is a number
        try:
            _ = int(udp_port)
        except:
            return False

        if int(udp_port) <= 0:
            return False

        return True


