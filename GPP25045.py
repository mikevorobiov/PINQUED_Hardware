"""
Module: GW INSTEK GPP-250-4.5 power supply unit control
Description: This module provides a class to interface with the GW INSTEK GPP250-4.5 power
             supply unit (PSU) using pyvisa for setting current and voltage on the PSU

Author: Mykhailo Vorobiov
Email: mvorobiov@wm.edu
Date: 2024-10-02
"""

import pyvisa
import numpy as np
import logging


class GPP25045():
    """
    A class for interfacing with the GW INSTEK GPP250-4.5 
    signle channel power supply unit.
    """


    def __init__(self, resource_name, alias='GPP250-4.5', log_level='INFO'):
        """
        Initialize the PSU class and establish connection.

        :param resource_name: VISA resource name for the PSU.
        :param alias: Alias for logging.
        :param log_level: Level of logging.
        """
        self.LOG_FORMAT = f'%(asctime)s [%(levelname)s] {alias}: %(message)s'
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format=self.LOG_FORMAT, level=log_level)
        self.psu_address = resource_name

        self.MAX_CURRENT = 10.0 # Amp
        self.MAX_VOLTAGE = 36.0 # Volt

        try:
            self.rm = pyvisa.ResourceManager()
            self.psu = self.rm.open_resource(self.psu_address)
            self.psu.timeout = 3000
            self.logger.info(f"Connection established with the GW INSTEK GPP250-4.5 PSU."
                             f"\n\tResource address: {self.psu_address}"
                             f'\n\tID: {self.get_idn()}')
            self.toggle_output(False)
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Failed to connect to the PSU.\n\t{e}')
            self.psu = None

    def get_idn(self):
        """
        Query the identification of the instrument.

        :return: Identifier string if query is successful or None otherwise.
        """
        try:
            return self.psu.query('*IDN?').strip()
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Error retrieving identification: {e}')
            return None
        

    def get_current_meas(self):
        """
        Query the current reading of the instrument.

        :return: Current reading in amps as float number and None if error occurs.
        """

        try:
            return float(self.psu.query('MEAS:CURR?'))
        except pyvisa.VisaIOError as e:
            self.logger.error(f"Error querying the current reading: {e}")
            return None
    
    def get_voltage_meas(self):
        """
        Query the voltage reading of the instrument.

        :return: Voltage reading in volts as float number and None if error occurs.
        """

        try:
            return float(self.psu.query('MEAS:VOLT?'))
        except pyvisa.VisaIOError as e:
            self.logger.error(f"Error querying the voltage reading: {e}")
            return None

    def get_power_meas(self):
        """
        Query the power reading of the instrument.

        :return: Power reading in watts as float number and None if error occurs.
        """

        try:
            return float(self.psu.query('MEAS:POWE?'))
        except pyvisa.VisaIOError as e:
            self.logger.error(f"Error querying the power reading: {e}")
            return None
        

    
    def set_current(self, current):
        """
        Set the target current output of the instrument.
        """

        if current <= self.MAX_CURRENT and current >= 0.0:
            try:
                self.psu.write(f'SOUR:CURR {current}')
                self.logger.info(f"Current is set to {current} V")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Error setting the current target output: {e}")
        else:
            self.logger.warning(f"Target current must be between 0 and {self.MAX_CURRENT} Amps."
                                f"\n\tThe traget current left unchanged.")

    def set_voltage(self, voltage):
        """
        Set the target voltage output of the instrument.
        """

        if voltage <= self.MAX_VOLTAGE and voltage >= 0.0:
            try:
                self.psu.write(f'SOUR:VOLT {voltage}')
                self.logger.info(f"Voltage is set to {voltage} V")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Error setting the voltage target output: {e}")
        else:
            self.logger.warning(f"Target voltage must be between 0 and {self.MAX_VOLTAGE} Volts."
                                f"\n\tThe traget voltage left unchanged.")

    def toggle_output(self, output_state=False):
        """
        Set the output state of the instrument ON or OFF.

        :param output_state: Boolean flag. Sets the output ON if 'True' or OFF if 'False'.
        """

        self.output_state = output_state
        try:
            if self.output_state:
                self.psu.write(f'OUTP:STAT 1')
                self.logger.info(f"Output is ON")
            else:
                self.psu.write(f'OUTP:STAT 0')
                self.logger.info(f"Output is OFF")
        except pyvisa.VisaIOError as e:
            self.logger.error(f"Error toggle the output: {e}")

    def close(self):
        """
        Close the connection to the PSU.
        """
        if self.psu:
            try:
                self.toggle_output(False)
                self.psu.close()
                self.logger.info("Connection to the PSU closed.")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Error closing connection: {e}")



