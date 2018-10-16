#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import random
import time
import sys
import iothub_client
from hubmanager.hubmanager import *

from iothub_client import IoTHubModuleClient, IoTHubClientError, IoTHubTransportProvider
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue

# HTTP options
# Because it can poll "after 9 seconds" polls will happen effectively
# at ~10 seconds.
# Note that for scalabilty, the default value of minimumPollingTime
# is 25 minutes. For more information, see:
# https://azure.microsoft.com/documentation/articles/iot-hub-devguide/#messaging
TIMEOUT = 241000
MINIMUM_POLLING_TIME = 9

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubModuleClient.send_event_to_output.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

RECEIVE_CONTEXT = 0
AVG_WIND_SPEED = 10.0
MIN_TEMPERATURE = 20.0
MIN_HUMIDITY = 60.0
MESSAGE_COUNT = 3
RECEIVED_COUNT = 0
TWIN_CONTEXT = 0
METHOD_CONTEXT = 0

# global counters
SEND_CALLBACKS = 0

PROTOCOL = IoTHubTransportProvider.MQTT

MSG_TXT = "{\"iotedge-x64\": \"DevPyTempSensor\",\"windSpeed\": %.2f,\"temperature\": %.2f,\"humidity\": %.2f}"



def main(protocol):
    try:
        print ( "\nPython %s\n" % sys.version )
        print ( "Mridu Pi Test: IoT Hub Client for Python" )

        initialize_client(protocol)

        print ( "Starting the IoT Hub Python sample..."  )

        content = "Mridu Temp Sensor from Python API"

        while True:
            # send a few messages every minute
            print ( "DevPyTempSensor sending %d messages" % MESSAGE_COUNT )

            for message_counter in range(0, MESSAGE_COUNT):
                temperature = MIN_TEMPERATURE + (random.random() * 10)
                humidity = MIN_HUMIDITY + (random.random() * 20)
                msg_txt_formatted = MSG_TXT % (
                    AVG_WIND_SPEED + (random.random() * 4 + 2),
                    temperature,
                    humidity)

                msg_properties = {
                    "temperatureAlert": 'true' if temperature > 28 else 'false'
                }
                send_event_to_output("temperatureOutput", msg_txt_formatted, msg_properties, message_counter)
                print ( "IoTHubModuleClient.send_event_to_output accepted message [%d] for transmission to IoT Hub." % message_counter )

            # Wait for Commands or exit
            print ( "IoTHubModuleClient waiting for commands, press Ctrl-C to exit." )

            status_counter = 0
            while status_counter < 6:
                status = client.get_send_status()
                print ( "Send status: %s" % status )
                time.sleep(10)
                status_counter += 1

    except IoTHubError as iothub_error:
        print ( "Unexpected error %s from IoTHub" % iothub_error )
        return
    except KeyboardInterrupt:
        print ( "IoTHubModuleClient sample stopped" )

if __name__ == '__main__':
    main(PROTOCOL)

