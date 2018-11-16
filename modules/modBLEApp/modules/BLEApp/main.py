# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import random
import time
import sys
import os
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
    
    # def __init__(self):      

    #
    # To be called whenever the feature updates its data.
    #
    # @param feature Feature that has updated.
    # @param sample  Data extracted from the feature.
    #
    def on_update(self, feature, sample):
        #if(self.num < NOTIFICATIONS):
        print(feature)
        send_event_to_output(BLE1_APPMOD_OUTPUT, "temperature: 34", {"temperatureAlert":'true'}, 0)
        self.num += 1


# Bluetooth Scanning time in seconds.
SCANNING_TIME_s = 5

# Bluetooth Low Energy devices' MAC address.
IOT_DEVICE_1_MAC = 'd8:9a:e3:f0:12:d7'
IOT_DEVICE_2_MAC = 'd7:90:95:be:58:7e' # TODO device 2 not set yet

# Number of notifications to get before disabling them.
NOTIFICATIONS = 3

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


def receive_ble1_message_callback(message, user_context):
        print ("received message on device 1!!")
        print ("user-context {}".format(user_context))
        # TODO From here we send switch info back to BLE device, e.g.
        # Writing switch status.
        # iot_device_2.disable_notifications(iot_device_2_feature_switch)
        # iot_device_2_feature_switch.write_switch_status(iot_device_2_status.value)
        # iot_device_2.enable_notifications(iot_device_2_feature_switch)


def main(protocol):
    try:
        print ( "\nPython %s\n" % sys.version )
        print ( "BLEModApp" )

        initialize_client(IoTHubTransportProvider.MQTT)
        set_message_callback(BLE1_APPMOD_INPUT, receive_ble1_message_callback, USER_CONTEXT)

        # Global variables.
        global iot_device_1, iot_device_2
        global iot_device_1_feature_switch, iot_device_2_feature_switch
        global iot_device_1_status, iot_device_2_status

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
                device_found = False
                for discovered in discovered_devices:
                    device_name = discovered.get_name()
                    print('%d) %s: [%s]' % (i, discovered.get_name(), discovered.get_tag()))
                    if discovered.get_tag() == IOT_DEVICE_1_MAC:
                        iot_device_1 = discovered
                        device_found = True
                        devices.append(iot_device_1)
                        print("IOT_DEVICE device found!")
                    elif discovered.get_tag() == IOT_DEVICE_2_MAC:
                        iot_device_2 = discovered
                        devices.append(iot_device_2)
                    if len(devices) == 1:
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

        # Resetting switches.
        print('Resetting switches...')
        iot_device_1_feature_switch.write_switch_status(iot_device_1_status.value)

        # Handling sensing and actuation of switch devices.
        iot_device_1_feature_switch.add_listener(MyFeatureListener())

        # Enabling notifications.
        print('Enabling Bluetooth notifications...')
        iot_device_1.enable_notifications(iot_device_1_feature_switch)

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
