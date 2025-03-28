import serial
import time

# Change COM port to match your ESP8266 (e.g., COM3, /dev/ttyUSB0)
SERIAL_PORT = "COM6"  # Windows Example: "COM3", Linux/Mac Example: "/dev/ttyUSB0"
BAUD_RATE = 115200  # Must match ESP8266 Serial.begin(115200)

try:
    # Open Serial Connection
    esp = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for ESP8266 to initialize

    while True:
        command = input("Enter Command (RIGHT-ON, RIGHT-OFF, LEFT-ON, LEFT-OFF, STOP): ").strip()

        if command in ["RIGHT-ON", "RIGHT-OFF", "LEFT-ON", "LEFT-OFF", "STOP"]:
            esp.write((command + "\n").encode())  # Send command via Serial
            print(f"Sent: {command}")
        else:
            print("Invalid command! Use: RIGHT-ON, RIGHT-OFF, LEFT-ON, LEFT-OFF, STOP")

except serial.SerialException as e:
    print(f"Serial Error: {e}")

except KeyboardInterrupt:
    print("\nProgram terminated by user.")

finally:
    if 'esp' in locals():
        esp.close()  # Close Serial connection when exiting