"""
Module: HP 3457A Digital Multimeter Control
Description: This module provides a class to interface with a digital multimeter (DMM)
             using pyvisa for performing measurements such as voltage, current,
             and resistance.

Author: Mykhailo Vorobiov
Email: mvorobiov@wm.edu
Date: 2024-10-02
"""

import pyvisa
import logging


class U1252B:
    """
    A class to interface with a HP 3457A Digital Multimeter (DMM) via pyvisa.

    This class allows you to measure DC voltage, AC voltage, DC current, AC current,
    and resistance from a DMM using pyvisa communication.
    """

    def __init__(self, resource_name, alias='DigitalMultimeter', log_level='INFO'):
        """
        Initialize the Digital Multimeter class and establish a connection.

        :param resource_name: VISA resource name for the multimeter.
        :param alias: Alias for logging.
        :param log_level: Logging level (default: INFO).
        """
        self.LOG_FORMAT = f'%(asctime)s [%(levelname)s] {alias}: %(message)s'
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format=self.LOG_FORMAT, level=log_level)
        self.dmm_address = resource_name

        try:
            self.rm = pyvisa.ResourceManager()
            self.dmm = self.rm.open_resource(self.dmm_address)
            self.dmm.timeout = 5000  # Set timeout to 5 seconds
            self.logger.info(f"Connection established with the digital multimeter."
                             f"\n\tResource address: {self.dmm_address}"
                             f'\n\tID: {self.get_idn()}')
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Failed to connect to the digital multimeter.\n\t{e}')
            self.dmm = None

    def get_idn(self):
        """
        Query the identification of the digital multimeter: manufacturer, model, serial number, and firmware version.

        :return: Identifier string if query is successful, or None otherwise.
        """
        try:
            return self.dmm.query('*IDN?')
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Error retrieving identification of the digital multimeter: {e}')
            return None

    def get_reading_primary(self):
        """
        Get measurement reading (primary)

        :return: measurement reading.
        """
        try:
            self.dmm.write("FETC?")
            voltage = float(self.dmm.read())
            self.logger.info(f"Measurement: {voltage} V")
            return voltage
        except pyvisa.VisaIOError as e:
            self.logger.error(f"Error measuring DC voltage: {e}")
            return None

    def close(self):
        """
        Close the connection to the multimeter.
        """
        if self.dmm:
            try:
                self.dmm.close()
                self.logger.info("Connection to the digital multimeter closed.")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Error closing connection to the multimeter: {e}")

# Example usage (commented out):
# dmm = DigitalMultimeter("USB0::0x1234::0x5678::INSTR")
# voltage = dmm.measure_voltage_dc()
# current = dmm.measure_current_dc()
# dmm.close()
