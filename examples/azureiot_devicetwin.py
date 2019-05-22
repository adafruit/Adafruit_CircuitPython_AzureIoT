import board
import busio
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
import neopixel
from adafruit_azureiot import IOT_Hub

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
status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2) # Uncomment for Most Boards
"""Uncomment below for ItsyBitsy M4"""
#status_light = dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1, brightness=0.2)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)

# Create an instance of the Azure IoT Hub
hub = IOT_Hub(wifi, secrets['azure_iot_hub'], secrets['azure_iot_sas'], secrets['device_id'])

# Get a Device Twin
device_twin = hub.get_device_twin()
# Filter out the device's name from the twin's properties
device_name = device_twin['properties']['desired']['deviceName']
print(device_name)

# Update a Device Twin's Properties
data = {"properties":{"desired": {"deviceName": "{{BasementTemperatureLoggerFeather}}"}}}
hub.update_device_twin(data)

# And read the updated device twin information
device_twin = hub.get_device_twin()
device_name = device_twin['properties']['desired']['deviceName']
print(device_name)
