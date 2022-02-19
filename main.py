"""
Greenhouse project - Adaptive humidification
Version 12. PID-regulator (Only P and I components implemented).

E.g.
https://www.amazon.com/Humidity-Controller-Inkbird-Humidistat-Pre-wired/dp/B01J1E5LWM
This one only turns on and turns off humidifier at defined values (it also controls
a dehumidifier if you have one). There is no actual control to how high or low
the humidity gets.
The same approach resulted in fluctuations of +-20% RH with my setup.

Notes on performance:
The humidity target was reached in five minutes and stayed within +-1.5% for the
remainder of the test (1.5 hours) for humidities 95% and below. For target
humidities above 95%, the target humidity was reached within 10 minutes and then
fluctuated a bit until settling from 20 minutes in within +-2% of target value.
Setting the target value to 99% resulted in the humidity, once reached, staying
above 97.1%.

Set TARGET_HUMIDITY to desired value. If you are using a fan or other ventilating
device, set FAE_RATE (otherwise set it to 0.0). If the humidity will not settle
around desired TARGET_HUMIDITY, you might need to adjust C_I and C_P. These
are the tuning parameters of the PI-controller.

PI-controller:
output = -C_P * proportional_error - C_I * integral_error
where
proportional_error = current_humidity - TARGET_HUMIDITY
integral_error = \sum_{0}^{now}(proportional_error)
(sum of proportional errors since start of device).

Reset
If the space is vented (e.g. door open) while the software is running, the
integral error will quickly increase and if the TARGET_HUMIDITY is high, it
will take a long time for the controller to reach equilibrium again.
90% RH: If the TARGET_HUMIDITY is 90%, opening the space will quickly reduce
the humidity to around 30%. The proportional error is then 60% and the integral
error will add this every cycle (10 seconds). After shutting the space,
the PID-controller will then blast the humidifier 100% of the time until
the correction starts to take effect. The maximal correction 10% points per
cycle, i.e. to correct for the error accumulated in one cycle will then take
6 cycles. Having the space open for e.g. 5 minutes will cause the controller to
be out of balance for 30 minutes!
95% RH: Keeping the space open for 5 minutes will require 1 hour to reset.
99% RH: Keeping the space open for 5 minutes will require 2.5 hours to reset
(with the hack of adding 1.0 to the error when hitting max humidity).
-There clearly is a need to handle this better. Otherwise the device will
need to be reset every time the space is opened. The code now resets the
controller if it has been hitting max humidity for 15 minutes. This is a
step in the right direction, but feels hacky. Reducing the time from 15 minutes
is also a bit risky, as setting the device for 99% RH took 10 minutes of
hitting >99.9% RH before it started stabilizing.
"""

import time
from machine import Pin
from DHT22 import DHT22

# Desired humidity in percent:
TARGET_HUMIDITY = 95.0

# Fresh air exchange in percent:
# With 70.0 the ventilator will be on 70% of the time.
# The ventilator is in the same cycle as the humidifier to make
# control of the humidification easier.
# E.g. a ventilator that pumps 2 liters or air per minute will
# replace the air twice per hour in a space that is 60 liters at
# 100%.
FAE_RATE = 70.0

# PID-controller parameters:
C_P = 2.0  # Coefficient for proportional error. 0.25 implies that an error of
# 100% would produce a 25% humidification rate next cycle.
C_I = 0.03  # Coefficient for integral error. A C_I of 0.01 indicates that an
# error of 40% over 100 seconds (10 cycles) would change the humidification rate
# by 4%.

# Time for one cycle. The humidifier and the ventilator are turned on and off
# once during this time and the humidification rate is re-estimated every cycle.
CYCLE_TIME = 10  # seconds
# Log info every 10 minutes and only temperature and humidity
SPARSE_LOGGING = True
LOG_COUNT = 0

# Hardware, connection pins for relays:
# Seems there is a clash with the screen (it is also using pins 6 and 7).
# I am thinking pins 20 and 21 should be safe choices.
RELAY_1_PIN = 6  # This is the relay above the usb-port
RELAY_2_PIN = 7  # This is the relay opposite from the usb-port


def control_humidity(verbose=False, test=False):
    """
    A function for controlling relay (and humidifier). Currently the
    mist from a humidifier is directed into a chamber with a little
    water on the bottom and the stones of a bubbler. The humidifier is
    on for humidification_rate * CYCLE_TIME, and the ventilator is
    on for FAE_RATE * CYCLE_TIME.

    Args:
    verbose (bool): Prints out metrics every cycle
    test (bool): If True, uses a fake generator to generate sensor
     readings. For testing purposes (without device).
    """
    # Humidifier runs in short cycles to keep humidity more constant.
    # See parameters at beginning of script for more details.
    if CYCLE_TIME < 2:
        print("Cycle time must be equal to or above 2 seconds to " +
              "ensure that the humidity sensor is reset every cycle.")
        raise Exception

    # Initialize relays:
    relay_1 = Pin(RELAY_1_PIN, Pin.OUT)
    relay_2 = Pin(RELAY_2_PIN, Pin.OUT)

    # Initialize sensor:
    if not test:
        sensor = DHT22(Pin(3, Pin.IN, Pin.PULL_UP))
    else:
        # For testing purposes
        sensor = FakeSensor()

    # Initialize cumulative (integral!) error:
    integral_err = 0.0
    reset_count = 0

    # Sleep 2 seconds to ensure sensor is ready.
    time.sleep_ms(2000)
    while True:
        # Continuous loop. Read sensor to estimate parameters
        temperature, current_humidity = sensor.read()

        # Proportional error:
        proportional_err =  current_humidity - TARGET_HUMIDITY
        if current_humidity > 99.9 and current_humidity > TARGET_HUMIDITY:
            # I.e. the DHT22 outputs max value
            # Add error to compensate for the discontinuous point
            # at and above 99.90001. This could potentially make
            # the device faster move away from humidity above
            # 99.9%.
            proportional_err += 1.0
            reset_count += 1
            if reset_count > 90:
                # The space has been externally vented and the
                # PID-controller needs to be reset. This is not meant
                # to happen accidentally, so the error should
                # continue for 15 minutes (900 seconds) before
                # this is called.
                integral_err = 0.0
                reset_count = 0
        else:
            reset_count = 0

        # Integral error. The integral error is estimated as a cumulative
        # sum (discrete approximation of integral).
        integral_err += proportional_err
        # The min-max is meant to clip the error at the point where
        # the integral part would keep the humidifier on for 100% of
        # the time or 0% of the time. If the setup contained a dehumidifier,
        # and the target humidity was below ambient air humidity, then
        # positive values should also be allowed.
        integral_err = min(0.0, max(-1 / C_I * 100, integral_err))

        # Combine the results:
        # PI-control (no derivative term)
        humidification_rate = - integral_err * C_I - proportional_err * C_P

        # Humidifier cannot be off for more than 0% of the time, nor on for more
        # than 100% of the time:
        humidification_rate = max(0.0, min(100.0, humidification_rate))
        
        # Log details
        if SPARSE_LOGGING:
            log_sparse_details(current_humidity, temperature)
        else:
            log_details(current_humidity, humidification_rate, proportional_err, integral_err)

        if verbose:
            print("=" * 40)
            print("Humidity: {}% RH".format(current_humidity))
            print("Proportional error: {}".format(proportional_err))
            print("Integral error: {}".format(integral_err))
            print("Humidification rate: {}% of cycle".format(humidification_rate))
            print("Fresh air rate: {}% of cycle".format(FAE_RATE))
            print("Cycle time: {} s".format(CYCLE_TIME))

        # Settings are re-estimated every cycle.
        sleep_time = CYCLE_TIME * 10 # sleep time as ms as there are 1000 iterations.
        for i in range(100):
            # Splitting one cycle in 1000 iterations
            if i < humidification_rate:
                relay_1.value(1)
            else:
                relay_1.value(0)
            if i < FAE_RATE:
                # Keep ventilator running
                relay_2.value(1)
            else:
                relay_2.value(0)
            time.sleep_ms(int(sleep_time))
        

def log_sparse_details(current_humidity,
                       current_temperature):
    """
    Sparse version of logging. Meant to save data
    only every 10 minutes to save space.
    """
    global LOG_COUNT
    LOG_COUNT += 1
    if LOG_COUNT >= 60:
        # 600 seconds have passed, i.e. 10 minutes.
        # Write to file.
        LOG_COUNT = 0
        try:
            with open('sparse_log.csv', 'r') as handle:
                # Just see if the file exists.
                # Throws an error if it does not.
                pass
            with open('sparse_log.csv', 'a') as handle:
                handle.write('"{}","{}"\n'.format(current_humidity,
                                                current_temperature))
        except OSError:
            # File did not exist. Write headers first.
            with open('sparse_log.csv', 'a') as handle:
                handle.write('"Humidity","Temperature"\n')
                handle.write('"{}","{}"\n'.format(current_humidity,
                                                current_temperature))


def log_details(current_humidity,
                humidification_rate,
                proportional_err,
                integral_err):
    """
    Function for logging info on humidity and state.
    
    Args:
    current_humidity (float): Last measured humidity
    humidification_rate (float): In [0, 100] [%]. How
     large part of the cycle the humidifier stays on.
    proportional_err (float): Last measured deviation from target
     humidity.
    integral (float): Accumulated error
    """
    try:
        # First check for existence of file. If it exists,
        # the below overwrites it (like when you are plugging
        # the Pico to your computer and it does not go into
        # REPL-model).
        with open('log.csv', 'r') as handle:
            # Do nothing. Throws an error if file does not exist.
            pass
        with open('log.csv', 'a') as handle:
            handle.write('"{}","{}","{}","{}"\n'.format(current_humidity,
                                                        humidification_rate,
                                                        proportional_err,
                                                        integral_err))
    except OSError:
        # Create file for logging:
        with open('log.csv', 'w') as handle:
            handle.write('"Humidity","Rate","Proportional error","Integral error"\n')
            handle.write('"{}","{}","{}","{}"\n'.format(current_humidity,
                                                        humidification_rate,
                                                        proportional_err,
                                                        integral_err))


class FakeSensor():
    """
    Fake temperature and humidity sensor class for
    testing purposes.
    """
    def __init__(self):
        # Does not need to do anything.
        pass

    def read(self):
        # Make up some reasonable number pair
        return 23, 55


def test():
    """
    Function for calling above with suitable test parameters.
    """
    global CYCLE_TIME
    CYCLE_TIME = 2.0
    control_humidity(True, True)


if __name__ == '__main__':
    # Run main program
    control_humidity()
