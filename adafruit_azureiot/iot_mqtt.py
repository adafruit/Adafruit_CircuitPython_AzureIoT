"""MQTT client for Azure IoT
"""

import gc
import json
import time
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi.adafruit_esp32spi_wifimanager import ESPSPI_WiFiManager
import adafruit_minimqtt as minimqtt
from adafruit_minimqtt import MQTT
import circuitpython_parse as parse
import adafruit_logging as logging
from .device_registration import DeviceRegistration
from . import constants


class IoTResponse:
    """A response from a direct method call
    """

    def __init__(self, code, message):
        self._code = code
        self._message = message

    def get_response_code(self):
        """Gets the method response code
        """
        return self._code

    def get_response_message(self):
        """Gets the method response message
        """
        return self._message


class IoTMQTTCallback:
    """An interface for classes that can be called by MQTT events
    """

    def message_sent(self, data) -> None:
        """Called when a message is sent to the cloud
        """

    def connection_status_change(self, connected: bool) -> None:
        """Called when the connection status changes
        """

    # pylint: disable=W0613, R0201
    def direct_method_called(self, method_name: str, payload) -> IoTResponse:
        """Called when a direct method is invoked
        """
        return IoTResponse("", "")

    # pylint: disable=C0103
    def cloud_to_device_message_received(self, body: str, properties: dict) -> None:
        """Called when a cloud to device message is received
        """

    def device_twin_desired_updated(self, desired_property_name: str, desired_property_value, desired_version: int) -> None:
        """Called when the device twin desired properties are updated
        """

    def device_twin_reported_updated(self, reported_property_name: str, reported_property_value, reported_version: int) -> None:
        """Called when the device twin reported values are updated
        """

    def settings_updated(self) -> None:
        """Called when the settings are updated
        """


# pylint: disable=R0902
class IoTMQTT:
    """MQTT client for Azure IoT
    """

    _iotc_api_version = constants.IOTC_API_VERSION

    def _gen_sas_token(self):
        token_expiry = int(time.time() + self._token_expires)
        uri = self._hostname + "%2Fdevices%2F" + self._device_id
        signed_hmac_sha256 = DeviceRegistration.compute_derived_symmetric_key(self._key, uri + "\n" + str(token_expiry))
        signature = parse.quote(signed_hmac_sha256, "~()*!.'")
        if signature.endswith("\n"):  # somewhere along the crypto chain a newline is inserted
            signature = signature[:-1]
        token = "SharedAccessSignature sr={}&sig={}&se={}".format(uri, signature, token_expiry)
        return token

    # Workaround for https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT/issues/25
    def _try_create_mqtt_client(self, hostname):
        minimqtt.set_socket(socket, self._wifi_manager.esp)

        self._mqtts = MQTT(
            broker=hostname,
            username=self._username,
            password=self._passwd,
            port=8883,
            keep_alive=120,
            is_ssl=True,
            client_id=self._device_id,
            log=True,
        )

        self._mqtts.logger.setLevel(logging.INFO)

        # set actions to take throughout connection lifecycle
        self._mqtts.on_connect = self._on_connect
        self._mqtts.on_message = self._on_message
        self._mqtts.on_log = self._on_log
        self._mqtts.on_publish = self._on_publish
        self._mqtts.on_disconnect = self._on_disconnect

        # initiate the connection using the adafruit_minimqtt library
        self._mqtts.last_will()
        self._mqtts.connect()

    def _create_mqtt_client(self):
        try:
            self._try_create_mqtt_client(self._hostname)
        except ValueError:
            # Workaround for https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT/issues/25
            self._try_create_mqtt_client("https://" + self._hostname)

    # pylint: disable=C0103, W0613
    def _on_connect(self, client, userdata, _, rc):
        self._logger.info("- iot_mqtt :: _on_connect :: rc = " + str(rc) + ", userdata = " + str(userdata))
        if rc == 0:
            self._mqtt_connected = True
        self._auth_response_received = True
        self._callback.connection_status_change(True)

    # pylint: disable=C0103, W0613
    def _on_log(self, client, userdata, level, buf):
        self._logger.info("mqtt-log : " + buf)
        if level <= 8:
            self._logger.error("mqtt-log : " + buf)

    def _on_disconnect(self, client, userdata, rc):
        self._logger.info("- iot_mqtt :: _on_disconnect :: rc = " + str(rc))
        self._auth_response_received = True

        if rc == 5:
            self._logger.error("on(disconnect) : Not authorized")
            self.disconnect()

        if rc == 1:
            self._mqtt_connected = False

        if rc != 5:
            self._callback.connection_status_change(False)

    def _on_publish(self, client, data, topic, msg_id):
        self._logger.info("- iot_mqtt :: _on_publish :: " + str(data) + " on topic " + str(topic))

    # pylint: disable=W0703
    def _handle_device_twin_update(self, msg: str, topic: str):
        self._logger.debug("- iot_mqtt :: _echo_desired :: " + topic)
        twin = None
        desired = None

        print(msg)

        try:
            twin = json.loads(msg)
        except Exception as e:
            self._logger.error("ERROR: JSON parse for Device Twin message object has failed. => " + msg + " => " + str(e))
            return

        if "reported" in twin:
            reported = twin["reported"]

            if "$version" in reported:
                reported_version = reported["$version"]
                reported.pop("$version")
            else:
                self._logger.error("ERROR: Unexpected payload for reported twin update => " + msg)
                return

            for property_name, value in reported.items():
                self._callback.device_twin_reported_updated(property_name, value, reported_version)

        is_patch = "desired" not in twin

        if is_patch:
            desired = twin
        else:
            desired = twin["desired"]

        if "$version" in desired:
            desired_version = desired["$version"]
            desired.pop("$version")
        else:
            self._logger.error("ERROR: Unexpected payload for desired twin update => " + msg)
            return

        for property_name, value in desired.items():
            self._callback.device_twin_desired_updated(property_name, value, desired_version)

    def _handle_direct_method(self, msg: str, topic: str):
        index = topic.find("$rid=")
        method_id = 1
        method_name = "None"
        if index == -1:
            self._logger.error("ERROR: C2D doesn't include topic id")
        else:
            method_id = topic[index + 5 :]
            topic_template = "$iothub/methods/POST/"
            len_temp = len(topic_template)
            method_name = topic[len_temp : topic.find("/", len_temp + 1)]

        ret = self._callback.direct_method_called(method_name, msg)

        ret_code = 200
        ret_message = "{}"
        if ret.get_response_code() is not None:
            ret_code = ret.get_response_code()
        if ret.get_response_message() is not None:
            ret_message = ret.get_response_message()

            # ret message must be JSON
            if not ret_message.startswith("{") or not ret_message.endswith("}"):
                ret_json = {"Value": ret_message}
                ret_message = json.dumps(ret_json)

        next_topic = "$iothub/methods/res/{}/?$rid={}".format(ret_code, method_id)
        self._logger.info("C2D: => " + next_topic + " with data " + ret_message + " and name => " + method_name)
        self._send_common(next_topic, ret_message)

    def _handle_cloud_to_device_message(self, msg: str, topic: str):
        parts = topic.split("&")[1:]

        properties = {}
        for part in parts:
            key_value = part.split("=")
            properties[key_value[0]] = key_value[1]

        self._callback.cloud_to_device_message_received(msg, properties)

    # pylint: disable=W0702, R0912
    def _on_message(self, client, msg_topic, payload):
        topic = ""
        msg = None

        print("Topic: ", str(msg_topic))
        self._logger.info("- iot_mqtt :: _on_message :: payload(" + str(payload) + ")")

        if payload is not None:
            try:
                msg = payload.decode("utf-8")
            except:
                msg = str(payload)

        if msg_topic is not None:
            try:
                topic = msg_topic.decode("utf-8")
            except:
                topic = str(msg_topic)

        if topic.startswith("$iothub/"):
            if topic.startswith("$iothub/twin/PATCH/properties/desired/") or topic.startswith("$iothub/twin/res/200/?$rid="):
                self._handle_device_twin_update(str(msg), topic)
            elif topic.startswith("$iothub/methods"):
                self._handle_direct_method(str(msg), topic)
            else:
                if not topic.startswith("$iothub/twin/res/"):  # not twin response
                    self._logger.error("ERROR: unknown twin! - {}".format(msg))
        elif topic.startswith("devices/{}/messages/devicebound".format(self._device_id)):
            self._handle_cloud_to_device_message(str(msg), topic)
        else:
            self._logger.error("ERROR: (unknown message) - {}".format(msg))

    def _send_common(self, topic, data) -> None:
        self._logger.debug("Sending message on topic: " + topic)
        self._logger.debug("Sending message: " + str(data))

        retry = 0

        while True:
            gc.collect()
            try:
                self._logger.debug("Trying to send...")
                self._mqtts.publish(topic, data)
                self._logger.debug("Data sent")
                break
            except RuntimeError as runtime_error:
                self._logger.info("Could not send data, retrying after 0.5 seconds: " + str(runtime_error))
                retry = retry + 1

                if retry >= 10:
                    self._logger.error("Failed to send data")
                    raise

                time.sleep(0.5)
                continue

        print("finished _send_common")
        gc.collect()

    def _get_device_settings(self) -> None:
        self._logger.info("- iot_mqtt :: _get_device_settings :: ")
        self.loop()
        self._send_common("$iothub/twin/GET/?$rid=0", " ")

    # pylint: disable=R0913
    def __init__(
        self,
        callback: IoTMQTTCallback,
        wifi_manager: ESPSPI_WiFiManager,
        hostname: str,
        device_id: str,
        key: str,
        token_expires: int = 21600,
        logger: logging = None,
    ):
        """Create the Azure IoT MQTT client
        :param wifi_manager: The WiFi manager
        :param IoTMQTTCallback callback: A callback class
        :param str hostname: The hostname of the MQTT broker to connect to, get this by registering the device
        :param str device_id: The device ID of the device to register
        :param str key: The primary or secondary key of the device to register
        :param int token_expires: The number of seconds till the token expires, defaults to 6 hours
        :param adafruit_logging logger: The logger
        """
        self._callback = callback
        self._wifi_manager = wifi_manager
        self._mqtt_connected = False
        self._auth_response_received = False
        self._mqtts = None
        self._device_id = device_id
        self._hostname = hostname
        self._key = key
        self._token_expires = token_expires
        self._username = "{}/{}/api-version={}".format(self._hostname, device_id, self._iotc_api_version)
        self._passwd = self._gen_sas_token()
        self._logger = logger if logger is not None else logging.getLogger("log")

    def connect(self):
        """Connects to the MQTT broker
        """
        self._logger.info("- iot_mqtt :: connect :: " + self._hostname)

        self._create_mqtt_client()

        self._logger.info(" - iot_mqtt :: connect :: created mqtt client. connecting..")
        while self._auth_response_received is None:
            self.loop()

        self._logger.info(" - iot_mqtt :: connect :: on_connect must be fired. Connected ? " + str(self.is_connected()))
        if not self.is_connected():
            return 1

        self._mqtt_connected = True
        self._auth_response_received = True

        self._mqtts.subscribe("devices/{}/messages/events/#".format(self._device_id))
        self._mqtts.subscribe("devices/{}/messages/devicebound/#".format(self._device_id))
        self._mqtts.subscribe("$iothub/twin/PATCH/properties/desired/#")  # twin desired property changes
        self._mqtts.subscribe("$iothub/twin/res/#")  # twin properties response
        self._mqtts.subscribe("$iothub/methods/#")

        if self._get_device_settings() == 0:
            self._callback.settings_updated()
        else:
            return 1

        return 0

    def disconnect(self):
        """Disconnects from the MQTT broker
        """
        if not self.is_connected():
            return

        self._logger.info("- iot_mqtt :: disconnect :: ")
        self._mqtt_connected = False
        self._mqtts.disconnect()

    def is_connected(self):
        """Gets if there is an open connection to the MQTT broker
        """
        return self._mqtt_connected

    def loop(self):
        """Listens for MQTT messages
        """
        if not self.is_connected():
            return

        self._mqtts.loop()

    def _send_common(self, topic, data):
        self._mqtts.publish(topic, data)

    def send_device_to_cloud_message(self, data, system_properties=None) -> None:
        """Send a device to cloud message from this device to Azure IoT Hub
        """
        self._logger.info("- iot_mqtt :: send_device_to_cloud_message :: " + data)
        topic = "devices/{}/messages/events/".format(self._device_id)

        if system_properties is not None:
            firstProp = True
            for prop in system_properties:
                if not firstProp:
                    topic += "&"
                else:
                    firstProp = False
                topic += prop + "=" + str(system_properties[prop])

        self._send_common(topic, data)
        self._callback.message_sent(data)

    def send_twin_patch(self, data):
        """Send a patch for the reported properties of the device twin
        """
        self._logger.info("- iot_mqtt :: sendProperty :: " + data)
        topic = "$iothub/twin/PATCH/properties/reported/?$rid={}".format(int(time.time()))
        return self._send_common(topic, data)
