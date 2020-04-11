"""Connectivity to Azure IoT Central
"""

import json
import time
from adafruit_esp32spi.adafruit_esp32spi_wifimanager import ESPSPI_WiFiManager
from device_registration import DeviceRegistration
from iot_error import IoTError
from iot_mqtt import IoTMQTT, IoTMQTTCallback, IoTResponse
import adafruit_logging as logging


class IoTCentralDevice(IoTMQTTCallback):
    """A device client for the Azure IoT Central service
    """

    def connection_status_change(self, connected: bool) -> None:
        """Called when the connection status changes
        """
        if self.on_connection_status_changed is not None:
            # pylint: disable=E1102
            self.on_connection_status_changed(connected)

    # pylint: disable=W0613, R0201
    def direct_method_called(self, method_name: str, data) -> IoTResponse:
        """Called when a direct method is invoked
        """
        if self.on_command_executed is not None:
            # pylint: disable=E1102
            return self.on_command_executed(method_name, data)

        raise IoTError("on_command_executed not set")

    def device_twin_desired_updated(self, desired_property_name: str, desired_property_value, desired_version: int) -> None:
        """Called when the device twin is updated
        """
        if self.on_property_changed is not None:
            # pylint: disable=E1102
            self.on_property_changed(desired_property_name, desired_property_value, desired_version)

        # when a desired property changes, update the reported to match to keep them in sync
        self.send_property(desired_property_name, desired_property_value)

    def device_twin_reported_updated(self, reported_property_name: str, reported_property_value, reported_version: int) -> None:
        """Called when the device twin is updated
        """
        if self.on_property_changed is not None:
            # pylint: disable=E1102
            self.on_property_changed(reported_property_name, reported_property_value, reported_version)

    # pylint: disable=R0913
    def __init__(
        self, wifi_manager: ESPSPI_WiFiManager, id_scope: str, device_id: str, key: str, token_expires: int = 21600, logger: logging = None
    ):
        super(IoTCentralDevice, self).__init__()
        self._wifi_manager = wifi_manager
        self._id_scope = id_scope
        self._device_id = device_id
        self._key = key
        self._token_expires = token_expires
        self._logger = logger
        self._device_registration = None
        self._mqtt = None

        self.on_connection_status_changed = None
        self.on_command_executed = None
        self.on_property_changed = None

    def connect(self):
        """Connects to Azure IoT Central
        """
        self._device_registration = DeviceRegistration(self._wifi_manager, self._id_scope, self._device_id, self._key, self._logger)

        token_expiry = int(time.time() + self._token_expires)
        hostname = self._device_registration.register_device(token_expiry)
        self._mqtt = IoTMQTT(self, hostname, self._device_id, self._key, self._token_expires, self._logger)

        self._mqtt.connect()

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

    def send_property(self, property_name, data):
        """Updates the value of a writable property
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        patch_json = {property_name: data}
        patch = json.dumps(patch_json)
        self._mqtt.send_twin_patch(patch)

    def send_telemetry(self, data):
        """Sends telemetry to the IoT Central app
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        if isinstance(data, dict):
            data = json.dumps(data)

        self._mqtt.send_device_to_cloud_message(data)
