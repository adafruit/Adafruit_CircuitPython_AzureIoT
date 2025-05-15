# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
from os import getenv

import adafruit_connection_manager
import adafruit_ntp
import rtc
import wifi

from adafruit_azureiot import IoTHubDevice
from adafruit_azureiot.iot_mqtt import IoTResponse

# Get WiFi details, ensure these are setup in settings.toml
ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")
device_connection_string = getenv("device_connection_string")

print("Connecting to WiFi...")
wifi.radio.connect(ssid, password)

pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)

print("Connected to WiFi!")

if time.localtime().tm_year < 2022:
    print("Setting System Time in UTC")
    ntp = adafruit_ntp.NTP(pool, tz_offset=0)

    # NOTE: This changes the system time so make sure you aren't assuming that time
    # doesn't jump.
    rtc.RTC().datetime = ntp.datetime
else:
    print("Year seems good, skipping set time.")

# You will need an Azure subscription to create an Azure IoT Hub resource
#
# If you don't have an Azure subscription:
#
# If you are a student, head to https://aka.ms/FreeStudentAzure and sign up, validating with your
#  student email address. This will give you $100 of Azure credit and free tiers of a load of
#  service, renewable each year you are a student
#
# If you are not a student, head to https://aka.ms/FreeAz and sign up to get $200 of credit for 30
#  days, as well as free tiers of a load of services
#
# Create an Azure IoT Hub and an IoT device in the Azure portal here:
# https://aka.ms/AzurePortalHome.
# Instructions to create an IoT Hub and device are here: https://aka.ms/CreateIoTHub
#
# The free tier of IoT Hub allows up to 8,000 messages a day, so try not to send messages too often
# if you are using the free tier
#
# Once you have a hub and a device, copy the device primary connection string.
# Add it to the settings.toml file in an entry called device_connection_string
#
# The adafruit-circuitpython-azureiot library depends on the following libraries:
#
# From the Adafruit CircuitPython Bundle https://github.com/adafruit/Adafruit_CircuitPython_Bundle:
# * adafruit-circuitpython-minimqtt


# Create an IoT Hub device client and connect
device = IoTHubDevice(pool, ssl_context, device_connection_string)


# Subscribe to direct method calls
# To invoke a method on the device, select it in the Azure Portal, select Direct Method,
# fill in the method name and payload, then select Invoke Method
# Direct method handlers need to return a response to show if the method was handled
# successfully or not, returning an HTTP status code and message
def direct_method_invoked(method_name: str, payload) -> IoTResponse:
    print("Received direct method", method_name, "with data", str(payload))
    # return a status code and message to indicate if the direct method was handled correctly
    return IoTResponse(200, "OK")


# Subscribe to the direct method invoked event
device.on_direct_method_invoked = direct_method_invoked
print("Connecting to Azure IoT Hub...")

# Connect to IoT Central
device.connect()

print("Connected to Azure IoT Hub!")

while True:
    try:
        # Poll every second for messages from the cloud
        device.loop()
    except (ValueError, RuntimeError) as e:
        print("Connection error, reconnecting\n", str(e))
        # If we lose connectivity, reset the wifi and reconnect
        wifi.radio.enabled = False
        wifi.radio.enabled = True
        wifi.radio.connect(ssid, password)
        device.reconnect()
        continue

    time.sleep(1)
