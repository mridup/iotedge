# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import random
import time
import sys
import os
import json
import requests
import blue_st_sdk
import iothub_client
# pylint: disable=E0611
from iothub_client import IoTHubModuleClient, IoTHubClientError, IoTHubTransportProvider
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue

from blue_st_sdk.manager import Manager, ManagerListener
from blue_st_sdk.node import NodeListener
from blue_st_sdk.feature import FeatureListener
from blue_st_sdk.features import *
from bluepy.btle import BTLEException

from enum import Enum

BLE1_APPMOD_INPUT   = 'BLE1_App_Input'
BLE2_APPMOD_INPUT   = 'BLE2_App_Input'
BLE1_APPMOD_OUTPUT  = 'BLE1_App_Output'
BLE2_APPMOD_OUTPUT  = 'BLE2_App_Output'
BLE1_DEVMOD_INPUT   = 'BLE1_Input'
BLE2_DEVMOD_INPUT   = 'BLE2_Input'
BLE1_DEVMOD_OUTPUT  = 'BLE1_Output'
BLE2_DEVMOD_OUTPUT  = 'BLE2_Output'

# Status of the switch.
class SwitchStatus(Enum):
    OFF = 0
    ON = 1

# INTERFACES

#
# Implementation of the interface used by the Manager class to notify that a new
# node has been discovered or that the scanning starts/stops.
#
class MyManagerListener(ManagerListener):

    #
    # This method is called whenever a discovery process starts or stops.
    #
    # @param manager Manager instance that starts/stops the process.
    # @param enabled True if a new discovery starts, False otherwise.
    #
    def on_discovery_change(self, manager, enabled):
        print('Discovery %s.' % ('started' if enabled else 'stopped'))
        if not enabled:
            print()

    #
    # This method is called whenever a new node is discovered.
    #
    # @param manager Manager instance that discovers the node.
    # @param node    New node discovered.
    #
    def on_node_discovered(self, manager, node):
        print('New device discovered: %s.' % (node.get_name()))


#
# Implementation of the interface used by the Node class to notify that a node
# has updated its status.
#
class MyNodeListener(NodeListener):

    #
    # To be called whenever a node changes its status.
    #
    # @param node       Node that has changed its status.
    # @param new_status New node status.
    # @param old_status Old node status.
    #
    def on_status_change(self, node, new_status, old_status):
        print('Device %s went from %s to %s.' %
            (node.get_name(), str(old_status), str(new_status)))


#
# Implementation of the interface used by the Feature class to notify that a
# feature has updated its data.
#
class MyFeatureListenerBLE1(FeatureListener):

    num = 0
    
    def __init__(self, hubManager):
        self.hubManager = hubManager

    #
    # To be called whenever the feature updates its data.
    #
    # @param feature Feature that has updated.
    # @param sample  Data extracted from the feature.
    #
    def on_update(self, feature, sample):
        #if(self.num < NOTIFICATIONS):
        # print('\n>>FeatureListenerBLE1 update: feature: ')
        print(feature)
        sample_str = sample.__str__()
        # print('sample data:' + sample_str)

        event = IoTHubMessage(bytearray(sample_str, 'utf8'))
        self.hubManager.forward_event_to_output(BLE1_APPMOD_OUTPUT, event, 0)
        self.num += 1


# Bluetooth Scanning time in seconds.
SCANNING_TIME_s = 5

# Bluetooth Low Energy devices' MAC address.
IOT_DEVICE_1_MAC = 'd8:9a:e3:f0:12:d7'  ##System Lab BLE board

# Number of notifications to get before disabling them.
NOTIFICATIONS = 3

# Number of node devices
NUM_DEVICES = 1

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubModuleClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

# global counters
RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0
USER_CONTEXT = 0
RECEIVE_CONTEXT = 0
AVG_WIND_SPEED = 10.0
MIN_TEMPERATURE = 20.0
MIN_HUMIDITY = 60.0
MESSAGE_COUNT = 3

MSG_TXT = "{\"iotedge\": \"DevPyTempSensor\",\"windSpeed\": %.2f,\"temperature\": %.2f,\"humidity\": %.2f}"

# Choose HTTP, AMQP or MQTT as transport protocol.  Currently only MQTT is supported.
PROTOCOL = IoTHubTransportProvider.MQTT


# This function will be called every time a method request is received
def method_callback(method_name, payload, user_context):
    print('received method call:')
    print('\tmethod name:', method_name)
    print('\tpayload:', payload)
    payload_url = str(payload[0])
    print(payload_url)
    json_dict = json.loads(payload)
    print ('\nURL to download from:')
    url = json_dict['url']
    print (url)
    filename = url[url.rfind("/")+1:]
    print (filename)

    # Download from URL provided in payload    
    # https://sample-videos.com/text/Sample-text-file-10kb.txt
    download_file = "/app/" + filename
    #file_url = "http://codex.cs.yale.edu/avi/db-book/db4/slide-dir/ch1-2.pdf"
    print('downloading file...')
    r = requests.get(url, stream = True)
    with open(download_file,"wb") as pdf: 
        for chunk in r.iter_content(chunk_size=1024):  
            # writing one chunk at a time to pdf file 
            if chunk: 
                pdf.write(chunk) 
    
    retval = DeviceMethodReturnValue()
    if os.path.isfile(download_file):
        print('download complete')
        retval.status = 200
        retval.response = "{\"result\":\"okay\"}"
    else:
        print('download failure')
        retval.status = 200
        retval.response = "{\"result\":\"error\"}"

    # Now start FW update process using blue-stsdk-python interface
    #  
    return retval


def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    print ( "\nConfirmation[%d] received for message with result = %s" % (user_context, result) )
    SEND_CALLBACKS += 1
    # print ( "Total calls confirmed: %d" % SEND_CALLBACKS )


def receive_ble1_message_callback(message, hubManager):
    global RECEIVE_CALLBACKS
    
    # Getting value.
    message_buffer = message.get_bytearray()
    size = len(message_buffer)
    message_text = message_buffer[:size].decode('utf-8')
    # print('\nble1 receive msg cb << message: \n')    
    data = message_text.split()[3]
    return IoTHubMessageDispositionResult.ACCEPTED


# module_twin_callback is invoked when the module twin's desired properties are updated.
def module_twin_callback(update_state, payload, user_context):
    print ( "\nModule twin callback >> call confirmed\n")


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
        self.client.set_message_callback(BLE1_APPMOD_INPUT, receive_ble1_message_callback, self)

        # Sets the callback when a module twin's desired properties are updated.
        self.client.set_module_twin_callback(module_twin_callback, self)

        # Register the callback with the client
        self.client.set_module_method_callback(method_callback, self)
        

    # Forwards the message received onto the next stage in the process.
    def forward_event_to_output(self, outputQueueName, event, send_context):
        self.client.send_event_async(
            outputQueueName, event, send_confirmation_callback, send_context)

    def get_send_status(self):
        return self.client.get_send_status()


def main(protocol):
    try:
        print ( "\nPython %s\n" % sys.version )

        # Global variables.
        global iot_device_1
        global iot_device_1_feature_switch
        global iot_device_1_status

        # initialize_client(IoTHubTransportProvider.MQTT)
        hub_manager = HubManager(protocol)

        # Initial state.
        iot_device_1_status = SwitchStatus.OFF

        print ( "Starting the FWModApp module using protocol MQTT...")
        print ( "This module implements a direct method to be invoked from backend or other modules as required")

        # Creating Bluetooth Manager.
        manager = Manager.instance()
        manager_listener = MyManagerListener()
        manager.add_listener(manager_listener)

        while True:
            # Synchronous discovery of Bluetooth devices.
            print('Scanning Bluetooth devices...\n')
            manager.discover(False, float(SCANNING_TIME_s))

            # Getting discovered devices.
            print('Getting node device...\n')
            discovered_devices = manager.get_nodes()

            # Listing discovered devices.
            if not discovered_devices:
                print('\nNo Bluetooth devices found.')
                continue
            else:
                print('\nAvailable Bluetooth devices:')
                # Checking discovered devices.
                devices = []
                dev_found = False
                i = 1
                for discovered in discovered_devices:
                    device_name = discovered.get_name()
                    print('%d) %s: [%s]' % (i, discovered.get_name(), discovered.get_tag()))
                    if discovered.get_tag() == IOT_DEVICE_1_MAC:
                        iot_device_1 = discovered
                        devices.append(iot_device_1)
                        print("IOT_DEVICE device found!")
                        dev_found = True
                        break
                    i += 1
                if dev_found is True:
                    break

        # Selecting a device.
        # Connecting to the devices.
        for device in devices:
            device.add_listener(MyNodeListener())
            print('Connecting to %s...' % (device.get_name()))
            device.connect()
            print('Connection done.')

        # Getting features.
        print('\nGetting features...')
        iot_device_1_feature_switch = iot_device_1.get_feature(feature_switch.FeatureSwitch)

        # Resetting switches.
        print('Resetting switches...')
        iot_device_1_feature_switch.write_switch_status(iot_device_1_status.value)

        # Handling sensing and actuation of switch devices.
        iot_device_1_feature_switch.add_listener(MyFeatureListenerBLE1(hub_manager))

        # Enabling notifications.
        print('Enabling Bluetooth notifications...')
        iot_device_1.enable_notifications(iot_device_1_feature_switch)

        # Getting notifications forever
        print("Ready to receive notifications")        

        # Bluetooth setup complete.
        print('\nBluetooth setup complete.')

        # Demo running.
        print('\nDemo running (\"CTRL+C\" to quit)...\n')

        # while True:
        #     # send a few messages every minute
        #     print ( "modfwapp sending %d messages" % MESSAGE_COUNT )

        #     for message_counter in range(0, MESSAGE_COUNT):
        #         temperature = MIN_TEMPERATURE + (random.random() * 10)
        #         humidity = MIN_HUMIDITY + (random.random() * 20)
        #         msg_txt_formatted = MSG_TXT % (
        #             AVG_WIND_SPEED + (random.random() * 4 + 2),
        #             temperature,
        #             humidity)

        #         msg_properties = {
        #             "temperatureAlert": 'true' if temperature > 28 else 'false'
        #         }
                
        #         event = IoTHubMessage(bytearray(msg_txt_formatted, 'utf8'))
        #         # hub_manager.forward_event_to_output("temperatureOutput", event, message_counter)

        #     # Wait for Commands or exit
        #     print ( "IoTHubModuleClient waiting for commands, press Ctrl-C to exit." )

        #     status_counter = 0
        #     while status_counter < 6:
        #         status = hub_manager.get_send_status()
        #         print ( "Send status: %s" % status )
        #         time.sleep(10)
        #         status_counter += 1

        # Infinite loop.
        while True:
            # continue
            # Getting notifications.
            if iot_device_1.wait_for_notifications(0.05):
                time.sleep(2) # workaround for Unexpected Response Issue
                print("rcvd notification!")
                continue

    except BTLEException as e:
        print(e)
        print('Exiting...\n')
        sys.exit(0)        
    except IoTHubError as iothub_error:
        print ( "Unexpected error %s from IoTHub" % iothub_error )
        return
    except KeyboardInterrupt:
        print ( "IoTHubModuleClient sample stopped" )

if __name__ == '__main__':
    main(PROTOCOL)
