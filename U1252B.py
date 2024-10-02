"""
Module: Keysight US1252B digital handheld multimeter control
Description: This module provides a class to interface with the Keysight US1252B 
             digital handheld multimeter using pyvisa.

Author: Mykhailo Vorobiov
Email: mvorobiov@wm.edu
Date: 2024-10-02
"""

import pyvisa
import numpy as np
import logging


class U1252B():
    """
    A class for interfacing with the Keysight U1252B digital hadheld multimeter.
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
