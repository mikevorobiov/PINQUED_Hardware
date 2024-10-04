import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


from HP34401A import *
from GPP25045 import *
from U1252B import *


import pyvisa
import time


rm = pyvisa.ResourceManager()

dmm_grid_hp = HP34401A(rm, 'visa://192.168.194.15/ASRL9::INSTR', alias='GridAmp', log_level='INFO')
psu = GPP25045(rm, 'visa://192.168.194.15/ASRL5::INSTR', alias='PSU1', log_level='INFO')

time.sleep(0.5)
dmm_grid_hp.write('SYST:REM')
time.sleep(0.5)
dmm_grid_hp.write('FUNC:CURR:DC 0.00001,0.00000001')
time.sleep(0.5)

NPLCycles = 100
dmm_grid_hp.write(f'CURR:DC:NPLC {NPLCycles}')

anode_current = []
grid_current = []


psu.toggle_output(True)

voltage = np.round( np.linspace(0,1,40)**2 * 30, decimals=2)
try:
    for v in voltage:
        psu.set_voltage(v)

        time.sleep((NPLCycles+1)/60)

        grid_current_reading = float(dmm_grid_hp.query('READ?').strip())
        grid_current.append(grid_current_reading)

except KeyboardInterrupt:
    print("Script interrupted by user.")

psu.toggle_output(False)
dmm_grid_hp.close()
psu.close()

np.savetxt('./data_2024-10-03.csv', np.transpose(np.vstack((voltage, grid_current))), header='Grid Voltage (V),Grid Current (A)', delimiter=',')

fig, ax = plt.subplots()
ax.plot(voltage, grid_current, linestyle='None', marker='o')
plt.show()


