Adafruit_CircuitPython_AzureIoT
================================

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-azureiot/badge/?version=latest
    :target: https://circuitpython.readthedocs.io/projects/azureiot/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://discord.gg/nBQh6qu
    :alt: Discord

.. image:: https://travis-ci.com/adafruit/Adafruit_CircuitPython_AzureIoT.svg?branch=master
    :target: https://travis-ci.com/adafruit/Adafruit_CircuitPython_AzureIoT
    :alt: Build Status

Access to `Microsoft Azure IoT <https://azure.microsoft.com/en-us/overview/iot/>`_ from a CircuitPython device. This library can perform device
messaging services (cloud-to-device, device-to-cloud), device services, and job services.

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

Building locally
================

Zip release files
-----------------

To build this library locally you'll need to install the
`circuitpython-build-tools <https://github.com/adafruit/circuitpython-build-tools>`_ package.

.. code-block:: shell

    python3 -m venv .env
    source .env/bin/activate
    pip install circuitpython-build-tools

Once installed, make sure you are in the virtual environment:

.. code-block:: shell

    source .env/bin/activate

Then run the build:

.. code-block:: shell

    circuitpython-build-bundles --filename_prefix adafruit-circuitpython-azureiot --library_location .

Sphinx documentation
-----------------------

Sphinx is used to build the documentation based on rST files and comments in the code. First,
install dependencies (feel free to reuse the virtual environment from above):

.. code-block:: shell

    python3 -m venv .env
    source .env/bin/activate
    pip install Sphinx sphinx-rtd-theme

Now, once you have the virtual environment activated:

.. code-block:: shell

    cd docs
    sphinx-build -E -W -b html . _build/html

This will output the documentation to ``docs/_build/html``. Open the index.html in your browser to
view them. It will also (due to -W) error out on any warning like Travis will. This is a good way to
locally verify it will pass.
