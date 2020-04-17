"""
An error from the IoT service
"""


class IoTError(Exception):
    """
    An error from the IoT service
    """

    def __init__(self, message: str):
        """Create the IoT Error
        :param str message: The error message
        """
        super(IoTError, self).__init__(message)
        self.message = message
