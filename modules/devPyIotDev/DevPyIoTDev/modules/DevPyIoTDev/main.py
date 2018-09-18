# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import random
import time
import sys
import iothub_client
# pylint: disable=E0611
from iothub_client import IoTHubModuleClient, IoTHubClientError, IoTHubTransportProvider
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError
from iothub_client import IoTHubClientRetryPolicy, GetRetryPolicyReturnValue
from simDevice import DeviceClient

# String containing Hostname, Device Id & Device Key in the format:
# "HostName=<host_name>;DeviceId=<device_id>;SharedAccessKey=<device_key>"
CONNECTION_STRING = "HostName=Mridu-IotHub.azure-devices.net;DeviceId=Dev_0;SharedAccessKey=rpdO7rL9wUYHdE8DJFaNhdonH25bsGD6tRPsZZJY6VY="

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubModuleClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000
TIMEOUT = 241000
MINIMUM_POLLING_TIME = 9

# global counters
RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0

RECEIVE_CONTEXT = 0
MESSAGE_COUNT = 5

CONNECTION_STATUS_CONTEXT = 0
TWIN_CONTEXT = 0
SEND_REPORTED_STATE_CONTEXT = 0
METHOD_CONTEXT = 0

# Choose HTTP, AMQP or MQTT as transport protocol.  Currently only MQTT is supported.
PROTOCOL = IoTHubTransportProvider.MQTT

# Callback received when the message that we're forwarding is processed.
def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    print ( "Confirmation[%d] received for message with result = %s" % (user_context, result) )
    map_properties = message.properties()
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    SEND_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % SEND_CALLBACKS )


# receive_message_callback is invoked when an incoming message arrives on the specified 
# input queue (in the case of this sample, "input1").  Because this is a filter module, 
# we will forward this message onto the "output1" queue.
def receive_message_callback(message, hubManager):
    global RECEIVE_CALLBACKS
    message_buffer = message.get_bytearray()
    size = len(message_buffer)
    print ( "    Data: <<<%s>>> & Size=%d" % (message_buffer[:size].decode('utf-8'), size) )
    map_properties = message.properties()
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    RECEIVE_CALLBACKS += 1
    print ( "    Total calls received: %d" % RECEIVE_CALLBACKS )
    hubManager.forward_event_to_output("output1", message, 0)
    return IoTHubMessageDispositionResult.ACCEPTED


def iothub_client_init():
    # prepare iothub client
    dev_client = DeviceClient(CONNECTION_STRING)
    if dev_client.client_protocol == IoTHubTransportProvider.HTTP:
        dev_client.client.set_option("timeout", TIMEOUT)
        dev_client.client.set_option("MinimumPollingTime", MINIMUM_POLLING_TIME)
    # set the time until a message times out
    dev_client.client.set_option("messageTimeout", MESSAGE_TIMEOUT)
    # some embedded platforms need certificate information
    # dev_client.set_certificates(dev_client)
    # to enable MQTT logging set to 1
    if dev_client.client_protocol == IoTHubTransportProvider.MQTT:
        dev_client.client.set_option("logtrace", 0)
        dev_client.client.set_message_callback(
            dev_client.receive_message_callback, RECEIVE_CONTEXT)
    if dev_client.client_protocol == IoTHubTransportProvider.MQTT or dev_client.client_protocol == IoTHubTransportProvider.MQTT_WS:
        dev_client.client.set_device_twin_callback(
            dev_client.device_twin_callback, TWIN_CONTEXT)
        dev_client.client.set_device_method_callback(
            dev_client.device_method_callback, METHOD_CONTEXT)
    if dev_client.client_protocol == IoTHubTransportProvider.AMQP or dev_client.client_protocol == IoTHubTransportProvider.AMQP_WS:
        dev_client.client.set_connection_status_callback(
            dev_client.connection_status_callback, CONNECTION_STATUS_CONTEXT)
    
    retryPolicy = IoTHubClientRetryPolicy.RETRY_INTERVAL
    retryInterval = 100
    dev_client.client.set_retry_policy(retryPolicy, retryInterval)
    print ( "SetRetryPolicy to: retryPolicy = %d" %  retryPolicy)
    print ( "SetRetryPolicy to: retryTimeoutLimitInSeconds = %d" %  retryInterval)
    retryPolicyReturn = dev_client.client.get_retry_policy()
    print ( "GetRetryPolicy returned: retryPolicy = %d" %  retryPolicyReturn.retryPolicy)
    print ( "GetRetryPolicy returned: retryTimeoutLimitInSeconds = %d" %  retryPolicyReturn.retryTimeoutLimitInSeconds)

    return dev_client


class HubManager(object):

    def __init__(
            self,
            protocol=IoTHubTransportProvider.MQTT):
        self.client_protocol = protocol
        self.client = IoTHubModuleClient()
        self.client.create_from_environment(protocol)

        # set the time until a message times out
        self.client.set_option("messageTimeout", MESSAGE_TIMEOUT)
        
        # sets the callback when a message arrives on "input1" queue.  Messages sent to 
        # other inputs or to the default will be silently discarded.
        self.client.set_message_callback("input1", receive_message_callback, self)

    # Forwards the message received onto the next stage in the process.
    def forward_event_to_output(self, outputQueueName, event, send_context):
        self.client.send_event_async(
            outputQueueName, event, send_confirmation_callback, send_context)

def main(protocol):
    try:
        print ( "\nPython %s\n" % sys.version )
        print ( "IoT Hub Client for Python" )

        hub_manager = HubManager(protocol)
        device_client = iothub_client_init()
        print ( "IoTHubClient sending %d messages" % MESSAGE_COUNT )
        message = IoTHubMessage("mridu test message from module!!!!")
        message_counter = 0
        message.message_id = "message_%d" % message_counter
        message.correlation_id = "correlation_%d" % message_counter
        # optional: assign properties
        prop_map = message.properties()
        prop_map.add("temperatureAlert", 'false')
        device_client.send_event(message, properties=prop_map, send_context=message_counter)

        print ( "Starting the IoT Hub Python sample using protocol %s..." % hub_manager.client_protocol)
        print ( "The sample is now waiting for messages and will indefinitely.  Press Ctrl-C to exit. ")

        while True:
            time.sleep(1)

    except IoTHubError as iothub_error:
        print ( "Unexpected error %s from IoTHub" % iothub_error )
        return
    except KeyboardInterrupt:
        print ( "IoTHubModuleClient sample stopped" )

if __name__ == '__main__':
    main(PROTOCOL)
