# SPDX-FileCopyrightText: 2020 Jim Bennett for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Elena Horton for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`device_registration`
=====================

Handles registration of IoT Central devices, and gets the hostname to use when connecting
to IoT Central over MQTT

* Author(s): Jim Bennett, Elena Horton
"""

import json
import ssl
import time

import adafruit_logging as logging
from adafruit_logging import Logger
import adafruit_minimqtt.adafruit_minimqtt as MQTT

from . import constants
from .quote import quote
from .keys import compute_derived_symmetric_key


class DeviceRegistrationError(Exception):
    """
    An error from the device registration
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class DeviceRegistration:
    """
    Handles registration of IoT Central devices, and gets the hostname to use when connecting
    to IoT Central over MQTT
    """

    # pylint: disable=R0913
    def __init__(
        self,
        socket,
        iface,
        id_scope: str,
        device_id: str,
        device_sas_key: str,
        logger: Logger = None,
    ):
        """Creates an instance of the device registration service

        :param socket: The network socket
        :param str id_scope: The ID scope of the device to register
        :param str device_id: The device ID of the device to register
        :param str device_sas_key: The primary or secondary key of the device to register
        :param adafruit_logging.Logger logger: The logger to use to log messages
        """
        self._id_scope = id_scope
        self._device_id = device_id
        self._device_sas_key = device_sas_key
        self._logger = logger if logger is not None else logging.getLogger("log")

        self._mqtt = None
        self._auth_response_received = False
        self._operation_id = None
        self._hostname = None

        self._socket = socket
        self._iface = iface

    # pylint: disable=W0613
    # pylint: disable=C0103
    def _on_connect(self, client, userdata, _, rc) -> None:
        self._logger.info(
            f"- device_registration :: _on_connect :: rc = {rc}, userdata = {userdata}"
        )

        self._auth_response_received = True

    # pylint: disable=W0613
    def _handle_dps_update(self, client, topic: str, msg: str) -> None:
        self._logger.info(f"Received registration results on topic {topic} - {msg}")
        message = json.loads(msg)

        if topic.startswith("$dps/registrations/res/202"):
            # Get the retry after and wait for that before responding
            parts = str.split(topic, "retry-after=")
            waittime = int(parts[1])

            self._logger.debug(f"Retrying after {waittime}s")

            time.sleep(waittime)
            self._operation_id = message["operationId"]
        elif topic.startswith("$dps/registrations/res/200"):
            self._hostname = message["registrationState"]["assignedHub"]

    def _connect_to_mqtt(self) -> None:
        self._mqtt.on_connect = self._on_connect

        self._mqtt.connect()

        self._logger.info(
            " - device_registration :: connect :: created mqtt client. connecting.."
        )
        while not self._auth_response_received:
            self._mqtt.loop()

        self._logger.info(
            f" - device_registration :: connect :: on_connect must be fired. Connected ? {self._mqtt.is_connected()}"
        )

        if not self._mqtt.is_connected():
            raise DeviceRegistrationError("Cannot connect to MQTT")

    def _start_registration(self) -> None:
        self._mqtt.add_topic_callback(
            "$dps/registrations/res/#", self._handle_dps_update
        )
        self._mqtt.subscribe("$dps/registrations/res/#")

        message = json.dumps({"registrationId": self._device_id})

        self._mqtt.publish(
            f"$dps/registrations/PUT/iotdps-register/?$rid={self._device_id}", message
        )

        retry = 0

        while self._operation_id is None and retry < 10:
            time.sleep(1)
            retry += 1
            self._mqtt.loop()

        if self._operation_id is None:
            raise DeviceRegistrationError(
                "Cannot register device - no response from broker for registration result"
            )

    def _wait_for_operation(self) -> None:
        message = json.dumps({"operationId": self._operation_id})
        self._mqtt.publish(
            f"$dps/registrations/GET/iotdps-get-operationstatus/?$rid={self._device_id}&operationId={self._operation_id}",
            message,
        )

        retry = 0

        while self._hostname is None and retry < 10:
            time.sleep(1)
            retry += 1
            self._mqtt.loop()

        if self._hostname is None:
            raise DeviceRegistrationError(
                "Cannot register device - no response from broker for operation status"
            )

    def register_device(self, expiry: int) -> str:
        """
        Registers the device with the IoT Central device registration service.
        Returns the hostname of the IoT hub to use over MQTT

        :param int expiry: The expiry time for the registration
        :returns: The underlying IoT Hub that this device should connect to
        :rtype: str
        :raises DeviceRegistrationError: if the device cannot be registered successfully
        :raises RuntimeError: if the internet connection is not responding or is unable to connect
        """

        username = f"{self._id_scope}/registrations/{self._device_id}/api-version={constants.DPS_API_VERSION}"

        # pylint: disable=C0103
        sr = self._id_scope + "%2Fregistrations%2F" + self._device_id
        sig_no_encode = compute_derived_symmetric_key(
            self._device_sas_key, sr + "\n" + str(expiry)
        )
        sig_encoded = quote(sig_no_encode, "~()*!.'")
        auth_string = f"SharedAccessSignature sr={sr}&sig={sig_encoded}&se={expiry}&skn=registration"

        MQTT.set_socket(self._socket, self._iface)

        self._mqtt = MQTT.MQTT(
            broker=constants.DPS_END_POINT,
            username=username,
            password=auth_string,
            port=8883,
            keep_alive=120,
            client_id=self._device_id,
            ssl_context=ssl.create_default_context(),
        )

        self._mqtt.enable_logger(logging, self._logger.getEffectiveLevel())

        self._connect_to_mqtt()
        self._start_registration()
        self._wait_for_operation()

        self._mqtt.disconnect()

        return str(self._hostname)
