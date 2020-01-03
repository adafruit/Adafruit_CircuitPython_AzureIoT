Adafruit_CircuitPython_AzureIoT
================================

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-azureiot/badge/?version=latest
    :target: https://circuitpython.readthedocs.io/projects/azureiot/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://discord.gg/nBQh6qu
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_AzureIoT/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_AzureIoT/actions/
    :alt: Build Status

Access to `Microsoft Azure IoT <https://azure.microsoft.com/en-us/overview/iot/>`_ from a CircuitPython device. This library can perform device
messaging services (cloud-to-device, device-to-cloud), device services, and job services.

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
    python3 -m venv .env
    source .env/bin/activate
    pip3 install adafruit-circuitpython-azureiot

Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Usage Example
=============

Create an instance of an Azure IoT Hub (you'll need your SAS Token).

.. code-block:: python

    my_hub = IOT_HUB(wifi, 'Azure_IOT_Hub_Name', 'Azure_IOT_Hub_SAS_Token', 'Azure_Device_Identifier')

Send a device-to-cloud message

.. code-block:: python

    my_hub.send_device_message('Hello Azure IoT!')

Enumerate all devices on an Azure IOT Hub

.. code-block:: python

    hub_devices = my_hub.get_devices()

Get information about the current device on an Azure IoT Hub

.. code-block:: python

    device_info = my_hub.get_device()

Get information about the current device's device twin

.. code-block:: python

    twin_info = my_hub.get_device_twin()

Update the current device's device twin properties

.. code-block:: python

    my_hub.update_device_twin(device_properties)

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_AzureIoT/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Documentation
=============

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.
