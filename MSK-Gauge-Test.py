import serial
from serial.rs485 import RS485Settings
import time

ser = serial.Serial(
    port='COM8',  # Replace with your port name, e.g., COM3 on Windows
    baudrate=19200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1,  # Timeout for reading/writing in seconds
)

# Configure RS485-specific settings
ser.rs485_mode = RS485Settings(
    rts_level_for_tx=True,  # Set RTS high during transmission
    rts_level_for_rx=False  # Set RTS low during reception
)

try:
    # Sending a command
    command = b'#02VER\r'
    ser.write(command)
    print(f"Sent: {command}")

    # Waiting and reading the response
    time.sleep(0.01)
    response = ser.read(16)  # Read expected number of bytes
    print(f"Received: {response}")

except serial.SerialException as e:
    print(f"Serial exception: {e}")

finally:
    # Close the serial port when done
    ser.close()


