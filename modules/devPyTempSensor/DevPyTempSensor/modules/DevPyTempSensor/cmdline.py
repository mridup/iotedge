import os
import sys
import logging
import argparse
import random
import time

from hubmanager.hubmanager import *

MESSAGE_COUNT = 2
AVG_WIND_SPEED = 10.0
MIN_TEMPERATURE = 20.0
MIN_HUMIDITY = 60.0

MSG_TXT = "{\"iotedge-0\": \"DevPyTempSensor\",\"windSpeed\": %.2f,\"temperature\": %.2f,\"humidity\": %.2f}"

def run_module(args):
    print ( "Run Module sending %d messages" % MESSAGE_COUNT )

    for message_counter in range(0, MESSAGE_COUNT):
        temperature = MIN_TEMPERATURE + (random.random() * 10)
        humidity = MIN_HUMIDITY + (random.random() * 20)
        msg_txt_formatted = MSG_TXT % (AVG_WIND_SPEED + (random.random() * 4 + 2), temperature, humidity)

        msg_properties = {"temperatureAlert": 'true' if temperature > 28 else 'false'}
        send_event_to_output("temperatureOutput", msg_txt_formatted, msg_properties, message_counter)
        print ( "IoTHubModuleClient.send_event_to_output accepted message [%d] for transmission to IoT Hub." % message_counter )
    return


def run_cmdline():
    def do_stuff(command, args, return_keys=False):
        switcher = {
            'run_module': lambda: run_module(args)
        }
        if return_keys:
            return switcher.keys()
        func = switcher.get(command, lambda: "nothing")
        return func()
    
    parser = argparse.ArgumentParser(description='EdgeST-SDK Azure Module Command Line')
    parser.add_argument('command', help=','.join(do_stuff(None, None, return_keys=True)))
    parser.add_argument('-message', help='send a message string', type=str, default='default_message')
    args = parser.parse_args()
    command = args.command
    logging.info('Running {} with args:{}'.format(command, args))
    do_stuff(command, args)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    run_cmdline()

