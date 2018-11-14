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
from blue_st_sdk.features.feature_audio_adpcm import FeatureAudioADPCM
from blue_st_sdk.features.feature_audio_adpcm_sync import FeatureAudioADPCMSync
from bluepy.btle import BTLEException

from hubmanager.hubmanager import *

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
    
    #def __init__(self, hubmanager):
    #    self.hubmanager = hubmanager
    #    print("MyFeatureListener initialized with hubmanager")

    #
    # To be called whenever the feature updates its data.
    #
    # @param feature Feature that has updated.
    # @param sample  Data extracted from the feature.
    #
    def on_update(self, feature, sample):
        #if(self.num < NOTIFICATIONS):
        print(feature)
        send_event_to_output("devOutput", "temperature: 34", {"temperatureAlert":'true'}, 0)
        self.num += 1

# Bluetooth Scanning time in seconds.
SCANNING_TIME_s = 5

# Number of notifications to get before disabling them.
NOTIFICATIONS = 3

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubModuleClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

# global counters
RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0

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


#class HubManager(object):
#
#    def __init__(
#            self,
#            protocol=IoTHubTransportProvider.MQTT):
#        self.client_protocol = protocol
        #self.client = IoTHubModuleClient()
        #self.client.create_from_environment(protocol)

        # set the time until a message times out
        #self.client.set_option("messageTimeout", MESSAGE_TIMEOUT)
        
        # sets the callback when a message arrives on "input1" queue.  Messages sent to 
        # other inputs or to the default will be silently discarded.
        #self.client.set_message_callback("input1", receive_message_callback, self)

    # Forwards the message received onto the next stage in the process.
#    def forward_event_to_output(self, outputQueueName, event, send_context):
#        self.client.send_event_async(
#            outputQueueName, event, send_confirmation_callback, send_context)

def main(protocol):
    try:
        print ( "\nPython %s\n" % sys.version )
        print ( "modAppModule" )

        initialize_client(IoTHubTransportProvider.MQTT)

        print ( "Starting the IoT Hub Python sample using protocol MQTT...")
        print ( "The sample is now waiting for messages and will indefinitely.  Press Ctrl-C to exit. ")

        # Creating Bluetooth Manager.
        manager = Manager.instance()
        manager_listener = MyManagerListener()
        manager.add_listener(manager_listener)

        while True:
            # Synchronous discovery of Bluetooth devices.
            print('Scanning Bluetooth devices...\n')
            manager.discover(False, SCANNING_TIME_s)

            # Getting discovered devices.
            print('Getting node device...\n')
            devices = manager.get_nodes()

            # Listing discovered devices.
            if not devices:
                print('\nNo Bluetooth devices found.')
                continue
            else:
                print('\nAvailable Bluetooth devices:')
                i = 1
                device_found = False
                for device in devices:
                    device_name = device.get_name()
                    print('%d) %s: [%s]' % (i, device.get_name(), device.get_tag()))
                    if device_name is "IOT_DEVICE":
                        device_found = True
                        print("IOT_DEVICE device found!")
                    i += 1
                break

        # Selecting a device.
        # Connecting to the device.
        node_listener = MyNodeListener()
        device.add_listener(node_listener)
        print('\nConnecting to %s...' % (device.get_name()))
        device.connect()
        print('Connection done.')
        #else:
        #    manager.remove_listener(manager_listener)
        #    print('IOT_DEVICE not found!')
        #    print('Exiting...\n')
        #    sys.exit(0)

        print('\nFeatures:')
        i = 1
        features = device.get_features()
        audioFeature = None
        audioSyncFeature = None
        for feature in features:
            if not feature.get_name() == FeatureAudioADPCMSync.FEATURE_NAME:
                if feature.get_name() == FeatureAudioADPCM.FEATURE_NAME:
                    audioFeature = feature
                    print('%d,%d) %s' % (i,i+1, "Audio & Sync"))
                else:
                    print('%d) %s' % (i, feature.get_name()))
                i+=1
            else:
                audioSyncFeature = feature

        choice = 7
        feature = features[choice - 1]

        # Enabling notifications.
        feature_listener = MyFeatureListener()
        feature.add_listener(feature_listener)
        device.enable_notifications(feature)

        if feature.get_name() == FeatureAudioADPCM.FEATURE_NAME:
            audioSyncFeature_listener = MyFeatureListener()
            audioSyncFeature.add_listener(audioSyncFeature_listener)
            device.enable_notifications(audioSyncFeature)
        elif feature.get_name() == FeatureAudioADPCMSync.FEATURE_NAME:
            audioFeature_listener = MyFeatureListener()
            audioFeature.add_listener(audioFeature_listener)
            device.enable_notifications(audioFeature)

        print("Ready to receive notifications")
        # Getting notifications forever
        #n=0
        while True:
            if device.wait_for_notifications(0.05):
                print("rcvd notification")

        #Disable notifications
        #device.disable_notifications(feature)
        #feature.remove_listener(feature_listener)

        #if feature.get_name() == FeatureAudioADPCM.FEATURE_NAME:
        #    device.disable_notifications(audioSyncFeature)
        #    audioSyncFeature.remove_listener(audioSyncFeature_listener)
        #elif feature.get_name() == FeatureAudioADPCMSync.FEATURE_NAME:
        #    device.disable_notifications(audioFeature)
        #    audioFeature.remove_listener(audioFeature_listener)


        while True:
            time.sleep(1)

    except IoTHubError as iothub_error:
        print ( "Unexpected error %s from IoTHub" % iothub_error )
        return
    except KeyboardInterrupt:
        print ( "IoTHubModuleClient sample stopped" )

if __name__ == '__main__':
    main(PROTOCOL)
