import iothub_client
from iothub_client import IoTHubModuleClient, IoTHubClientError, IoTHubTransportProvider
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubModuleClient.send_event_to_output.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

# global counters
SEND_CALLBACKS = 0

hub_manager = None

client_protocol = IoTHubTransportProvider.MQTT
client = IoTHubModuleClient()

def initialize_client(protocol):
    client_protocol = protocol
    # client = IoTHubModuleClient()
    print ( "\nMridu: creating module from env\n")
    client.create_from_environment(protocol)
    # set the time until a message times out
    client.set_option("messageTimeout", MESSAGE_TIMEOUT)
    # set to increase logging level
    # client.set_option("logtrace", 1)


# Sends a message to the queue with outputQueueName, "temperatureOutput" in the case of the sample.
def send_event_to_output(outputQueueName, event, properties, send_context):
    if not isinstance(event, IoTHubMessage):
        event = IoTHubMessage(bytearray(event, 'utf8'))

    if len(properties) > 0:
        prop_map = event.properties()
        for key in properties:
            prop_map.add_or_update(key, properties[key])

    client.send_event_async(
        outputQueueName, event, send_confirmation_callback, send_context)

def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    print ( "MPD: Confirmation[%d] received for message with result = %s" % (user_context, result) )
    map_properties = message.properties()
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    SEND_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % SEND_CALLBACKS )


def set_instance(instance):
    hub_manager = instance
            

def get_instance():
    return hub_manager


