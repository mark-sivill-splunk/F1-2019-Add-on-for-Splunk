# F1-2019-Add-on-for-Splunk
Capture telemetry data from the Codemasters F1 2019 game and send it to Splunk. The add-on takes the binary telemetry data generated from the Formula 1 game which is sent over UDP and then converts to JSON for Splunk ingestion.  The add-on has been tested successfully with the Playstation, Xbox and PC versions of the F1 2019 game.  The add-on has also been tested successfully using a Playstation with Codemasters F1 2020 game when telemetry mode is set to F1 2019

Splunk Setup
============

After the add-on has been installed into Splunk and restarted, configure a data input through either of the following

* from "F1 2019 Add-on for Splunk" app then "Inputs" tab
* from Splunk main menu "Settings" then "Data inputs"

Set the following values for the data input

* Name of data input
* UDP Port Number which by default is 20777 (same default as F1 2019 game)
* Interval to a number (number is ignored by add-on)
* Index for location of F1 data within Splunk

Note the IP address of the machine where the add-on is located. The IP address needs to be reached from the machine where the F1 2019 game is run from. The IP address of the machine may have a different internal IP address compared to the IP address that the machine can be reached on externally.

While a data input can receive data from multiple gaming rigs at the same time, there will be a point when the UDP packets will over whelm the single UDP port configured by the add-on. For multiple gaming rig set ups the preference should be for multiple data inputs with associated unique UDP port numbers.

F1 2019 Game Setup
==================

To send telemetry from the F1 2019 game to the add-on goto "Game Options" then "Settings" then "Telemetry Settings", then set

* UDP Telemetry to On
* Broadcast Mode to Off
* UDP IP Address to the IP address where the add-on is located
* Port to same number used in add-on for "UDP Port Number" (default value is 20777)
* UDP Send Rate to 10Hz
* UDP Format to 2019 which is the default value

Message Description
===================

The F1 2019 JSON messages created within Splunk are based on [f1-2019-telemetry packets.py version 1.1.4](https://gitlab.com/reddish/f1-2019-telemetry/-/blob/master/f1_2019_telemetry/packets.py) which in turn is based on [Codemasters F1 2019 UDP Specification](https://forums.codemasters.com/topic/44592-f1-2019-udp-specification/)

JSON messages are created in the "F1 2019" format.

A single player will generate about 400KB of data per second ( at about 45 events per second ) when racing and telemetry is set to 10Hz.

Troubleshooting
===============

From within Splunk the status of the add-on can be examined if access to the _internal index is available using the following SPL -

`index=_internal "[f1_2019_addon]"`

Also if the add-on is working but not receiving data, please check that UDP data can be sent to the machine and port created within "Data inputs". For example running the following bash command line from the same machine where the add-on is installed will send a badly formed UDP message to the add-on -

`echo -n "test" `>`/dev/udp/localhost/20777`

The badly formed UDP message can be found within Splunk using the following SPL -

`index=_internal "[f1_2019_addon]"`

Within the returned results an event similar to below should be seen if the badly formed UDP message arrived successfully in Splunk -

`Error unpacking UDP packet - Bad telemetry packet: too short (4 bytes)`

The bash command line can be used to send a badly formed UDP message to remote machines and different ports, for example to send to remote machine `example.com` on port `20778` use -

`echo -n "test" `>`/dev/udp/example.com/20778`

Viewing F1 2019 data
====================

The [F1 2019 App for Splunk](https://splunkbase.splunk.com/app/4915/) is a minimal app that contains lookup tables and pre-canned dashboards to optionally view data generated from this add-on.

Alternatively use the following SPL to start exploring the data -

`index=* sourcetype=codemasters:f1:2019:*`
