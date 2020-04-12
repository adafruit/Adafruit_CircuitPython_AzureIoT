import json
import random
import time
import board
import busio
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
import neopixel

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# ESP32 Setup
try:
    esp32_cs = DigitalInOut(board.ESP_CS)
    esp32_ready = DigitalInOut(board.ESP_BUSY)
    esp32_reset = DigitalInOut(board.ESP_RESET)
except AttributeError:
    esp32_cs = DigitalInOut(board.D9)
    esp32_ready = DigitalInOut(board.D10)
    esp32_reset = DigitalInOut(board.D5)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)  # Uncomment for Most Boards
"""Uncomment below for ItsyBitsy M4"""
# status_light = dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1, brightness=0.2)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)

# You will need an Azure subscription to create an IoT Hub
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
# Once you have a hub and a device, copy the device promary connection string.
# Add it to the secrets.py file in an entry called DeviceConnectionString

from adafruit_azureiot import IoTHubDevice

# Create an IoT Hub device client and connect
device = IoTHubDevice(wifi, secrets["DeviceConnectionString"])
device.connect()

message_counter = 0

while True:
    # Send a device to cloud message every minute
    # You can see the overview of messages sent from the device in the Overview tab
    # of the IoT Hub in the Azure Portal
    if message_counter > 60:
        message = {"Temperature": random.randint(0, 50)}
        device.send_device_to_cloud_message(json.dumps(message))
        message_counter = 0

    message_counter = message_counter + 1

    # Poll every second for messages from the cloud
    device.loop()

    time.sleep(1)
