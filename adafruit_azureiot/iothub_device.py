"""Connectivity to Azure IoT Hub
"""

import json
from adafruit_esp32spi.adafruit_esp32spi_wifimanager import ESPSPI_WiFiManager
import adafruit_logging as logging
from .iot_error import IoTError
from .iot_mqtt import IoTMQTT, IoTMQTTCallback, IoTResponse


def _validate_keys(connection_string_parts):
    """Raise ValueError if incorrect combination of keys
    """
    host_name = connection_string_parts.get(HOST_NAME)
    shared_access_key_name = connection_string_parts.get(SHARED_ACCESS_KEY_NAME)
    shared_access_key = connection_string_parts.get(SHARED_ACCESS_KEY)
    device_id = connection_string_parts.get(DEVICE_ID)

    if host_name and device_id and shared_access_key:
        pass
    elif host_name and shared_access_key and shared_access_key_name:
        pass
    else:
        raise ValueError("Invalid Connection String - Incomplete")


DELIMITER = ";"
VALUE_SEPARATOR = "="

HOST_NAME = "HostName"
SHARED_ACCESS_KEY_NAME = "SharedAccessKeyName"
SHARED_ACCESS_KEY = "SharedAccessKey"
SHARED_ACCESS_SIGNATURE = "SharedAccessSignature"
DEVICE_ID = "DeviceId"
MODULE_ID = "ModuleId"
GATEWAY_HOST_NAME = "GatewayHostName"

VALID_KEYS = [
    HOST_NAME,
    SHARED_ACCESS_KEY_NAME,
    SHARED_ACCESS_KEY,
    SHARED_ACCESS_SIGNATURE,
    DEVICE_ID,
    MODULE_ID,
    GATEWAY_HOST_NAME,
]


class IoTHubDevice(IoTMQTTCallback):
    """A device client for the Azure IoT Hub service
    """

    def connection_status_change(self, connected: bool) -> None:
        """Called when the connection status changes
        """
        if self._on_connection_status_changed is not None:
            # pylint: disable=E1102
            self._on_connection_status_changed(connected)

    # pylint: disable=W0613, R0201
    def direct_method_invoked(self, method_name: str, payload) -> IoTResponse:
        """Called when a direct method is invoked
        """
        if self._on_direct_method_invoked is not None:
            # pylint: disable=E1102
            return self._on_direct_method_invoked(method_name, payload)

        raise IoTError("on_direct_method_invoked not set")

    # pylint: disable=C0103
    def cloud_to_device_message_received(self, body: str, properties: dict):
        """Called when a cloud to device message is received
        """
        if self._on_cloud_to_device_message_received is not None:
            # pylint: disable=E1102
            self._on_cloud_to_device_message_received(body, properties)

    def device_twin_desired_updated(self, desired_property_name: str, desired_property_value, desired_version: int) -> None:
        """Called when the device twin is updated
        """
        if self._on_device_twin_desired_updated is not None:
            # pylint: disable=E1102
            self._on_device_twin_desired_updated(desired_property_name, desired_property_value, desired_version)

    def device_twin_reported_updated(self, reported_property_name: str, reported_property_value, reported_version: int) -> None:
        """Called when the device twin is updated
        """
        if self._on_device_twin_reported_updated is not None:
            # pylint: disable=E1102
            self._on_device_twin_reported_updated(reported_property_name, reported_property_value, reported_version)

    def __init__(self, wifi_manager: ESPSPI_WiFiManager, device_connection_string: str, token_expires: int = 21600, logger: logging = None):
        self._wifi_manager = wifi_manager
        self._token_expires = token_expires
        self._logger = logger if logger is not None else logging.getLogger("log")

        connection_string_values = {}

        try:
            cs_args = device_connection_string.split(DELIMITER)
            connection_string_values = dict(arg.split(VALUE_SEPARATOR, 1) for arg in cs_args)
        except (ValueError, AttributeError):
            raise ValueError("Connection string is required and should not be empty or blank and must be supplied as a string")

        if len(cs_args) != len(connection_string_values):
            raise ValueError("Invalid Connection String - Unable to parse")

        _validate_keys(connection_string_values)

        self._hostname = connection_string_values[HOST_NAME]
        self._device_id = connection_string_values[DEVICE_ID]
        self._shared_access_key = connection_string_values[SHARED_ACCESS_KEY]

        self._logger.debug("Hostname: " + self._hostname)
        self._logger.debug("Device Id: " + self._device_id)
        self._logger.debug("Shared Access Key: " + self._shared_access_key)

        self._on_connection_status_changed = None
        self._on_direct_method_invoked = None
        self._on_cloud_to_device_message_received = None
        self._on_device_twin_desired_updated = None
        self._on_device_twin_reported_updated = None

        self._mqtt = None

    @property
    def on_connection_status_changed(self):
        """Event fired when the connection status changes
        """
        return self._on_connection_status_changed

    @on_connection_status_changed.setter
    def on_connection_status_changed(self, new_on_connection_status_changed):
        """Event fired when the connection status changes
        """
        self._on_connection_status_changed = new_on_connection_status_changed

    @property
    def on_direct_method_invoked(self):
        """Event fired when a direct method is invoked
        """
        return self._on_direct_method_invoked

    @on_direct_method_invoked.setter
    def on_direct_method_invoked(self, new_on_direct_method_invoked):
        """Event fired when a direct method is invoked
        """
        self._on_direct_method_invoked = new_on_direct_method_invoked

    @property
    def on_cloud_to_device_message_received(self):
        """Event fired when a cloud to device message is received
        """
        return self._on_cloud_to_device_message_received

    @on_cloud_to_device_message_received.setter
    def on_cloud_to_device_message_received(self, new_on_cloud_to_device_message_received):
        """Event fired when a cloud to device message is received
        """
        self._on_cloud_to_device_message_received = new_on_cloud_to_device_message_received

    @property
    def on_device_twin_desired_updated(self):
        """Event fired when the desired properties on a device twin are updated
        """
        return self._on_device_twin_desired_updated

    @on_device_twin_desired_updated.setter
    def on_device_twin_desired_updated(self, new_on_device_twin_desired_updated):
        """Event fired when the desired properties on a device twin are updated
        """
        self._on_device_twin_desired_updated = new_on_device_twin_desired_updated

        if self._mqtt is not None:
            self._mqtt.subscribe_to_twins()

    @property
    def on_device_twin_reported_updated(self):
        """Event fired when the reported properties on a device twin are updated
        """
        return self._on_device_twin_reported_updated

    @on_device_twin_reported_updated.setter
    def on_device_twin_reported_updated(self, new_on_device_twin_reported_updated):
        """Event fired when the reported properties on a device twin are updated
        """
        self._on_device_twin_reported_updated = new_on_device_twin_reported_updated

        if self._mqtt is not None:
            self._mqtt.subscribe_to_twins()

    def connect(self):
        """Connects to Azure IoT Central
        """
        self._mqtt = IoTMQTT(
            self, self._wifi_manager, self._hostname, self._device_id, self._shared_access_key, self._token_expires, self._logger
        )
        self._mqtt.connect()

        if self._on_device_twin_desired_updated is not None or self._on_device_twin_reported_updated is not None:
            self._mqtt.subscribe_to_twins()

    def disconnect(self):
        """Disconnects from the MQTT broker
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        self._mqtt.disconnect()

    def is_connected(self) -> bool:
        """Gets if there is an open connection to the MQTT broker
        """
        if self._mqtt is not None:
            return self._mqtt.is_connected()

        return False

    def loop(self):
        """Listens for MQTT messages
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        self._mqtt.loop()

    def send_device_to_cloud_message(self, message, system_properties=None):
        """Sends a device to cloud message to the IoT Hub
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        self._mqtt.send_device_to_cloud_message(message, system_properties)

    def update_twin(self, patch):
        """Updates the reported properties in the devices device twin
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        if isinstance(patch, dict):
            patch = json.dumps(patch)

        self._mqtt.send_twin_patch(patch)
