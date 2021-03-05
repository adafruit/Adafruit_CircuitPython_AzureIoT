# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
#
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
# Create an Azure IoT Hub and an IoT device in the Azure portal here: https://aka.ms/AzurePortalHome.
# Instructions to create an IoT Hub and device are here: https://aka.ms/CreateIoTHub
#
# The free tier of IoT Hub allows up to 8,000 messages a day, so try not to send messages too often
# if you are using the free tier
#
# Once you have a hub and a device, copy the device primary connection string.
# Add it to the secrets.py file in an entry called device_connection_string
#
# The adafruit-circuitpython-azureiot library depends on the following libraries:
#
# From the Adafruit CircuitPython Bundle (https://github.com/adafruit/Adafruit_CircuitPython_Bundle):
# * adafruit-circuitpython-minimqtt
# * adafruit-circuitpython-requests

import json
import random
import rtc
import socketpool
import ssl
import time
import wifi

from adafruit_azureiot import IoTHubDevice
import adafruit_requests

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])


print("Getting the time...")
print("Setting System Time in UTC")
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
response = requests.get("https://io.adafruit.com/api/v2/time/seconds")
if response:
    if response.status_code == 200:
        r = rtc.RTC()
        r.datetime = time.localtime(int(response.text))
        print(f"System Time: {r.datetime}")
    else:
        print("Setting time failed")


# Create an IoT Hub device client and connect

# Original Code
# device = IoTHubDevice(socket, esp, secrets["device_connection_string"])

device = IoTHubDevice(
    pool, ssl.create_default_context(), secrets["device_connection_string"]
)

print("Connecting to Azure IoT Hub...")

# Connect to IoT Central
device.connect()

print("Connected to Azure IoT Hub!")

message_counter = 60

while True:
    try:
        # Send a device to cloud message every minute
        # You can see the overview of messages sent from the device in the Overview tab
        # of the IoT Hub in the Azure Portal
        if message_counter >= 60:
            message = {"Temperature": random.randint(0, 50)}
            device.send_device_to_cloud_message(json.dumps(message))
            message_counter = 0
        else:
            message_counter = message_counter + 1

        # Poll every second for messages from the cloud
        device.loop()
    except (ValueError, RuntimeError) as e:
        print("Connection error, reconnecting\n", str(e))
        # If we lose connectivity, reset the wifi and reconnect
        wifi.reset()
        wifi.connect()
        device.reconnect()
        continue

    time.sleep(1)
