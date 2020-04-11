"""
Device Registration
=====================

Handles registration of IoT Central devices, and gets the hostname to use when connecting
to IoT Central over MQTT
"""

import gc
import json
import time
import circuitpython_base64 as base64
import circuitpython_hmac as hmac
import circuitpython_parse as parse
from adafruit_esp32spi.adafruit_esp32spi_wifimanager import ESPSPI_WiFiManager
import adafruit_logging as logging
from adafruit_logging import Logger
import adafruit_hashlib as hashlib
from . import constants


AZURE_HTTP_ERROR_CODES = [400, 401, 404, 403, 412, 429, 500]  # Azure HTTP Status Codes


class DeviceRegistrationError(Exception):
    """
    An error from the device registration
    """

    def __init__(self, message):
        super(DeviceRegistrationError, self).__init__(message)
        self.message = message


class DeviceRegistration:
    """
    Handles registration of IoT Central devices, and gets the hostname to use when connecting
    to IoT Central over MQTT
    """

    _dps_endpoint = constants.DPS_END_POINT
    _dps_api_version = constants.DPS_API_VERSION
    _loop_interval = 2

    @staticmethod
    def _parse_http_status(status_code, status_reason):
        """Parses status code, throws error based on Azure IoT Common Error Codes.
        :param int status_code: HTTP status code.
        :param str status_reason: Description of HTTP status.
        """
        for error in AZURE_HTTP_ERROR_CODES:
            if error == status_code:
                raise TypeError("Error {0}: {1}".format(status_code, status_reason))

    def __init__(self, wifi_manager: ESPSPI_WiFiManager, id_scope: str, device_id: str, key: str, logger: Logger = None):
        """Creates an instance of the device registration
        :param wifi_manager: WiFiManager object from ESPSPI_WiFiManager.
        :param str id_scope: The ID scope of the device to register
        :param str device_id: The device ID of the device to register
        :param str key: The primary or secondary key of the device to register
        :param adafruit_logging.Logger key: The primary or secondary key of the device to register
        """
        wifi_type = str(type(wifi_manager))
        if "ESPSPI_WiFiManager" not in wifi_type:
            raise TypeError("This library requires a WiFiManager object.")

        self._wifi_manager = wifi_manager
        self._id_scope = id_scope
        self._device_id = device_id
        self._key = key
        self._logger = logger if logger is not None else logging.getLogger("log")

    @staticmethod
    def compute_derived_symmetric_key(secret, reg_id):
        """Computes a derived symmetric key from a secret and a message
        """
        secret = base64.b64decode(secret)
        return base64.b64encode(hmac.new(secret, msg=reg_id.encode("utf8"), digestmod=hashlib.sha256).digest())

    def _loop_assign(self, operation_id, headers) -> str:
        uri = "https://%s/%s/registrations/%s/operations/%s?api-version=%s" % (
            self._dps_endpoint,
            self._id_scope,
            self._device_id,
            operation_id,
            self._dps_api_version,
        )
        self._logger.info("- iotc :: _loop_assign :: " + uri)
        target = parse.urlparse(uri)

        response = self.__run_get_request_with_retry(target.geturl(), headers)

        try:
            data = response.json()
        except Exception as error:
            err = "ERROR: " + str(error) + " => " + str(response)
            self._logger.error(err)
            raise DeviceRegistrationError(err)

        loop_try = 0

        if data is not None and "status" in data:
            if data["status"] == "assigning":
                time.sleep(self._loop_interval)
                if loop_try < 20:
                    loop_try = loop_try + 1
                    return self._loop_assign(operation_id, headers)

                err = "ERROR: Unable to provision the device."
                self._logger.error(err)
                raise DeviceRegistrationError(err)

            if data["status"] == "assigned":
                state = data["registrationState"]
                return state["assignedHub"]
        else:
            data = str(data)

        err = "DPS L => " + str(data)
        self._logger.error(err)
        raise DeviceRegistrationError(err)

    def __run_put_request_with_retry(self, url, body, headers):
        retry = 0
        response = None

        while True:
            gc.collect()
            try:
                self._logger.debug("Trying to send...")
                response = self._wifi_manager.put(url, json=body, headers=headers)
                self._logger.debug("Sent!")
                break
            except RuntimeError as runtime_error:
                self._logger.info("Could not send data, retrying after 0.5 seconds: " + str(runtime_error))
                retry = retry + 1

                if retry >= 10:
                    self._logger.error("Failed to send data")
                    raise

                time.sleep(0.5)
                continue

        gc.collect()
        return response

    def __run_get_request_with_retry(self, url, headers):
        retry = 0
        response = None

        while True:
            gc.collect()
            try:
                self._logger.debug("Trying to send...")
                response = self._wifi_manager.get(url, headers=headers)
                self._logger.debug("Sent!")
                break
            except RuntimeError as runtime_error:
                self._logger.info("Could not send data, retrying after 0.5 seconds: " + str(runtime_error))
                retry = retry + 1

                if retry >= 10:
                    self._logger.error("Failed to send data")
                    raise

                time.sleep(0.5)
                continue

        gc.collect()
        return response

    def register_device(self, expiry: int) -> str:
        """
        Registers the device with the IoT Central device registration service.
        Returns the hostname of the IoT hub to use over MQTT
        :param str expiry: The expiry time
        """
        # pylint: disable=c0103
        sr = self._id_scope + "%2Fregistrations%2F" + self._device_id
        sig_no_encode = DeviceRegistration.compute_derived_symmetric_key(self._key, sr + "\n" + str(expiry))
        sig_encoded = parse.quote(sig_no_encode, "~()*!.'")
        auth_string = "SharedAccessSignature sr=" + sr + "&sig=" + sig_encoded + "&se=" + str(expiry) + "&skn=registration"

        headers = {
            "content-type": "application/json; charset=utf-8",
            "user-agent": "iot-central-client/1.0",
            "Accept": "*/*",
        }

        if auth_string is not None:
            headers["authorization"] = auth_string

        body = {"registrationId": self._device_id}

        uri = "https://%s/%s/registrations/%s/register?api-version=%s" % (
            self._dps_endpoint,
            self._id_scope,
            self._device_id,
            self._dps_api_version,
        )
        target = parse.urlparse(uri)

        self._logger.info("Connecting...")
        self._logger.info("URL: " + target.geturl())
        self._logger.info("body: " + json.dumps(body))
        print("headers: " + json.dumps(headers))

        response = self.__run_put_request_with_retry(target.geturl(), body, headers)

        data = None
        try:
            data = response.json()
        except Exception as e:
            err = "ERROR: non JSON is received from " + self._dps_endpoint + " => " + str(response) + " .. message : " + str(e)
            self._logger.error(err)
            raise DeviceRegistrationError(err)

        if "errorCode" in data:
            err = "DPS => " + str(data)
            self._logger.error(err)
            raise DeviceRegistrationError(err)

        time.sleep(1)
        return self._loop_assign(data["operationId"], headers)
