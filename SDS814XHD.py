import pyvisa
import numpy as np
import struct
import logging


class SDS814XHD:
    """A class for interfacing with the SDS814XHD oscilloscope."""

    VALID_CHANNELS = ['C1', 'C2', 'C3', 'C4', 'F1', 'F2', 'F3', 'F4']
    
    TIMEBASE_LIST = [
        200e-12, 500e-12, 1e-9, 2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9,
        200e-9, 500e-9, 1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 
        200e-6, 500e-6, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 
        200e-3, 500e-3, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000
    ]

    def __init__(self, resource_name, alias='SDS814XHD', log_level='INFO'):
        """
        Initialize the oscilloscope class and establish connection.

        :param resource_name: VISA resource name for the oscilloscope.
        :param alias: Alias for logging.
        :param log_level: Level of logging.
        """
        self.LOG_FORMAT = f'%(asctime)s [%(levelname)s] {alias}: %(message)s'
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format=self.LOG_FORMAT, level=log_level)
        self.scope_address = resource_name

        try:
            self.rm = pyvisa.ResourceManager()
            self.oscilloscope = self.rm.open_resource(self.scope_address)
            self.oscilloscope.timeout = 3000
            self.logger.info(f"Connection established with the SDS814X HD oscilloscope."
                             f"\n\tResource address: {self.scope_address}"
                             f'\n\tID: {self.get_idn()}')
            self.read_preamble()
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Failed to connect to the oscilloscope.\n\t{e}')
            self.oscilloscope = None

    def get_idn(self):
        """
        Query the identification of the instrument.

        :return: Identifier string if query is successful or None otherwise.
        """
        try:
            return self.oscilloscope.query('*IDN?')
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Error retrieving identification: {e}')
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
            self.logger.error(f"Error querying the current channel: {e}")
            return None

    def set_channel(self, channel='C1'):
        """
        Select the channel from which to read data.

        :param channel: Channel number can be C1, C2, C3, C4, F1, F2, F3, F4. Default 'C1'.
        :return: Returns 0 if successful, 1 if ended with error.
        """
        if self.is_valid_channel(channel):
            try:
                self.oscilloscope.write(f'WAV:SOUR {channel}')
                self.logger.info(f"Active channel: {channel}")
            except pyvisa.VisaIOError as e:
                self.logger.error(f"Failed to set channel: {e}")
                return 1
        else:
            self.logger.warning(f"Invalid channel name '{channel}'. "
                                f"Valid channels: {', '.join(self.VALID_CHANNELS)}.")
            current_channel = self.get_current_channel()
            if current_channel:
                self.logger.warning(f"Falling back to the current channel: {current_channel}.")
            return 1
        return 0

    def get_number_of_points(self):
        """
        Retrieve the number of sampled points of the current waveform.

        :return: Integer number of sampled points.
        """
        try:
            return int(float(self.oscilloscope.query('ACQ:POIN?').strip()))
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Error retrieving the number of points: {e}')
            return None

    def read_preamble(self):
        """
        Read and parse the preamble string to extract waveform parameters.
        """
        try:
            self.logger.debug('Requesting preamble from the oscilloscope.')
            self.oscilloscope.write(':WAV:PRE?')
            preamble = self.oscilloscope.read_raw()
            n_skip = 11  # Skip header bits
            self.logger.debug('Unpacking the preamble bitstream.')


            self.num_points = struct.unpack('l', preamble[n_skip+116:n_skip+120])[0]
            self.first_point = struct.unpack('l', preamble[n_skip+132:n_skip+136])[0]
            self.data_interval = struct.unpack('l', preamble[n_skip+136:n_skip+140])[0]
            self.read_frames = struct.unpack('l', preamble[n_skip+144:n_skip+148])[0]
            self.sum_frames = struct.unpack('l', preamble[n_skip+148:n_skip+152])[0]
            self.vertical_gain = struct.unpack('f', preamble[n_skip+156:n_skip+160])[0]
            self.vertical_offset = struct.unpack('f', preamble[n_skip+160:n_skip+164])[0]
            self.code_per_div = struct.unpack('f', preamble[n_skip+164:n_skip+168])[0]
            self.adc_bit = struct.unpack('h', preamble[n_skip+172:n_skip+174])[0]
            self.sequence_frame_idx = struct.unpack('h', preamble[n_skip+174:n_skip+176])[0]
            self.horizontal_interval = struct.unpack('f', preamble[n_skip+176:n_skip+180])[0]
            self.horizontal_offset = struct.unpack('d', preamble[n_skip+180:n_skip+188])[0]
            self.timebase_idx = struct.unpack('h', preamble[n_skip+324:n_skip+326])[0]
            self.vertical_coupling_idx = struct.unpack('h', preamble[n_skip+326:n_skip+328])[0]
            self.probe_attenuation = struct.unpack('f', preamble[n_skip+328:n_skip+332])[0]
            self.bw_limit = struct.unpack('h', preamble[n_skip+334:n_skip+336])[0]
            self.source_channel = struct.unpack('h', preamble[n_skip+344:n_skip+346])[0]

            self.timebase = self.TIMEBASE_LIST[self.timebase_idx]
            self.logger.debug(f'First point: {self.first_point}, '
                              f'Number of points: {self.num_points}, '
                              f'Data interval: {self.data_interval}, '
                              f'Frames read: {self.read_frames}')
            self.logger.info('Preamble updated.')
        except pyvisa.VisaIOError as e:
            self.logger.error(f'Error retrieving the preamble: {e}')
    
    def get_preamble_dict(self):
        """
        Form a dictionary from the oscilloscope parameters after reading the preamble.

        :return: Dictionary of the oscilloscope's parameters.
        """
        return {
            'Number of points': self.num_points,
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
            'Timebase (s)': self.timebase,
            'Vertical coupling index': self.vertical_coupling_idx,
            'Probe attenuation': self.probe_attenuation,
            'Bandwidth limit': self.bw_limit,
            'Source channel index': self.source_channel,
            'Source channel name': self.VALID_CHANNELS[self.source_channel]
        }

    def _convert_data(self, raw_values):
        """
        Convert raw waveform data to voltage samples and create time samples.

        :param raw_values: A bitstream of raw waveform values.
        :return: Two arrays of time samples and voltage samples.
        """
        if raw_values.size > 0:
            horizontal_grid_num = 10  # Specific for SDS800X HD model line
            voltage_levels = np.array(raw_values, dtype=np.float32)
            voltage_data = (voltage_levels * (self.vertical_gain / self.code_per_div) 
                            - self.vertical_offset)
            time_data = (self.horizontal_offset 
                         - 0.5 * horizontal_grid_num * self.timebase 
                         + np.arange(self.num_points) * self.horizontal_interval)
            self.logger.debug('Conversion successful.')
            return time_data, voltage_data
        else:
            self.logger.error('Raw data conversion failed: empty bitstream.')
            return None

    def get_waveform(self, update=True):
        """
        Retrieve waveform data from the selected channel.

        :param update: If true, update oscilloscope parameters.
        :return: Two numpy arrays of time and voltage readings.
        """
        if not self.oscilloscope:
            self.logger.error(f"Oscilloscope not connected. Resource: {self.scope_address}")
            return None

        if update:
            self.read_preamble()

        try:
            self.oscilloscope.write(':WAV:WIDT WORD')  # Set to 16-bit words
            self.logger.debug('Set data format to 16-bit words.')

            self.oscilloscope.write(':WAV:DATA?')
            self.logger.debug('Requested waveform data.')

            raw_data = self.oscilloscope.read_raw().rstrip()
            self.logger.debug(f'Received raw bitstream: {len(raw_data)} bytes.')

            num_digits = int(struct.unpack('c', raw_data[1:2])[0])

            raw_values = np.frombuffer(raw_data, offset=num_digits + 2, dtype=np.int16)
            self.logger.info('Waveform data retrieved.')
            return self._convert_data(raw_values)

        except (pyvisa.VisaIOError, ValueError) as e:
            self.logger.error(f"Error retrieving waveform data: {e}")
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
                self.logger.error(f"Error closing connection: {e}")



