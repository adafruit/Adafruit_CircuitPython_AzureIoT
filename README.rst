Adafruit_CircuitPython_AzureIoT
================================

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-azureiot/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/azureiot/en/latest/
    :alt: Documentation Status

.. image:: https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_Bundle/main/badges/adafruit_discord.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_AzureIoT/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_AzureIoT/actions/
    :alt: Build Status

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Code Style: Ruff

A CircuitPython device library for `Microsoft Azure IoT Services <https://azure.microsoft.com/overview/iot/?WT.mc_id=academic-3168-jabenn>`_ from a CircuitPython device. This library only supports key-base authentication, it currently doesn't support X.509 certificates.

Installing from PyPI
=====================
On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-azureiot/>`_. To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-azureiot

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-azureiot

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .venv
    source .venv/bin/activate
    pip3 install adafruit-circuitpython-azureiot

Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Adafruit CircuitPython BinASCII <https://github.com/adafruit/Adafruit_CircuitPython_Binascii>`_
* `Adafruit CircuitPython Logging <https://github.com/adafruit/Adafruit_CircuitPython_Logging>`_
* `Adafruit CircuitPython MiniMQTT <https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

**Board Compatibility:** The following built-in modules must be available: gc, json, time

Usage Example
=============

This library supports both `Azure IoT Hub <https://azure.microsoft.com/services/iot-hub/?WT.mc_id=academic-3168-jabenn>`_ and `Azure IoT Central <https://azure.microsoft.com/services/iot-central/?WT.mc_id=academic-3168-jabenn>`__.

To create an Azure IoT Hub instance or an Azure IoT Central app, you will need an Azure subscription. If you don't have an Azure subscription, you can sign up for free:

- If you are a student 18 or over, head to `aka.ms/FreeStudentAzure <https://aka.ms/FreeStudentAzure>`_ and sign up, validating with your student email address. This will give you $100 of Azure credit and free tiers of a load of service, renewable each year you are a student. You will not need a credit card.

- If you are not a student, head to `aka.ms/FreeAz <https://aka.ms/FreeAz>`_ and sign up to get $200 of credit for 30 days, as well as free tiers of a load of services. You will need a credit card for validation only, your card will not be charged.

ESP32 AirLift Networking
========================

To use this library, you will need to create an ESP32_SPI WifiManager, connected to WiFi. You will also need to set the current time, as this is used to generate time-based authentication keys. One way to do this is with the following code:

.. code-block:: python

    # get_time will raise ValueError if the time isn't available yet so loop until
    # it works.
    now_utc = None
    while now_utc is None:
        try:
            now_utc = time.localtime(esp.get_time()[0])
        except ValueError:
            pass
    rtc.RTC().datetime = now_utc

Native Networking
=================
To use this library, with boards that have native networking support, you need to be connected to a network. You will also need to set the current time, as this is used to generate time-based authentication keys. One way to do this is the `Adafruit NTP library <https://github.com/adafruit/Adafruit_CircuitPython_NTP>`_ with the following code:

.. code-block:: python

    pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
    ntp = adafruit_ntp.NTP(pool, tz_offset=0)

    # NOTE: This changes the system time so make sure you aren't assuming that time
    # doesn't jump.
    rtc.RTC().datetime = ntp.datetime

Azure IoT Hub
-------------

To interact with Azure IoT Hub, you will need to create a hub, and a register a device inside that hub. There is a free tier available, and this free tier allows up to 8,000 messages a day, so try not to send messages too often if you are using this tier.

- Open the `Azure Portal <https://aka.ms/AzurePortalHome>`_.
- Follow the instructions in `Microsoft Docs <https://aka.ms/CreateIoTHub>`_ to create an Azure IoT Hub and register a device.
- Copy the devices Primary or secondary connection string, and add this to your ``settings.toml`` file.

You can find the device connection string by selecting the IoT Hub in the `Azure Portal <https://aka.ms/AzurePortalHome>`_, *selecting Explorer -> IoT devices*, then selecting your device.

.. image:: iot-hub-device.png
   :alt: Locating the device in the IoT hub blade

*Locating the device in the IoT hub blade*

Then copy either the primary or secondary connection string using the copy button next to the value.

.. image:: iot-hub-device-keys.png
   :alt: Copy the primary connection string

*Copy the primary connection string*

**Connect your device to Azure IoT Hub**

.. code-block:: python

    from adafruit_azureiot import IoTHubDevice

    device = IoTHubDevice(wifi, device_connection_string)
    device.connect()

Once the device is connected, you will regularly need to run a ``loop`` to poll for messages from the cloud.

.. code-block:: python

    while True:
        device.loop()
        time.sleep(1)

**Send a device to cloud message**

.. code-block:: python

    message = {"Temperature": temp}
    device.send_device_to_cloud_message(json.dumps(message))

**Receive device to cloud messages**

.. code-block:: python

    def cloud_to_device_message_received(body: str, properties: dict):
        print("Received message with body", body, "and properties", json.dumps(properties))

    # Subscribe to cloud to device messages
    device.on_cloud_to_device_message_received = cloud_to_device_message_received

**Receive direct methods**

.. code-block:: python

    def direct_method_invoked(method_name: str, payload) -> IoTResponse:
        print("Received direct method", method_name, "with data", str(payload))
        # return a status code and message to indicate if the direct method was handled correctly
        return IoTResponse(200, "OK")

    # Subscribe to direct methods
    device.on_direct_method_invoked = direct_method_invoked

**Update reported properties on the device twin**

*This is not supported on Basic tier IoT Hubs, only on the free and standard tiers.*

.. code-block:: python

    patch = {"Temperature": temp}
    device.update_twin(patch)

**Subscribe to desired property changes on the device twin**

*This is not supported on Basic tier IoT Hubs, only on the free and standard tiers.*

.. code-block:: python

    def device_twin_desired_updated(desired_property_name: str, desired_property_value, desired_version: int):
        print("Property", desired_property_name, "updated to", str(desired_property_value), "version", desired_version)

    # Subscribe to desired property changes
    device.on_device_twin_desired_updated = device_twin_desired_updated

Azure IoT Central
-----------------

To use Azure IoT Central, you will need to create an Azure IoT Central app, create a device template and register a device against the template.

- Head to `Azure IoT Central <https://apps.azureiotcentral.com/?WT.mc_id=academic-3168-jabenn>`__
- Follow the instructions in the `Microsoft Docs <https://docs.microsoft.com/azure/iot-central/core/quick-deploy-iot-central?WT.mc_id=academic-3168-jabenn>`__ to create an application. Every tier is free for up to 2 devices.
- Follow the instructions in the `Microsoft Docs <https://docs.microsoft.com/azure/iot-central/core/quick-create-simulated-device?WT.mc_id=academic-3168-jabenn>`__ to create a device template.
- Create a device based off the template, and select **Connect** to get the device connection details. Store the ID Scope, Device ID and either the primary or secondary device SAS key in your ``settings.toml`` file.

.. image:: iot-central-connect-button.png
   :alt: The IoT Central connect button

*The connect button*

.. image:: iot-central-connect-dialog.png
   :alt: The IoT Central connection details dialog

*The connection details dialog*


settings.toml:

.. code-block:: python

    # WiFi settings
    CIRCUITPY_WIFI_SSID="Your WiFi ssid"
    CIRCUITPY_WIFI_PASSWORD="Your WiFi password"

    # Azure IoT Central settings
    id_scope="Your ID Scope"
    device_id="Your Device ID"
    device_sas_key="Your Primary Key"

**Connect your device to your Azure IoT Central app**

.. code-block:: python

    import wifi
    from os import getenv
    from adafruit_azureiot import IoTCentralDevice
    import adafruit_connection_manager

    ssid = getenv("CIRCUITPY_WIFI_SSID")
    password = getenv("CIRCUITPY_WIFI_PASSWORD")
    id_scope = getenv("id_scope")
    device_id = getenv("device_id")
    device_sas_key = getenv("device_sas_key")

    wifi.radio.connect(ssid, password)

    pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)

    device = IoTCentralDevice(pool, id_scope, device_id, device_sas_key)
    device.connect()

Once the device is connected, you will regularly need to run a ``loop`` to poll for messages from the cloud.

.. code-block:: python

    while True:
        device.loop()
        time.sleep(1)

**Send telemetry**

.. code-block:: python

    message = {"Temperature": temp}
    device.send_telemetry(json.dumps(message))

**Listen for commands**

.. code-block:: python

    def command_executed(command_name: str, payload) -> IoTResponse:
        print("Command", command_name, "executed with payload", str(payload))
        # return a status code and message to indicate if the command was handled correctly
        return IoTResponse(200, "OK")

    # Subscribe to commands
    device.on_command_executed = command_executed

**Update properties**

.. code-block:: python

    device.send_property("Desired_Temperature", temp)

**Listen for property updates**

.. code-block:: python

    def property_changed(property_name, property_value, version):
        print("Property", property_name, "updated to", str(property_value), "version", str(version))

    # Subscribe to property updates
    device.on_property_changed = property_changed

Learning more about Azure IoT services
--------------------------------------

If you want to learn more about setting up or using Azure IoT Services, check out the following resources:

- `Azure IoT documentation on Microsoft Docs <https://docs.microsoft.com/azure/iot-fundamentals/?WT.mc_id=academic-3168-jabenn>`_
- `IoT learning paths and modules on Microsoft Learn <https://docs.microsoft.com/learn/browse/?term=iot&WT.mc_id=academic-3168-jabenn>`_ - Free, online, self-guided hands on learning with Azure IoT services

Documentation
=============

API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/azureiot/en/latest/>`_.

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_AzureIoT/blob/main/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
