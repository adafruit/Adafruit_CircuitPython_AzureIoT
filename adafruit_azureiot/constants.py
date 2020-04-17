# The MIT License (MIT)
#
# Copyright (c) 2020 Jim Bennett
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`constants`
================================================================================

This file is for maintaining Microsoft Azure IoT constants that could be changed or added to over time for different scenarios

* Author(s): Jim Bennett, Elena Horton
"""

# The version of the IoT Central MQTT API this code is built against
IOTC_API_VERSION = "2016-11-14"

# The version of the Azure Device Provisioning Service this code is built against
DPS_API_VERSION = "2018-11-01"

# The Azure Device Provisioning service endpoint that this library uses to provision IoT Central devices
DPS_END_POINT = "global.azure-devices-provisioning.net"
