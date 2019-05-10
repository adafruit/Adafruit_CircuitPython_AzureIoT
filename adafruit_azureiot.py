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
`Adafruit_AzureIoT`
================================================================================

Access to Microsoft Azure IoT from CircuitPython


* Author(s): Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's ESP32SPI library: https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI
"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_AzureIoT.git"

AZURE_API_VERSION = "2018-06-30" # Azure URI API Version Identifier

class iot_hub:
    """
    Provides access to Azure IoT Hub.
    https://docs.microsoft.com/en-us/rest/api/iothub/
    """
    def __init__(self, wifi_manager, iot_hub_name, sas_token):
        """ Creates an instance of an Azure IoT Hub Client.
        :param wifi_manager: WiFiManager object from ESPSPI_WiFiManager
        :param str iot_hub_name: Name of your IoT Hub
        :param str sas_token: SAS Token Identifier
                                (https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-devguide-security)
        """
        wifi_type = str(type(wifi_manager))
        if 'ESPSPI_WiFiManager' in wifi_type:
            self.wifi = wifi_manager
        else:
            raise TypeError("This library requires a WiFiManager object.")
        self._iot_hub_url = "https://{0}.azure-devices.net".format(iot_hub_name)
        self._sas_token = sas_token
        self.azure_header = {"Authorization":'SharedAccessSignature sr=azure-airlift-test-hub.azure-devices.net&sig=4WbbY2AWdwJJzsxKKNliRnQ5mzX87JW8ToEoc%2FezuoU%3D&skn=iothubowner&se=1557550171'}

    # HTTP Request Methods
    def _post(self, path, payload):
        response = self.wifi.post(
            path,
            json=payload,
            headers=self.azure_header)
        return response.json()

    def _get(self, path, payload):
        response = self.wifi.get(
            path,
            json=payload,
            headers=self.azure_header)
        return response.json()

    # Device Messaging 
    # D2C: Device-to-Cloud
    def send_device_message(self, device_id, message):
        """Sends a device-to-cloud message.
        :param string device_id: Device Identifier.
        :param string message: Message.
        """
        path = "{0}/devices/{1}/messages/events?api-version={2}".format(self._iot_hub_url, device_id, AZURE_API_VERSION)
        self._post(path, message)

    # C2D: Cloud-to-Device

    # IoT Hub Service
    def get_devices(self):
        """Retrieve devices from the identity registry of your IoT hub.
        """
        path = "https://{0}/devices/?api-version={1}".format(self._iot_hub_url, AZURE_API_VERSION)
        self._get(path)


    # IoT Hub Resource Provider