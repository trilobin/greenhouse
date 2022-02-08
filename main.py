"""
Version 5. PID-regulator
-Integrator part is just sum over errors since day 1. It will
 need a well defined range to avoid "windup" (quite small).
 Also sampling schedule is important here.
 "Integrator should be limited to the range of the drive output",
 i.e. 0 to 60 seconds out of 1 minute cycle.
-Proportional part as is


Greenhouse project
Adaptive humidification. Discrete PID-regulator.

At start of humidification
If humidity too high but decreasing (projection close to correct) (since last cycle): leave as is
If humidity too high and constant, decrease humidification time (or increase break? maybe both start+stop=60)
If humidity too high and increasing, decrease humidification time
If humidity too low but increasing (projection getting close to correct): leave as is
If humidity too low and constant, increase humidification time
If humidity too low and decreasing, increase humidification time

Maybe use a taylor-series -like approach instead of PID?
"""

import utime
#import mutime
import time
from machine import Pin
from DHT22 import DHT22


def log_details(current_humidity,
                humidifier_on,
                humidification_time,
                cycle_time):
    """
    Function for logging details
    
    Args:
    current_humidity (float): Last measured humidity
    humidifier_on (bool): Whether the humidifier is on or not.
    humidification_time (int): How long the humidifier will be on
     in this cycle
    cycle_time (int): Time or humidification cycle
    """
    try:
        # First check for existence of file. If it exists,
        # the below overwrites it (like when you are plugging
        # the Pico to your computer and it does not go into
        # REPL-model).
        with open('log.csv', 'a') as handle:
            handle.write('"{}","{}","{}","{}"\n'.format(current_humidity,
                                                        humidifier_on,
                                                        humidification_time,
                                                        cycle_time))
    except:
        # Create file for logging:
        with open('log.csv', 'w') as handle:
            handle.write('"Humidity","ON/OFF","ON-time","Cycle time"\n')
            handle.write('"{}","{}","{}","{}"\n'.format(current_humidity,
                                                        humidifier_on,
                                                        humidification_time,
                                                        cycle_time))


def control_humidity(verbose=False):
    """
    A function for controlling relay (and humidifier). Nothing
    simple about this anymore.
    
    10 second cycle (humidifier on & off)
    Use PID-control do define how large part of the cycle should
    be "on."
    Proportional error (currently): (actual humidity) - (target humidity)
    Integral error: sum_0^{Now}(min(max_error, max(min_error, error_i)))
    Derivative: Predicting the future, if we are overshooting, this needs
     to be decreased etc.
    Constants:
    c_i: Constant for integral term
    c_p: constant for proportional term
    c_d: constant for derivative term

    Args:
    verbose (bool): Prints out metrics every cycle
    
    Notes:
    Perhaps implement a parabola with zero-point at humidity_target.
     That could serve as an adaptive coefficient?
    Cycle time might be way too short again. It is now fluctuating
    between 99.9 and 83% RH.
    """
    # Humidifier runs in short cycles to keep humidity constant better.
    cycle_time = 10  # seconds
    humidification_rate = 30  # % of the cycle
    # Can adjust the cycle times later if needed.

    # The actual target
    humidity_target = 95.0  # % RH. This is the target humidity.

    # Constants
    c_i = 0.0
    c_p = 5.0
    c_d = 0.0  # Turn of derivative term first
    max_integral = 20 # % of cycle time. Could be up to 100
    min_integral = -20 # % of cycle time. Could be down to -100
    integral_error = 0.0
    previous_error = 0.0
    
    # relay_1 = Pin(6, Pin.OUT)  # This is the relay above the usb-port
    relay_2 = Pin(7, Pin.OUT)  # This is the relay opposite from the usb-port
    sensor = DHT22(Pin(3, Pin.IN, Pin.PULL_UP))
    # Sleep 2 seconds to ensure sensor is ready.
    time.sleep_ms(2000)
    if cycle_time < 2:
        print("Cycle time must be above 2 seconds to " +
              "ensure that the humidity sensor is ready.")
        raise Exception

    while True:
        # Continuous loop
        temperature, humidity = sensor.read()
        log_details(humidity, True, 100, cycle_time)

        # Estimate PID parameters for next cycle:
        # Proportional part:
        error =  humidity - humidity_target
        # Integral part
        # We could also look into the entire cycle (10 measurements/cycle)
        integral_error += error
        integral_error = max(min_integral, min(max_integral, integral_error))
        # Derivative (rate of change)
        derivative_of_error = error - previous_error
        projected_error = error + error - previous_error
        # Store for next iteration
        previous_error = error

        humidification_rate -= c_i * integral_error + c_p * error +\
                               c_d * projected_error
        humidification_rate = max(10.0, min(40.0, humidification_rate))  # 50% to prevent wild fluctuations.
        # With min 0 and max 50%, the humidity stayed in 88-98%.

        """
        Make some "reset" if humidity exceeds 99.9%. For a PID-controller,
        that is a discountinuous point as no amount of humidity or no humidity
        changes anything. The droplets that have formed will keep the humidity
        high for a long time. Perhaps just wait it out? The PID-controller seems
        to handle it reasonably well.
        """
        """
        Perhaps limit change to 15-20% per minute? Could prevent the humidifier
        from flooding the room.
        With c_d 0.4 and c_p 5.0, min 10, max 40, the humidity fluctuated between
        71% and 97%.
        """

        if verbose:
            print("-" * 40)
            print("Humidity: {}% RH".format(humidity))
            print("Temperature: {} C".format(temperature))
            print("Humidification rate: {}% of cycle".format(humidification_rate))
            print("Cycle time: {} s".format(cycle_time))
            try:
                print("Min humidity in cycle: {}% RH".format(min_cycle_humidity))
                print("Max humidity in cycle: {}% RH".format(max_cycle_humidity))
            except:
                pass

        for i in range(int(cycle_time * humidification_rate)):
            # Turn humidifier on
            relay_2.value(1)
            time.sleep_ms(10)  # 0.01 seconds
            # Sensor needs 2 seconds to reset
            #temperature, humidity = sensor.read()
            #humidity_list.append(humidity)
        for i in range(int(cycle_time * (100 - humidification_rate))):
            relay_2.value(0)
            time.sleep_ms(10)
            #utime.sleep(2)
            #temperature, humidity = sensor.read()
            #humidity_list.append(humidity)


if __name__ == '__main__':
    # Run main program
    control_humidity()
