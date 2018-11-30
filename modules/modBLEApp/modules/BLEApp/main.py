# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import random
import time
import sys
import os
import json
import blue_st_sdk
import iothub_client
# pylint: disable=E0611
from iothub_client import IoTHubModuleClient, IoTHubClientError, IoTHubTransportProvider
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError

from blue_st_sdk.manager import Manager, ManagerListener
from blue_st_sdk.node import NodeListener
from blue_st_sdk.feature import FeatureListener
from blue_st_sdk.features import *
from bluepy.btle import BTLEException

from hubmanager.hubmanager import *
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
class MyFeatureListener(FeatureListener):

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
        print(feature)
        print('sample:')
        sample_str = sample.__str__()
        print(sample_str)

        event = IoTHubMessage(bytearray(sample_str, 'utf8'))

        # json_sample = json.dumps(sample)
        # send_event_to_output(BLE1_APPMOD_OUTPUT, sample_str, send_confirmation_callback, {"temperatureAlert":'true'}, 0)
        self.hubManager.forward_event_to_output(BLE1_APPMOD_OUTPUT, event, 0)
        self.num += 1


# Bluetooth Scanning time in seconds.
SCANNING_TIME_s = 5

# Bluetooth Low Energy devices' MAC address.
IOT_DEVICE_1_MAC = 'd8:9a:e3:f0:12:d7'
IOT_DEVICE_2_MAC = 'cd:09:26:cd:a7:f8'

# Number of notifications to get before disabling them.
NOTIFICATIONS = 3

# Number of node devices
NUM_DEVICES = 2

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubModuleClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

# global counters
RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0
USER_CONTEXT = 0

# Choose HTTP, AMQP or MQTT as transport protocol.  Currently only MQTT is supported.
PROTOCOL = IoTHubTransportProvider.MQTT

def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    print ( "MPD: Confirmation[%d] received for message with result = %s" % (user_context, result) )
    # map_properties = message.properties()
    # key_value_pair = map_properties.get_internals()
    # print ( "    Properties: %s" % key_value_pair )
    # SEND_CALLBACKS += 1
    # print ( "    Total calls confirmed: %d" % SEND_CALLBACKS )

# Global variables.
global iot_device_1, iot_device_2
global iot_device_1_feature_switch, iot_device_2_feature_switch
global iot_device_1_status, iot_device_2_status

def receive_message_callback(message, hubManager):
    global RECEIVE_CALLBACKS
    TEMPERATURE_THRESHOLD = 25
    message_buffer = message.get_bytearray()
    size = len(message_buffer)
    message_text = message_buffer[:size].decode('utf-8')
    print('\nreceive msg cb << message: \n')
    print(message_text)    
    data = message_text.split()[3]
    print ('data part:')
    print (data)
    # hubManager.forward_event_to_output("randomoutput1", message, 0)
    return IoTHubMessageDispositionResult.ACCEPTED


def receive_ble1_message_callback(message, hubManager):
    print ("received message on device 1!!")
    # print ("sample {}".format(message))
    
    message_buffer = message.get_bytearray()
    size = len(message_buffer)
    message_text = message_buffer[:size].decode('utf-8')
    data = message_text.split()[3]
    print ('data part:')
    print (data)
    
    # Toggle switch status.
    # iot_device_2_status = SwitchStatus.ON if data != '[0]' else SwitchStatus.OFF
    
    # # Writing switch status.
    # iot_device_2.disable_notifications(iot_device_2_feature_switch)
    # iot_device_2_feature_switch.write_switch_status(iot_device_2_status.value)
    # iot_device_2.enable_notifications(iot_device_2_feature_switch)
    # print ("exiting receive_ble1_message_callback...")


def receive_ble2_message_callback(message, user_context):
    print ("received message on device 2!!")
    print ("user-context {}".format(user_context))

    global iot_device_1, iot_device_1_feature_switch, iot_device_1_status
    # iot_device_1_status = SwitchStatus.OFF
    # Getting value.
    print ("module receive_ble2 message:")
    print (message)
    switch_status = feature_switch.FeatureSwitch.get_switch_status(message)

    # Toggle switch status.
    iot_device_1_status = SwitchStatus.ON if switch_status != 0 else SwitchStatus.OFF
    
    # Writing switch status.
    iot_device_1.disable_notifications(iot_device_1_feature_switch)
    iot_device_1_feature_switch.write_switch_status(iot_device_1_status.value)
    iot_device_1.enable_notifications(iot_device_1_feature_switch)


# module_twin_callback is invoked when the module twin's desired properties are updated.
def module_twin_callback(update_state, payload, user_context):
    # global TWIN_CALLBACKS
    # global TEMPERATURE_THRESHOLD
    # print ( "\nTwin callback called with:\nupdateStatus = %s\npayload = %s\ncontext = %s" % (update_state, payload, user_context) )
    # data = json.loads(payload)
    # if "desired" in data and "TemperatureThreshold" in data["desired"]:
    #     TEMPERATURE_THRESHOLD = data["desired"]["TemperatureThreshold"]
    # if "TemperatureThreshold" in data:
    #     TEMPERATURE_THRESHOLD = data["TemperatureThreshold"]
    # TWIN_CALLBACKS += 1
    print ( "\nTwin callback >> call confirmed\n")


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
        self.client.set_message_callback(BLE1_APPMOD_INPUT, receive_message_callback, self)

        # Sets the callback when a module twin's desired properties are updated.
        self.client.set_module_twin_callback(module_twin_callback, self)
        

    # Forwards the message received onto the next stage in the process.
    def forward_event_to_output(self, outputQueueName, event, send_context):
        self.client.send_event_async(
            outputQueueName, event, send_confirmation_callback, send_context)


def main(protocol):
    try:
        print ( "\nPython %s\n" % sys.version )
        print ( "BLEModApp" )

        # initialize_client(IoTHubTransportProvider.MQTT)
        hub_manager = HubManager(protocol)
        # set_message_callback(BLE1_APPMOD_INPUT, receive_ble1_message_callback, USER_CONTEXT)
        # set_message_callback(BLE2_APPMOD_INPUT, receive_ble2_message_callback, USER_CONTEXT)

        

        # Initial state.
        iot_device_1_status = SwitchStatus.OFF
        iot_device_2_status = SwitchStatus.OFF

        print ( "Starting the BLEModApp module using protocol MQTT...")
        print ( "This module will listen for feature changes of 2 BLE devices")
        print ( "and forward the messages to respective BLE dev module. It will also listen for")
        print ( "incoming route messages and subsequently on reception,")
        print ( "act on the feature of the respective BLE devices")

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
                i = 1
                for discovered in discovered_devices:
                    device_name = discovered.get_name()
                    print('%d) %s: [%s]' % (i, discovered.get_name(), discovered.get_tag()))
                    if discovered.get_tag() == IOT_DEVICE_1_MAC:
                        iot_device_1 = discovered
                        devices.append(iot_device_1)
                        print("IOT_DEVICE device 1 found!")
                    elif discovered.get_tag() == IOT_DEVICE_2_MAC:
                        iot_device_2 = discovered
                        devices.append(iot_device_2)
                        print("IOT_DEVICE device 2 found!")
                    if len(devices) == 2:
                        break
                    i += 1
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
        iot_device_2_feature_switch = iot_device_2.get_feature(feature_switch.FeatureSwitch)

        # Resetting switches.
        print('Resetting switches...')
        iot_device_1_feature_switch.write_switch_status(iot_device_1_status.value)
        iot_device_2_feature_switch.write_switch_status(iot_device_2_status.value)

        # Handling sensing and actuation of switch devices.
        iot_device_1_feature_switch.add_listener(MyFeatureListener(hub_manager))
        # iot_device_2_feature_switch.add_listener(MyFeatureListener())

        # Enabling notifications.
        print('Enabling Bluetooth notifications...')
        iot_device_1.enable_notifications(iot_device_1_feature_switch)
        # iot_device_2.enable_notifications(iot_device_2_feature_switch)

        # Getting notifications forever
        print("Ready to receive notifications")        

        # Bluetooth setup complete.
        print('\nBluetooth setup complete.')

        # Demo running.
        print('\nDemo running (\"CTRL+C\" to quit)...\n')

        # Infinite loop.
        while True:
            # Getting notifications.
            if iot_device_1.wait_for_notifications(0.05):
                print("rcvd notification!")
        
        print ("...going out...")

        while True:
            sleep(1)

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
