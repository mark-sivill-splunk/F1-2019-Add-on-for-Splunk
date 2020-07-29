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
# use to check for late arriving UDP packages by specific packet type
#

from datetime import datetime
import random

class udp_packet_tracker:

    # class set up
    def __init__(self):

        # lookup used to hold last time a packet received
        self.lookup_dict = {}
        self.counter = 0

        # 2020-4 resuable values
        self.counter_reset = 50000                         # every event increases the counter by one
        self.time_to_live_check_in_seconds = 256           # ttl 255 for UDP messages
        self.flush_dict_count = random.randint(1, (self.counter_reset-1) ) 

    #
    # return true if relative time is late compared to existing relative times
    #
    def is_packet_late(self, key, relative_time):

        # use universal time for people who might be gaming across daylights saving time changes
        current_time = datetime.utcnow()

        #
        # periodically tidy dict
        #
        if self.counter == self.flush_dict_count:
            self.lookup_dict = {key: value for (key, value) in self.lookup_dict.items() if ( current_time - value[1] ).total_seconds() < self.time_to_live_check_in_seconds }
            
        if self.counter == self.counter_reset:
            self.counter = 0

        self.counter = self.counter + 1

        #
        # check value in lookup
        #
        dict_value = self.lookup_dict.get(key)

        if dict_value is None:
            self.lookup_dict[key] = ( relative_time, current_time ) # no value for key so create one
            return False
        elif dict_value[0] < relative_time:
            self.lookup_dict[key] = ( relative_time, current_time ) # newer relative time, so update
            return False
        else:
            return True






