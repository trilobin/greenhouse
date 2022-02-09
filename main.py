"""
Version 6. PID-regulator

Greenhouse project
Adaptive humidification. Discrete PID-regulator.

At start of humidification
If humidity too high but decreasing (projection close to correct) (since last cycle): leave as is
If humidity too high and constant, decrease humidification time (or increase break? maybe both start+stop=60)
If humidity too high and increasing, decrease humidification time
If humidity too low but increasing (projection getting close to correct): leave as is
If humidity too low and constant, increase humidification time
If humidity too low and decreasing, increase humidification time

Control based on projected error which is calculated from current error,
derivative of error, and second derivative of error.

Perhaps make changes slow when approaching the humidity limit from below
but large when exceeding it. This would serve to slowly build up to the desired
humidity and then keeping it there, rather than having it run away. Maybe.

Alternatively binary search could be used to look for optimal humidification time.
It would need to be "restarted" or somehow backtracked from time to time.
"""

import time
from machine import Pin
from DHT22 import DHT22


def log_details(current_humidity,
                humidification_rate,
                error,
                derivative,
                second_derivative,
                projected_error,
                change):
    """
    Function for logging details
    
    Args:
    current_humidity (float): Last measured humidity
    humidification_rate (float): In [0, 100] [%]. How
     large part of the cycle the humidifier stays on.
    error (float): Last measured deviation from target
     humidity.
    derivative (float): Estimated change rate in humidity
     in a 10 second cycle.
    second_derivative (float): Estimated change of change
     (derivative) in last two cycles (20 seconds).
    change (float): Last adjustement to humidification rate.
    """
    try:
        # First check for existence of file. If it exists,
        # the below overwrites it (like when you are plugging
        # the Pico to your computer and it does not go into
        # REPL-model).
        with open('log.csv', 'a') as handle:
            handle.write('"{}","{}","{}","{}","{}","{}","{}"\n'.format(current_humidity,
                                                                       humidification_rate,
                                                                       error,
                                                                       derivative,
                                                                       second_derivative,
                                                                       projected_error,
                                                                       change))
    except:
        # Create file for logging:
        with open('log.csv', 'w') as handle:
            handle.write('"Humidity","ON/OFF","ON-time","Cycle time"\n')
            handle.write('"{}","{}","{}","{}","{}","{}","{}"\n'.format(current_humidity,
                                                                       humidification_rate,
                                                                       error,
                                                                       derivative,
                                                                       second_derivative,
                                                                       projected_error,
                                                                       change))


def control_humidity(verbose=False):
    """
    A function for controlling relay (and humidifier). Nothing
    simple about this anymore.
    
    10 second cycle (humidifier on & off)
    Adjusting settings every 10 cycles

    Args:
    verbose (bool): Prints out metrics every cycle
    
    Notes:
    Perhaps implement a parabola with zero-point at humidity_target.
     That could serve as an adaptive coefficient?
     Essentially some kind of variable coefficient for change
     could stabilize the system.
     Currently there is a "hinge-loss" -like solution for this.
     
    Perhaps estimate derivative by fitting f(t) \approx c * t + err and use
     c as estimate for derivative. Using three to five points would provide
     a more stable estimate this way. Do something similar for the second
     derivative.

    Make some "reset" if humidity exceeds 99.9%. For a PID-controller,
     that is a discountinuous point as no amount of humidity changes
     anything. The droplets that have formed will keep the humidity
     high for a long time. Perhaps just wait it out? The PID-controller seems
     to handle it reasonably well.

    Perhaps limit change to 15-20% per minute? Could prevent the humidifier
     from saturating the room.
    With c_d 0.4 and c_p 5.0, min 10, max 40, the humidity fluctuated between
     71% and 97%.
    """
    # Humidifier runs in short cycles to keep humidity constant better.
    cycle_time = 10  # seconds
    humidification_rate = 20  # % of the cycle
    # Can adjust the cycle times later if needed.
    c_e = 1.0  # Coefficient for error
    c_d = 1.0  # Coefficient for derivative
    c_dd = 0.7  # Coefficient for second derivative
    # A more accurate estimate of the second derivative would be super
    # useful, but the sensor will not do that. So it might be better
    # to just use less weight for this. On average, it will still be
    # allright.
    n_loops = 10  # Number of loops between adjusting settings

    # The actual target
    humidity_target = 95.0  # % RH. This is the target humidity.
    
    # relay_1 = Pin(6, Pin.OUT)  # This is the relay above the usb-port
    relay_2 = Pin(7, Pin.OUT)  # This is the relay opposite from the usb-port
    sensor = DHT22(Pin(3, Pin.IN, Pin.PULL_UP))
    # Sleep 2 seconds to ensure sensor is ready.
    time.sleep_ms(2000)
    if cycle_time < 2:
        print("Cycle time must be above 2 seconds to " +
              "ensure that the humidity sensor is ready.")
        raise Exception

    # Log details before starting loop:
    temperature, humidity = sensor.read()
    # Store an empty line for "restart".
    log_details(humidity, 0, 0, 0, 0, 0, 0)

    humidity_list = [0.0, 0.0, 0.0]
    while True:
        # Continuous loop

        # Proportional part:
        error =  humidity - humidity_target
        # Derivative (change during last 10 seconds)
        derivative = humidity_list[-1] - humidity_list[-2]
        # Second derivative
        second_derivative = derivative - (humidity_list[-2] - humidity_list[-3])
        # Projection based on these three for the end of next cycle:
        # Project over 10 cycles, one full loop:
        # Could dampen the effect of derivative and especially second derivative.
        # n_loops * d is the amount of error the derivative will introduce in the same
        # number of loops. factorial(n_loops) * s-d is the amount of error the second
        # derivative will introduce in n_loops.
        # factorial(n_loops) would hypothetically be correct, but factorial(10)
        # =3628800... I.e. it would make the system hyper sensitive (and unstable).
        projected_error = c_e * error +\
                          (c_d * n_loops * derivative +
                           + c_dd * n_loops * second_derivative)
        # This approximation is rather ad hoc:
        # Could e.g. be averages from the last 10 iterations
        #humidification_velocity = humidity / humidification_rate
        humidification_velocity = 4  # Constant based on your setup.
        # Flip sign becasue we want to fix the error
        change = -projected_error / humidification_velocity
        # Hinge-loss:
        if humidity < humidity_target and change > 0:
            # Just make half of the needed change. Approach
            # desired value slowly.
            change *= 0.5
        elif humidity > humidity_target and change < 0:
            change *= 4
        humidification_rate += change
        # Reset lists:
        humidity_list = []

        humidification_rate = max(5.0, min(50.0, humidification_rate))
        # With min 5 and max 50%, the humidity stayed in 88-98%.


        if verbose:
            print("=" * 40)
            print("Humidity: {}% RH".format(humidity))
            print("Temperature: {} C".format(temperature))
            print("Humidification rate: {}% of cycle".format(humidification_rate))
            print("Cycle time: {} s".format(cycle_time))
            try:
                print("Min humidity in cycle: {}% RH".format(min_cycle_humidity))
                print("Max humidity in cycle: {}% RH".format(max_cycle_humidity))
            except:
                pass
            print("-" * 40)
            print("Error: {}".format(error))
            print("Derivative: {}".format(derivative))
            print("Second derivative: {}".format(second_derivative))
            print("Projected error: {}".format(projected_error))
            print("Change: {}".format(change))
            print("New humidification_rate: {}".format(humidification_rate))
            print("-" * 40)

        for j in range(n_loops):
            # cycle_time is 10 seconds. With 10 iterations, that
            # makes for 100 seconds.
            for i in range(int(cycle_time * humidification_rate)):
                # Turn humidifier on
                relay_2.value(1)
                time.sleep_ms(10)  # 0.01 seconds
            for i in range(int(cycle_time * (100 - humidification_rate))):
                relay_2.value(0)
                time.sleep_ms(10)
            # Log details every cycle (every 10 seconds)
            temperature, humidity = sensor.read()
            log_details(humidity, humidification_rate, error, derivative,
                        second_derivative, projected_error, change)
            humidity_list.append(humidity)
            if verbose:
                print("Humidity: {}".format(humidity))
        


if __name__ == '__main__':
    # Run main program
    control_humidity()
