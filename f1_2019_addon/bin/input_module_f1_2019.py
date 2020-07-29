
# encoding = utf-8

import os
import sys
import time
import datetime

'''
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
'''
'''
# For advanced users, if you want to create single instance mod input, uncomment this method.
def use_single_instance_mode():
    return True
'''

from f1_2019_shared import f1_2019_shared


def validate_input(helper, definition):
    
    #
    # check udp port number is valid
    #
    udp_port_number = definition.parameters.get('udp_port_number', None)

    # check is a number
    try:
        _ = int(udp_port_number)
    except:
        raise ValueError(
            "UDP Port Number must be a number, current value is %s" % udp_port_number)

    # check if number is above 0
    if int(udp_port_number) <= 0:
        raise ValueError(
            "UDP Port Number must be above 0, current value is %s" % udp_port_number)

    pass

def collect_events(helper, ew):
    
    #
    # define specfic Splunk functions to pass to a generic f1 class
    #
    def output_event(data, time, host, source, sourcetype):
        event = helper.new_event(
            data=data, time=time, host=host, index=helper.get_output_index(), source=source, sourcetype=sourcetype)
        ew.write_event(event)

    def log_error(text):
        ew.log("ERROR", "[" + helper.get_app_name() + "][" +
               helper.get_input_stanza_names() + "] " + text)

    def log_warn(text):
        ew.log("WARN", "[" + helper.get_app_name() + "][" +
               helper.get_input_stanza_names() + "] " + text)

    def log_info(text):
        ew.log("INFO", "[" + helper.get_app_name() + "][" +
               helper.get_input_stanza_names() + "] " + text)

    def log_debug(text):
        ew.log("DEBUG", "[" + helper.get_app_name() + "][" +
               helper.get_input_stanza_names() + "] " + text)

    # pass functions and variables into shared python module
    f1 = f1_2019_shared(helper.get_arg('udp_port_number'), output_event, log_error, log_warn, log_info, log_debug)

    # start collecting data on port
    f1.collect_data()
