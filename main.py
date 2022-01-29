"""
Greenhouse project

Poll humidity every 30 seconds.
When humidity drops below threshold, turn on relay for
minute.
Wait for another 30 seconds and poll again.
"""

import utime
from machine import Pin
from DHT22 import DHT22

def control_humidity(verbose=False):
    """
    A simple function for turning on a relay if the humidity is too low.
    """
    # relay_1 = Pin(6, Pin.OUT)  # This is the relay above the usb-port
    relay_2 = Pin(7, Pin.OUT)  # This is the relay opposite from the usb-port
    sensor = DHT22(Pin(3, Pin.IN, Pin.PULL_UP))
    utime.sleep(10)
    
    while True:
        # Continuous loop
        temperature, humidity = sensor.read()
        if verbose:
            print("Humidity: {}".format(humidity))
            print("Temperature: {}".format(temperature))
        if humidity < 95.0:
            relay_2.value(1)
            # Keep it on for one minute
            utime.sleep(60)  # 4 seconds for testing purposes
            # Then turn it off
            relay_2.value(0)
        # Wait after humidifying before checking again
        utime.sleep(30)


if __name__ == '__main__':
    # Run main program
    control_humidity()

