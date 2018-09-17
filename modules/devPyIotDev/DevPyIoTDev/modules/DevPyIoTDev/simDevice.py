# Copyright (c) STMicroelectronics. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import json
import random
import time
import iothub_client
import iothub_client_cert
import iothub_client_cert

# if you don't give the following, pyLint shows error when importing IoTHubModuleClient, etc. from iothub_client
# pylint: disable=E0611
from iothub_client import IoTHubModuleClient, IoTHubClientError, IoTHubTransportProvider
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue
from iothub_client import IoTHubClient

TIMEOUT = 241000
MINIMUM_POLLING_TIME = 9

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

RECEIVE_CONTEXT = 0
AVG_WIND_SPEED = 10.0
MIN_TEMPERATURE = 20.0
MIN_HUMIDITY = 60.0
MESSAGE_COUNT = 5
RECEIVED_COUNT = 0
TWIN_CONTEXT = 0
METHOD_CONTEXT = 0

# global counters
RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0
BLOB_CALLBACKS = 0
TWIN_CALLBACKS = 0
SEND_REPORTED_STATE_CALLBACKS = 0
METHOD_CALLBACKS = 0

# chose HTTP, AMQP or MQTT as transport protocol
PROTOCOL = IoTHubTransportProvider.MQTT

MSG_TXT = "{\"deviceId\": \"myPythonDevice\",\"windSpeed\": %.2f,\"temperature\": %.2f,\"humidity\": %.2f}"

class DeviceClient(object):

    def __init__(
            self,
            connection_string,
            protocol=IoTHubTransportProvider.MQTT):
        print ("Device Client __init__ ....creating IoTHubClient connection!")
        print ("Connection String = %s" % connection_string)
        self.client_protocol = protocol
        self.client = IoTHubClient(connection_string, protocol)
        if protocol == IoTHubTransportProvider.HTTP:
            self.client.set_option("timeout", TIMEOUT)
            self.client.set_option("MinimumPollingTime", MINIMUM_POLLING_TIME)
        # set the time until a message times out
        self.client.set_option("messageTimeout", MESSAGE_TIMEOUT)
        # some embedded platforms need certificate information
        # self.set_certificates()
        self.client.set_message_callback(self.receive_message_callback, RECEIVE_CONTEXT)
        self.client.set_device_twin_callback(self.device_twin_callback, TWIN_CONTEXT)
        self.client.set_device_method_callback(self.device_method_callback, METHOD_CONTEXT)


    def set_certificates(self):
        from iothub_client_cert import CERTIFICATES
        try:
            self.client.set_option("TrustedCerts", CERTIFICATES)
            print ( "set_option TrustedCerts successful" )
        except IoTHubClientError as iothub_client_error:
            print ( "set_option TrustedCerts failed (%s)" % iothub_client_error )


    def send_event(self, event, properties, send_context):
        if not isinstance(event, IoTHubMessage):
            event = IoTHubMessage(bytearray(event, 'utf8'))

        if len(properties) > 0:
            prop_map = event.properties()
            for key in properties:
                prop_map.add_or_update(key, properties[key])

        self.client.send_event_async(
            event, self.send_confirmation_callback, send_context)


    def send_reported_state(self, reported_state, size, user_context):
        self.client.send_reported_state(
            reported_state, size,
            self.send_reported_state_callback, user_context)


    def upload_to_blob(self, destinationfilename, source, size, usercontext):
        self.client.upload_blob_async(
            destinationfilename, source, size, 
            self.blob_upload_conf_callback, usercontext)


    def send_confirmation_callback(self, message, result, user_context):
        global SEND_CALLBACKS
        print ( "Confirmation[%d] received for message with result = %s" % (user_context, result) )
        map_properties = message.properties()
        key_value_pair = map_properties.get_internals()
        print ( "    Properties: %s" % key_value_pair )
        SEND_CALLBACKS += 1
        print ( "    Total calls confirmed: %d" % SEND_CALLBACKS )


    def receive_message_callback(self, message, counter):
        global RECEIVE_CALLBACKS
        message_buffer = message.get_bytearray()
        size = len(message_buffer)
        print ( "Received Message [%d]:" % counter )
        print ( "    Data: <<<%s>>> & Size=%d" % (message_buffer[:size].decode('utf-8'), size) )
        map_properties = message.properties()
        key_value_pair = map_properties.get_internals()
        print ( "    Properties: %s" % key_value_pair )
        counter += 1
        RECEIVE_CALLBACKS += 1
        print ( "    Total calls received: %d" % RECEIVE_CALLBACKS )
        return IoTHubMessageDispositionResult.ACCEPTED


    def device_twin_callback(self, update_state, payload, user_context):
        global TWIN_CALLBACKS
        print ( "\nTwin callback called with:\nupdateStatus = %s\npayload = %s\ncontext = %s" % (update_state, payload, user_context) )
        TWIN_CALLBACKS += 1
        print ( "Total calls confirmed: %d\n" % TWIN_CALLBACKS )


    def send_reported_state_callback(self, status_code, user_context):
        global SEND_REPORTED_STATE_CALLBACKS
        print ( "Confirmation for reported state received with:\nstatus_code = [%d]\ncontext = %s" % (status_code, user_context) )
        SEND_REPORTED_STATE_CALLBACKS += 1
        print ( "    Total calls confirmed: %d" % SEND_REPORTED_STATE_CALLBACKS )


    def device_method_callback(self, method_name, payload, user_context):
        global METHOD_CALLBACKS
        print ( "\nMethod callback called with:\nmethodName = %s\npayload = %s\ncontext = %s" % (method_name, payload, user_context) )
        METHOD_CALLBACKS += 1
        print ( "Total calls confirmed: %d\n" % METHOD_CALLBACKS )
        device_method_return_value = DeviceMethodReturnValue()
        device_method_return_value.response = "{ \"Response\": \"This is the response from the device\" }"
        device_method_return_value.status = 200
        return device_method_return_value


    def blob_upload_conf_callback(self, result, user_context):
        global BLOB_CALLBACKS
        print ( "Blob upload confirmation[%d] received for message with result = %s" % (user_context, result) )
        BLOB_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % BLOB_CALLBACKS )
