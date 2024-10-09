"""
Module: HP 3457A Digital Multimeter Control
Description: This module provides a class to interface with a digital multimeter (DMM)
             using pyvisa for performing measurements such as voltage, current,
             and resistance.

Author: Mykhailo Vorobiov
Email: mvorobiov@wm.edu
Date: 2024-10-02
Updated: 2024-10-08
"""

import pyvisa
import logging


class HP3457A:
    """
    A class to interface with a HP 3457A Digital Multimeter (DMM) via pyvisa.

    This class allows you to measure DC voltage, AC voltage, DC current, AC current,
    and resistance from a DMM using pyvisa communication.
    """

    # List of data return formats
    FORMATS = ['ASCII', 
               'SINT', 
               'DINT', 
               'SREAL', 
               'DREAL'
               ]
    
    BEEPER_STATUS = ['ON','OFF','ONCE']

    # List of functions
    FUNCTIONS = ['DCV',
                 'ACV',
                 'ACDCV',
                 'OHM',
                 'OHMF',
                 'DCI',
                 'ACI',
                 'ACDCI',
                 'FREQ',
                 'PER'
                ]
    
    # DC Volts Spec
    DCV_RES = {'30mv': {'6.5': 10e-9, '5.5': 100e-9, '4.5': 1e-6, '3.5': 10e-6},
                    '300mv': {'6.5': 100e-9, '5.5': 1e-6, '4.5': 10e-6, '3.5': 100e-6},
                    '3v': {'6.5': 1e-6, '5.5': 10e-6, '4.5': 100e-6, '3.5': 1e-3},
                    '30v': {'6.5': 10e-6, '5.5': 100e-6, '4.5': 1e-3, '3.5': 10e-3},
                    '300v': {'6.5': 100e-6, '5.5': 1e-3, '4.5': 10e-3, '3.5': 100e-3}
                    }
    
    DCV_ACC = {'30mv': {'100': {'acc': .0045, 'counts': 365}, '10': {'acc': .0045, 'counts': 385},
                    '1': {'acc': .0045, 'counts': 500}, '.1': {'acc': .0045, 'counts': 70},
                    '.005': {'acc': .0045, 'counts': 19}, '.0005': {'acc': .0045, 'counts': 6}},
                    '300mv': {'100': {'acc': .0035, 'counts': 39}, '10': {'acc': .0035, 'counts': 40},
                    '1': {'acc': .0035, 'counts': 50}, '.1': {'acc': .0035, 'counts': 9},
                    '.005': {'acc': .0035, 'counts': 4}, '.0005': {'acc': .0035, 'counts': 4}},
                    '3v': {'100': {'acc': .0025, 'counts': 6}, '10': {'acc': .0025, 'counts': 7},
                    '1': {'acc': .0025, 'counts': 7}, '.1': {'acc': .0025, 'counts': 4},
                    '.005': {'acc': .0025, 'counts': 4}, '.0005': {'acc': .0025, 'counts': 4}},
                    '30v': {'100': {'acc': .0040, 'counts': 19}, '10': {'acc': .0040, 'counts': 20},
                    '1': {'acc': .0040, 'counts': 30}, '.1': {'acc': .0040, 'counts': 7},
                    '.005': {'acc': .0040, 'counts': 4}, '.0005': {'acc': .0040, 'counts': 4}},
                    '300v': {'100': {'acc': .0055, 'counts': 6}, '10': {'acc': .0055, 'counts': 7},
                    '1': {'acc': .0055, 'counts': 7}, '.1': {'acc': .0055, 'counts': 4},
                    '.005': {'acc': .0055, 'counts': 4}, '.0005': {'acc': .0055, 'counts': 4}}
                    }
    
    # DC Current Spec
    DCI_RES = {'300ua': {'6.5': 100e-12, '5.5': 1e-9, '4.5': 10e-9, '3.5': 100e-9},
                    '3ma': {'6.5': 1e-9, '5.5': 10e-9, '4.5': 100e-9, '3.5': 1e-6},
                    '30ma': {'6.5': 10e-9, '5.5': 100e-9, '4.5': 1e-6, '3.5': 10e-6},
                    '300ma': {'6.5': 100e-9, '5.5': 1e-6, '4.5': 10e-6, '3.5': 100e-6},
                    '1a': {'6.5': 1e-6, '5.5': 10e-6, '4.5': 100e-6, '3.5': 1e-3}
                    }
    
    DCI_ACC = {'300ua': {'100': {'acc': .04, 'counts': 104}, '10': {'acc': .04, 'counts': 104},
                    '1': {'acc': .04, 'counts': 115}, '.1': {'acc': .04, 'counts': 14},
                    '.005': {'acc': .04, 'counts': 5}, '.0005': {'acc': .04, 'counts': 4}},
                    '3ma': {'100': {'acc': .04, 'counts': 104}, '10': {'acc': .04, 'counts': 104},
                    '1': {'acc': .04, 'counts': 115}, '.1': {'acc': .04, 'counts': 14},
                    '.005': {'acc': .04, 'counts': 5}, '.0005': {'acc': .04, 'counts': 4}},
                    '30ma': {'100': {'acc': .04, 'counts': 104}, '10': {'acc': .04, 'counts': 104},
                    '1': {'acc': .04, 'counts': 115}, '.1': {'acc': .04, 'counts': 14},
                    '.005': {'acc': .04, 'counts': 5}, '.0005': {'acc': .04, 'counts': 4}},
                    '300ma': {'100': {'acc': .08, 'counts': 204}, '10': {'acc': .08, 'counts': 204},
                    '1': {'acc': .08, 'counts': 215}, '.1': {'acc': .08, 'counts': 24},
                    '.005': {'acc': .08, 'counts': 6}, '.0005': {'acc': .08, 'counts': 4}},
                    '1a': {'100': {'acc': .08, 'counts': 604}, '10': {'acc': .08, 'counts': 604},
                    '1': {'acc': .08, 'counts': 615}, '.1': {'acc': .08, 'counts': 64},
                    '.005': {'acc': .08, 'counts': 10}, '.0005': {'acc': .08, 'counts': 5}}
                    }

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
            self.dmm.write('ID?')
            return self.dmm.read_bytes(9).decode().strip()
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Error retrieving identification of the digital multimeter: {e}')
            return None
    
    def _check_format(self, format):
        if format in self.FORMATS:
            return True
        else:
            return False
        
    def set_format(self, format='ASCII'):
        if self._check_format(format):
            try:
                self.dmm.write(f'OFORMAT\\s{format};')
                self.logger.info(f'Format  has been set to {format}')
            except pyvisa.VisaIOError as e:
                self.logger.error(f'Couldn\'t set reading format to {format}: {e}')
        else:
            self.logger.warning(f'Entered format is not allowed. Allowed formats: {self.FORMATS}')

    def get_reading(self):
        try:
            self.dmm.write(f'TARM\\sAUTO')
            return float(self.dmm.read_bytes(16).decode().strip())
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Error failed to get reading: {e}')

    def set_beeper_status(self, status='OFF'):
        if status in self.BEEPER_STATUS:
            try:
                self.dmm.write(f'BEEP\\s{status}')
                self.logger.info(f'Beeper is set to {status}')
            except pyvisa.VisaIOError as e:
                self.logger.error(f'Error setting beeper status: {e}')
        else:
            self.logger.warning(f'Warning! The passed beeper status is not allowed.'
                                f'Choose from {self.BEEPER_STATUS}')

    def set_function(self, function='DCV'):
        """
        Set the measurement function of the multimeter.

        :param function: Measurement function .
        """
        if function in self.FUNCTIONS:
            try:
                self.dmm.write(f"FUNC\\s{function}")
                self.logger.info(f"Measurement function set to {function}")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Error setting measurement function: {e}")
        else:
            self.logger.warning(f"Invalid measurement function '{function}'. "
                                f"Valid functions are: {', '.join(self.FUNCTIONS)}")

    def get_temperature(self):
        try:
            self.dmm.write("TEMP?")
            temp = float(self.dmm.read(16).decode().strip())
            self.logger.info(f"DMM's internal temperature is: {temp}")
            return temp
        except pyvisa.VisaIOError as e:
            self.logger.error(f"Error retrieving DMM's internal temperature: {e}")

    def toggle_keyboard(self, status=True):
        if status:
            try:
                self.dmm.write("LOCK\\sON")
                self.logger.info(f"DMM's keyboard is unlocked.")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Error unlocking the DMM's keyboard: {e}")
        else:
            try:
                self.dmm.write("LOCK\\sOFF")
                self.logger.info(f"DMM's keyboard is locked.")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Error locking the DMM's keyboard: {e}")

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


# Example usage
if __name__ == "__main__":
    rm = pyvisa.ResourceManager()
    dmm = HP3457A("visa://192.168.194.15/GPIB1::22::INSTR")
    dmm.set_format('ASCII')
    dmm.set_beeper_status('ONCE')
    dmm.set_function('DCV')
    print(dmm.get_reading())
    dmm.close()
