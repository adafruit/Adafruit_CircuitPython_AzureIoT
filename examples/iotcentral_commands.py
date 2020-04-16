import time
import board
import busio
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
from adafruit_ntp import NTP

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
    esp32_cs = DigitalInOut(board.D13)
    esp32_ready = DigitalInOut(board.D11)
    esp32_reset = DigitalInOut(board.D12)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets)
wifi.connect()

ntp = NTP(esp)
# Wait for a valid time to be received
while not ntp.valid_time:
    time.sleep(0.1)
    ntp.set_time()

# To use Azure IoT Central, you will need to create an IoT Central app.
# You can either create a free tier app that will live for 7 days without an Azure subscription,
# Or a standard tier app that will last for ever with an Azure subscription.
# The standard tiers are free for up to 2 devices
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
# Create an Azure IoT Central app by following these instructions: https://aka.ms/CreateIoTCentralApp
# Add a device template with telemetry, properties and commands, as well as a view to visualize the
# telemetry and execute commands, and a form to set properties.
#
# Next create a device using the device template, and select Connect to get the device connection details.
# Add the connection details to your secrets.py file, using the following values:
#
# 'id_scope' - the devices ID scope
# 'device_id' - the devices device id
# 'key' - the devices primary key

from adafruit_azureiot import IoTCentralDevice
from adafruit_azureiot.iot_mqtt import IoTResponse

# Create an IoT Hub device client and connect
device = IoTCentralDevice(wifi, secrets["id_scope"], secrets["device_id"], secrets["key"])

# Subscribe to commands
# Commands can be sent from the devices Dashboard in IoT Central, assuming
# the device template and view has been set up with the commands
# Command handlers need to return a response to show if the command was handled
# successfully or not, returning an HTTP status code and message
def command_executed(command_name: str, payload) -> IoTResponse:
    print("Command", command_name, "executed with payload", str(payload))
    # return a status code and message to indicate if the command was handled correctly
    return IoTResponse(200, "OK")


device.on_command_executed = command_executed

device.connect()

while True:
    # Poll every second for messages from the cloud
    device.loop()

    time.sleep(1)
