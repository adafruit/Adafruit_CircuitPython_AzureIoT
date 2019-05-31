# The MIT License (MIT)
#
# Copyright (c) 2019 Brent Rubell for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_azureiot`
================================================================================

Microsoft Azure IoT for CircuitPython

* Author(s): Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's ESP32SPI library: https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI
"""

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_AzureIoT.git"

AZ_API_VER = "2018-06-30" # Azure URI API Version Identifier
AZURE_HTTP_ERROR_CODES = [400, 401, 404, 403, 412, 429, 500] # Azure HTTP Status Codes

class IOT_Hub:
    """
    Provides access to a Microsoft Azure IoT Hub.
    https://docs.microsoft.com/en-us/rest/api/iothub/
    """
    def __init__(self, wifi_manager, iot_hub_name, sas_token, device_id):
        """ Creates an instance of an Azure IoT Hub Client.
        :param wifi_manager: WiFiManager object from ESPSPI_WiFiManager.
        :param str iot_hub_name: Name of your IoT Hub.
        :param str sas_token: Azure IoT Hub SAS Token Identifier.
        :param str device_id: Unique Azure IoT Device Identifier.
        """
        _wifi_type = str(type(wifi_manager))
        if 'ESPSPI_WiFiManager' in _wifi_type:
            self._wifi = wifi_manager
        else:
            raise TypeError("This library requires a WiFiManager object.")
        self._iot_hub_url = "https://{0}.azure-devices.net".format(iot_hub_name)
        self._sas_token = sas_token
        self._device_id = device_id
        self._azure_header = {"Authorization":self._sas_token}

    @property
    def device_id(self):
        """Returns the current device identifier"""
        return self._device_id

    @device_id.setter
    def device_id(self, device_identifier):
        """Sets the current device identifier
        :param str device_identifier: Unique device identifier.
        """
        self._device_id = device_identifier

    @staticmethod
    def _parse_http_status(status_code, status_reason):
        """Parses status code, throws error based on Azure IoT Common Error Codes.
        :param int status_code: HTTP status code.
        :param str status_reason: Description of HTTP status.
        """
        for error in AZURE_HTTP_ERROR_CODES:
            if error == status_code:
                raise TypeError("Error {0}: {1}".format(status_code, status_reason))

    # Cloud-to-Device Messaging
    def get_hub_message(self):
        """Returns a message from a Microsoft Azure IoT Hub (Cloud-to-Device).
        Returns None if the message queue is empty.
        NOTE: HTTP Cloud-to-Device messages are throttled. Poll every 25+ minutes.
        """
        reject_message = True
        # get a device-bound notification
        path = "{0}/devices/{1}/messages/deviceBound?api-version={2}".format(self._iot_hub_url,
                                                                             self._device_id,
                                                                             AZ_API_VER)
        data = self._get(path, is_c2d=True)
        if data == 204: # device's message queue is empty
            return None
        etag = data[1]['etag']
        if etag: # either complete or nack the message
            reject_message = False
            path_complete = "{0}/devices/{1}/messages/deviceBound/{2}?api-version={3}".format(
                self._iot_hub_url, self._device_id, etag.strip('\'"'), AZ_API_VER)
            if reject_message:
                path_complete += '&reject'
            del_status = self._delete(path_complete)
        if del_status == 204:
            return data[0]
        return None

    # Device-to-Cloud Messaging
    def send_device_message(self, message):
        """Sends a device-to-cloud message.
        :param string message: Message to send to Azure IoT.
        """
        path = "{0}/devices/{1}/messages/events?api-version={2}".format(self._iot_hub_url,
                                                                        self._device_id, AZ_API_VER)
        self._post(path, message, return_response=False)

    # Device Twin
    def get_device_twin(self):
        """Returns the device's device twin information in JSON format.
        """
        path = "{0}/twins/{1}?api-version={2}".format(self._iot_hub_url,
                                                      self._device_id, AZ_API_VER)
        return self._get(path)

    def update_device_twin(self, properties):
        """Updates tags and desired properties of the device's device twin.
        :param str properties: Device Twin Properties
        (https://docs.microsoft.com/en-us/rest/api/iothub/service/updatetwin#twinproperties)
        """
        path = "{0}/twins/{1}?api-version={2}".format(self._iot_hub_url,
                                                      self._device_id, AZ_API_VER)
        return self._patch(path, properties)

    def replace_device_twin(self, properties):
        """Replaces tags and desired properties of a device twin.
        :param str properties: Device Twin Properties.
        """
        path = "{0}/twins/{1}?api-version-{2}".format(self._iot_hub_url,
                                                      self._device_id, AZ_API_VER)
        return self._put(path, properties)

    # IoT Hub Service
    def get_devices(self):
        """Enumerate devices from the identity registry of the IoT Hub.
        """
        path = "{0}/devices/?api-version={1}".format(self._iot_hub_url, AZ_API_VER)
        return self._get(path)

    def get_device(self):
        """Gets device information from the identity
        registry of an IoT Hub.
        """
        path = "{0}/devices/{1}?api-version={2}".format(self._iot_hub_url,
                                                        self._device_id, AZ_API_VER)
        return self._get(path)

    # HTTP Helper Methods
    def _post(self, path, payload, return_response=True):
        """HTTP POST
        :param str path: Formatted Azure IOT Hub Path.
        :param str payload: JSON-formatted Data Payload.
        """
        response = self._wifi.post(
            path,
            json=payload,
            headers=self._azure_header)
        self._parse_http_status(response.status_code, response.reason)
        if return_response:
            return response.json()
        return response.text

    def _get(self, path, is_c2d=False):
        """HTTP GET
        :param str path: Formatted Azure IOT Hub Path.
        :param bool is_c2d: Cloud-to-device get request.
        """
        response = self._wifi.get(
            path,
            headers=self._azure_header)
        status_code = response.status_code
        if is_c2d:
            if status_code == 200:
                data = response.text
                headers = response.headers
                response.close()
                return data, headers
            response.close()
            return status_code
        json = response.json()
        response.close()
        return json

    def _delete(self, path, etag=None):
        """HTTP DELETE
        :param str path: Formatted Azure IOT Hub Path.
        """
        if etag:
            data_headers = {"Authorization":self._sas_token, "If-Match":'"%s"'%etag}
        else:
            data_headers = self._azure_header
        response = self._wifi.delete(
            path,
            headers=data_headers)
        self._parse_http_status(response.status_code, response.reason)
        status_code = response.status_code
        response.close()
        return status_code

    def _patch(self, path, payload):
        """HTTP PATCH
        :param str path: Formatted Azure IOT Hub Path.
        :param str payload: JSON-formatted payload.
        """
        response = self._wifi.patch(
            path,
            json=payload,
            headers=self._azure_header)
        self._parse_http_status(response.status_code, response.reason)
        json_data = response.json()
        response.close()
        return json_data

    def _put(self, path, payload=None):
        """HTTP PUT
        :param str path: Formatted Azure IOT Hub Path.
        :param str payload: JSON-formatted payload.
        """
        response = self._wifi.put(
            path,
            json=payload,
            headers=self._azure_header)
        self._parse_http_status(response.status_code, response.reason)
        json_data = response.json()
        response.close()
        return json_data
