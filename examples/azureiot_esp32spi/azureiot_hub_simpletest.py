# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import json
import random
import time
from os import getenv

import adafruit_connection_manager
import board
import busio
import neopixel
import rtc
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
from digitalio import DigitalInOut

# Get WiFi details and Azure keys, ensure these are setup in settings.toml
ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")
device_connection_string = getenv("device_connection_string")

# ESP32 Setup
try:
    esp32_cs = DigitalInOut(board.ESP_CS)
    esp32_ready = DigitalInOut(board.ESP_BUSY)
    esp32_reset = DigitalInOut(board.ESP_RESET)
except AttributeError:
    esp32_cs = DigitalInOut(board.D13)
    esp32_ready = DigitalInOut(board.D11)
    esp32_reset = DigitalInOut(board.D12)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

"""Use below for Most Boards"""
status_pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)  # Uncomment for Most Boards
"""Uncomment below for ItsyBitsy M4"""
# status_pixel = dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1, brightness=0.2)
# Uncomment below for an externally defined RGB LED
# import adafruit_rgbled
# from adafruit_esp32spi import PWMOut
# RED_LED = PWMOut.PWMOut(esp, 26)
# GREEN_LED = PWMOut.PWMOut(esp, 27)
# BLUE_LED = PWMOut.PWMOut(esp, 25)
# status_pixel = adafruit_rgbled.RGBLED(RED_LED, BLUE_LED, GREEN_LED)
wifi = adafruit_esp32spi_wifimanager.WiFiManager(esp, ssid, password, status_pixel=status_pixel)

print("Connecting to WiFi...")

wifi.connect()

print("Connected to WiFi!")

print("Getting the time...")

# get_time will raise ValueError if the time isn't available yet so loop until
# it works.
now_utc = None
while now_utc is None:
    try:
        now_utc = time.localtime(esp.get_time()[0])
    except ValueError:
        pass
rtc.RTC().datetime = now_utc

print("Time:", str(time.time()))

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
from adafruit_azureiot import IoTHubDevice

pool = adafruit_connection_manager.get_radio_socketpool(esp)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp)
# Create an IoT Hub device client and connect
device = IoTHubDevice(pool, ssl_context, device_connection_string)

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
            message_counter += 1

        # Poll every second for messages from the cloud
        device.loop()
    except (ValueError, RuntimeError) as e:
        print("Connection error, reconnecting\n", str(e))
        wifi.reset()
        wifi.connect()
        device.reconnect()
        continue
    time.sleep(1)
