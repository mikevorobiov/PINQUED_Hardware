import pyvisa
import numpy as np
import struct

import logging

class SDS814XHD:

    # List of valid channels
    VALID_CHANNELS = ['C1', 'C2', 'C3', 'C4', 'F1', 'F2', 'F3', 'F4']
    
    # List of timebases in units of sec/div
    TIMEBASE_LIST = [200e-12,500e-12, 1e-9,
                        2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 
                        1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 
                        1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 
                        1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]

    def __init__(self, 
                 resource_name,
                 alias = 'SDS814XHD',
                 log_level='INFO'):
        """
        Initialize the oscilloscope class and establish connection.

        :param resource_name: VISA resource name for the oscilloscope.
        :param log_level: Level of logging for logger object.
        :logger_obj: Logger object
        """ 
        self.LOG_FORMAT = f'%(asctime)s [%(levelname)s] {alias}: %(message)s'
        self.logger = logging.getLogger(__name__)

        logging.basicConfig(format = self.LOG_FORMAT, level=log_level)
        self.scope_address = resource_name

        try:
            self.rm = pyvisa.ResourceManager()
            self.oscilloscope = self.rm.open_resource(self.scope_address)
            self.oscilloscope.timeout = 3000
            self.logger.info("Connection established with the SDS814X HD oscilloscope."
                             f"\n\t Resource address: {self.scope_address}"
                             f'\n\t ID: {self.get_idn()}')
            self.read_preamble()
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Failed to connect to the oscilloscope.\n\t{e}')
            self.oscilloscope = None

    def get_idn(self):
        """
        Query the identification of the instrument: its type and software version. 
        The response consists of four different fields
        providing information on the manufacturer, the scope model,
        the serial number and the firmware revision.

        :return: Identifier string if query is successful or None otherwise
        """
        try:
            return self.oscilloscope.query('*IDN?')
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Error retrieving identification of the oscilloscope: {e}')
            return None

    
    def is_valid_channel(self, channel):
        """
        Check if the given channel name is valid.

        :param channel: The channel name to validate.
        :return: True if the channel is valid, False otherwise.
        """
        return channel in self.VALID_CHANNELS
    
    def get_current_channel(self):
        """
        Retrieve the currently active channel from the oscilloscope.

        :return: The current channel name or None if there was an error.
        """
        try:
            return self.oscilloscope.query('WAV:SOUR?').strip()
        except pyvisa.VisaIOError as e:
            self.logger.error(f"Error querying the current channel ID: {e}")
            return None


    def set_channel(self, channel='C1'):
        """
        Select the channel from which to read data.
        If the reveived channel name is valid then sets the channel as current.
        Otherwise falls back to the recently active channel.

        :param channel: Channel number C1, C2, C3, C4, F1, F2, F3, F4. Default: 'C1'.
        :retrun: Returns 0 if the retrieval has been successful and 1 if ended with error.
        """
        # Validate the channel name
        if self.is_valid_channel(channel):
            try:
                # Set the the specified channel as active channel
                self.oscilloscope.write(f'WAV:SOUR {channel}')
                self.logger.info(f"Active channel: {channel}")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Failed to set channel: {e}")
        else:
            self.logger.warning(
                f"Invalid channel name '{channel}'. "
                f"Valid channels are: {', '.join(self.VALID_CHANNELS)}."
            )
            try:
                # Get and set the current channel as a fallback
                current_channel = self.get_current_channel()
                if current_channel:
                    self.logger.warning(f"Falling back to the current active channel: {current_channel}.")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Error retrieving the current channel: {e}")

                

    def get_number_of_points(self):
        """
        Retrieve the number of sampled points of the current waveform on the screen.

        :return: Integer number of sampled points.
        """
        try:
            return int(float(self.oscilloscope.query('ACQ:POIN?').strip()))
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Error retrieving the number of points: {e}')

    def read_preamble(self):
        """
        Read preamble string as a bitstream and parse it to save as the classes' fields.
        """
        try:
            # Retrieve the preamble block (e.g., scaling factors) as bitstream 
            self.logger.debug('Requesting preamble with the oscilloscope parameters.')
            self.oscilloscope.write(':WAV:PRE?')
            preamble = self.oscilloscope.read_raw()
            # The first 11 bits contain header (we don't need it)
            n_skip = 11
            # Retrieve and parse parameters from the preamble
            self.logger.debug('Unpacking the preamble bitstream.')
            self.num_points = struct.unpack('l', preamble[n_skip+116:n_skip+119+1])[0] # Number of data points
            # Extract scaling factors from the preamble
            self.first_point = struct.unpack('l', preamble[n_skip+132:n_skip+135+1])[0] # The offset relative to the beginning of the trace buffer
            self.data_interval = struct.unpack('l', preamble[n_skip+136:n_skip+139+1])[0] # Indicates the interval between data points for waveform transfer. Value is the same as the parameter of the :WAVeform:INTerval remote command.
            self.read_frames = struct.unpack('l', preamble[n_skip+144:n_skip+147+1])[0] # number of sequence frames transferred this time. Used to calculate the reading times of sequence waveform
            self.sum_frames = struct.unpack('l', preamble[n_skip+148:n_skip+151+1])[0] # sum_frames, number of sequence frames acquired. Used to calculate the reading times of sequence waveform
            self.vertical_gain = struct.unpack('f', preamble[n_skip+156:n_skip+159+1])[0] # Vertical gain. The value of vertical scale without probe attenuation
            self.vertical_offset = struct.unpack('f', preamble[n_skip+160:n_skip+163+1])[0] # The value of vertical offset without probe attenuation
            self.code_per_div = struct.unpack('f', preamble[n_skip+164:n_skip+167+1])[0] # The value is different for different vertical gain of different models
            self.adc_bit = struct.unpack('h', preamble[n_skip+172:n_skip+173+1])[0] # ADC bit
            self.sequence_frame_idx = struct.unpack('h', preamble[n_skip+174:n_skip+175+1])[0] # The specified frame index of sequence set by the parameter <value1> of the command :WAVeform:SEQuence. Default Value is 1
            self.horizontal_interval = struct.unpack('f', preamble[n_skip+176:n_skip+179+1])[0] # Horizontal interval. Sampling interval for time domain waveforms. Horizontal interval = 1/sampling rate.
            self.horizontal_offset = struct.unpack('d', preamble[n_skip+180:n_skip+187+1])[0] #Horizontal offset. Trigger offset for the first sweep of the trigger, seconds between the trigger and the first data point. Unit is s.
            self.timebase_idx = struct.unpack('h', preamble[n_skip+324:n_skip+325+1])[0] # Index of the timebase in the list 'timebase'
            self.vertical_coupling_idx = struct.unpack('h', preamble[n_skip+326:n_skip+327+1])[0] # Vertical coupling. 0-DC,1-AC,2-GND
            self.probe_attenuation = struct.unpack('f', preamble[n_skip+328:n_skip+331+1])[0] # Probe attenuation.
            # fixed_vertical_gain has been skipped due to the presence of the 'vertical_gain' variable
            self.bw_limit = struct.unpack('h', preamble[n_skip+334:n_skip+335+1])[0] # Bandwidth limit. 0-OFF,1-20M,2-200M
            self.source_channel = struct.unpack('h', preamble[n_skip+344:n_skip+345+1])[0] # Wave source. 0-C1,1-C2,2-C3,3-C4,4-C5,5-C6,6-C7,7-C8
            self.logger.debug('Unpacked the preamble bitstream.')

            self.timebase = self.TIMEBASE_LIST[self.timebase_idx]

            self.logger.debug(f'\n\tFirst point: {self.first_point}\n\t'
                                f'Number of points: {self.num_points}\n\t'
                                f'Data interval: {self.data_interval}\n\t'
                                f'Frames read: {self.read_frames}')

        except pyvisa.VisaIOError as e:
            self.logger.error(f'Error occured while trying to retrieve the preamble: {e}')
    
    def get_preamble_dict(self):
        """
        Takes the oscilloscope parameters updated using the 'read_preamble()' method 
        and forms a dictionary.


        :return: Dictionary of the oscilloscope's parameters.
        """
        preamble_dict = {
            'Number of points' : self.num_points,
            'First point': self.first_point,
            'Data interval': self.data_interval,
            'Read frames': self.read_frames,
            'Sum frames': self.sum_frames,
            'Vertical gain': self.vertical_gain,
            'Vertical offset': self.vertical_offset,
            'Code per division': self.code_per_div,
            'ADC bit': self.adc_bit,
            'Sequence frame index': self.sequence_frame_idx,
            'Horizontal interval': self.horizontal_interval,
            'Horizontal offset': self.horizontal_offset,
            'Timebase index': self.timebase_idx,
            'Timebase (s)': self.TIMEBASE_LIST[self.timebase_idx],
            'Vertical coupling index': self.vertical_coupling_idx,
            'Probe attenuation': self.probe_attenuation,
            'Bandwidth limit': self.bw_limit,
            'Source channel index': self.source_channel,
            'Source channel name': self.VALID_CHANNELS[self.source_channel]
        }
        return preamble_dict
    
    def _convert_data(self, raw_values):
        """
        The function converts raw bitstream of the waveform and converts it to voltage samples. 
        Additionally, it creates a properly scaled array of time samples.

        :param raw_values: A bitstream of raw waveform values.
        :return: Two arrays of for time samples and voltage samples.
        """
        if raw_values.size > 0:
            horizontal_grid_num = 10 # Specific for SDS800X HD model line
            voltage_levels = np.array(raw_values, dtype=np.float32)
            voltage_data = voltage_levels*(self.vertical_gain / self.code_per_div) - self.vertical_offset
            time_data = self.horizontal_offset - 0.5*horizontal_grid_num * self.timebase + np.arange(self.num_points)*self.horizontal_interval
            self.logger.debug('Conversion successful.')
            self.logger.debug(f'Voltage and time array lengths: {len(voltage_data)}, {len(time_data)}')
            return time_data, voltage_data
        else:
            self.logger.error('Raw data conversion failed. Received an empty waveform bitstream.')
            return None
    
    def get_waveform(self, update = True):
        """
        Retrieve the waveform data from the selected channel.
        
        :param update: Boolean flag. If true, then current parameters are read and stored in the class' fields.
        :return: Two numpy arrays containing time and voltage readings.
        """
        if not self.oscilloscope:
            self.logger.error("Oscilloscope is not connected.\n\t"
                              f"Resource name: {self.scope_address}")
            return None
        
        # Before reading the actual data,
        # we must read the current state of the oscilloscope's parameters.
        if update == True:
            self.read_preamble()

        try:

            # Retrieve the waveform
            self.oscilloscope.write(':WAV:WIDT WORD') # Use 'WORD' option to send datapoints in 16 bit words (used since 814X scope is 12 bit)
            self.logger.debug('Data format is set to 16-bit word')

            self.oscilloscope.write(':WAV:DATA?') # Ask to send data
            self.logger.debug('Waveform data requested')

            self.logger.debug('Requesting bitstream from the oscilloscope')
            raw_data = self.oscilloscope.read_raw().rstrip() # Read raw binary data
            if len(raw_data) > 0:
                self.logger.debug(f'Raw bistream has been received: {len(raw_data)}')
            else:
                self.logger.debug(f'Received an empty raw bitstream received')

            # Use timebase index to assign proper timebase set on the oscope panel
            self.timebase = self.TIMEBASE_LIST[self.timebase_idx]

            num_digits = int(struct.unpack('c', raw_data[1:2])[0]) #

            # Transfrom bitstream of 16 bit long words into an array of unsigned integers
            raw_values = np.frombuffer(raw_data, 
                                       offset=num_digits+2, 
                                       count=-1, 
                                       dtype=np.int16)
            self.logger.info('Waveform data retrieved.')
            self.logger.debug(f"Raw values array have: {len(raw_values)} points")

            return self._convert_data(raw_values)

        except pyvisa.VisaIOError as e:
            self.logger.error(f"Error retrieving waveform data.\n\t{e}")
            return None
        except ValueError as e:
            self.logger.error(f"Data conversion error.\n\t{e}")
            return None

    def close(self):
        """
        Close the connection to the oscilloscope.
        """
        if self.oscilloscope:
            try:
                self.oscilloscope.close()
                self.logger.info("Connection to the oscilloscope closed.")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Error closing connection to the oscilloscope.\n\t{e}")


