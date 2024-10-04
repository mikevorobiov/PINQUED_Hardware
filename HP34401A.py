"""
Module: HP 34401A Digital Multimeter Control
Description: This module provides a class to interface with a digital multimeter (DMM)
             using pyvisa for performing measurements such as voltage, current,
             and resistance.

Author: Mykhailo Vorobiov
Email: mvorobiov@wm.edu
Date: 2024-10-03


THIS CLASS DOES WORK AND COMMUNICATE WITH THE 
APPROPRIATE DMM PROPERLY. 
CURRENTLY ONLYD DIRECTLY THROUGH QUERY AND WRITE FUNCTIONS
"""

import pyvisa
import logging
import time

class HP34401A:
    """
    A class to interface with a HP 34401A Digital Multimeter (DMM) via pyvisa.

    This class allows you to measure DC voltage, AC voltage, DC current, AC current,
    and resistance from a DMM using pyvisa communication.
    """

    def __init__(self, visa_rm, resource_address, alias='DigitalMultimeter', log_level='INFO'):
        """
        Initialize the Digital Multimeter class and establish a connection.

        :param resource_name: VISA resource name for the multimeter.
        :param alias: Alias for logging.
        :param log_level: Logging level (default: INFO).
        """
        self.LOG_FORMAT = f'%(asctime)s [%(levelname)s] {alias}: %(message)s'
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format=self.LOG_FORMAT, level=log_level)

        try:
            self.dmm = visa_rm.open_resource(resource_address)
            self.dmm.timeout = 5000  # Set timeout to 5 seconds
            self.logger.info(f"Connection established with the digital multimeter."
                             f"\n\tResource address: {resource_address}"
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

    def config(self):
        return


    def measure_current_dc(self):
        """
        Measure DC current.

        :return: DC current reading.
        """
        try:
            self.dmm.write("MEAS:CURR:DC?\n")
            time.sleep(0.25)
            current = float(self.dmm.read())
            self.logger.info(f"DC Current measured: {current} A")
            return current
        except pyvisa.VisaIOError as e:
            self.logger.error(f"Error measuring DC current: {e}")
            return None
    
    def set_range(self, min, max):
        if min < max:
            try:
                self.dmm.write("MEAS:CURR:DC?\n")
                time.sleep(0.25)
                current = float(self.dmm.read())
                self.logger.info(f"DC Current measured: {current} A")
                return current
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Error measuring DC current: {e}")
                return None
        else:
            self.logger.error('Error! Max range value cannot be less than min.')
            return None
        

    def set_function(self, function):
        """
        Set the measurement function of the multimeter.

        :param function: Measurement function (e.g., "VOLT:DC", "VOLT:AC", "CURR:DC", "RES").
        """
        valid_functions = ["VOLT:DC", "VOLT:AC", "CURR:DC", "CURR:AC", "RES"]
        if function in valid_functions:
            try:
                self.dmm.write(f"CONF{function}\n")
                self.logger.info(f"Measurement function set to CONF:{function}")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Error setting measurement function: {e}")
        else:
            self.logger.warning(f"Invalid measurement function '{function}'. "
                                f"Valid functions are: {', '.join(valid_functions)}")

    def write(self, command):
        if isinstance(command, str):
            self.dmm.write(command)
            self.logger.info(f"Sent command: {command}")
        else:
            self.logger.error(f'Write argument {command} is not a string.')
    
    def query(self, command):
        if isinstance(command, str):
            result = self.dmm.query(command)
            self.logger.info(f"Query {command} resulted in: {result}")
            return result
        else:
            self.logger.error(f'Query argument {command} is not a string.')
    
    
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
