# SPDX-FileCopyrightText: 2020 Jim Bennett for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Elena Horton for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_azureiot`
================================================================================

Microsoft Azure IoT for CircuitPython

* Author(s): Jim Bennett, Elena Horton

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

**ESP32SPI Peripheral Networking**

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's ESP32SPI Networking library: https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI

**Native Networking**

* CircuitPython's Wifi Module: https://docs.circuitpython.org/en/latest/shared-bindings/wifi/index.html
* Adafruit's CircuitPython Requests Library: https://github.com/adafruit/Adafruit_CircuitPython_Requests/
"""

from .iot_error import IoTError
from .iot_mqtt import IoTResponse
from .iotcentral_device import IoTCentralDevice
from .iothub_device import IoTHubDevice

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_AzureIoT.git"

__all__ = ["IoTHubDevice", "IoTCentralDevice", "IoTResponse", "IoTError"]
