import iothub_client
from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue
# from iothub_client_args import get_iothub_opt, OptionError # iothub_client_args isn't supported in azure-iothub-device-client==1.4.0

# HTTP options
# Because it can poll "after 9 seconds" polls will happen effectively
# at ~10 seconds.
# Note that for scalabilty, the default value of minimumPollingTime
# is 25 minutes. For more information, see:
# https://azure.microsoft.com/documentation/articles/iot-hub-devguide/#messaging
TIMEOUT = 241000
MINIMUM_POLLING_TIME = 9

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

RECEIVE_CONTEXT = 0
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

def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    print ( "Device Instance Confirmation[%d] received for message with result = %s" % (user_context, result) )
    map_properties = message.properties()
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    SEND_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % SEND_CALLBACKS )


def receive_message_callback(message, counter):
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


def device_twin_callback(update_state, payload, user_context):
    global TWIN_CALLBACKS
    print ( "\nTwin callback called with:\nupdateStatus = %s\npayload = %s\ncontext = %s" % (update_state, payload, user_context) )
    TWIN_CALLBACKS += 1
    print ( "Total calls confirmed: %d\n" % TWIN_CALLBACKS )


def send_reported_state_callback(status_code, user_context):
    global SEND_REPORTED_STATE_CALLBACKS
    print ( "Confirmation for reported state received with:\nstatus_code = [%d]\ncontext = %s" % (status_code, user_context) )
    SEND_REPORTED_STATE_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % SEND_REPORTED_STATE_CALLBACKS )


def device_method_callback(method_name, payload, user_context):
    global METHOD_CALLBACKS
    print ( "\nMethod callback called with:\nmethodName = %s\npayload = %s\ncontext = %s" % (method_name, payload, user_context) )
    METHOD_CALLBACKS += 1
    print ( "Total calls confirmed: %d\n" % METHOD_CALLBACKS )
    device_method_return_value = DeviceMethodReturnValue()
    device_method_return_value.response = "{ \"Response\": \"This is the response from the device\" }"
    device_method_return_value.status = 200
    return device_method_return_value


def blob_upload_conf_callback(result, user_context):
    global BLOB_CALLBACKS
    print ( "Blob upload confirmation[%d] received for message with result = %s" % (user_context, result) )
    BLOB_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % BLOB_CALLBACKS )

    
class DeviceClient(object):

    def __init__(
            self,
            connection_string,
            protocol=IoTHubTransportProvider.MQTT):
        self.client_protocol = protocol
        self.client = IoTHubClient(connection_string, protocol)
        if protocol == IoTHubTransportProvider.HTTP:
            self.client.set_option("timeout", TIMEOUT)
            self.client.set_option("MinimumPollingTime", MINIMUM_POLLING_TIME)
        # set the time until a message times out
        self.client.set_option("messageTimeout", MESSAGE_TIMEOUT)
        # some embedded platforms need certificate information
        # self.set_certificates()
        self.client.set_message_callback(receive_message_callback, RECEIVE_CONTEXT)
        self.client.set_device_twin_callback(device_twin_callback, TWIN_CONTEXT)
        self.client.set_device_method_callback(device_method_callback, METHOD_CONTEXT)

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
            event, send_confirmation_callback, send_context)

    def send_reported_state(self, reported_state, size, user_context):
        self.client.send_reported_state(
            reported_state, size,
            send_reported_state_callback, user_context)

    def upload_to_blob(self, destinationfilename, source, size, usercontext):
        self.client.upload_blob_async(
            destinationfilename, source, size,
            blob_upload_conf_callback, usercontext)

            