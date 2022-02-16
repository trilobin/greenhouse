"""
Greenhouse project - Adaptive humidification
Version 9. PID-regulator (Only P and I components in use now).

E.g.
https://www.amazon.com/Humidity-Controller-Inkbird-Humidistat-Pre-wired/dp/B01J1E5LWM
This one only turns on and turns off humidifier at defined values (it also controls
a dehumidifier if you have one). There is no actual control to how high or low
the humidity gets.
Trying the same approach resulted in fluctuations of +-20% RH.

Let's try a PI controller without the derivative term. And maybe set the
tuning parameters while aiming for 70% RH (instead of 95% RH) to prevent
the process from hitting 99.9% RH and flooding the space.

Maybe make the algorithm increase humidity in steps. If we start from 20% RH,
then first reach 50% and stabilize, then 70%, then 80%, then 90%, then 95%?
This would to some extent stabilize the system while trying to reach higher
values at the same time preventing the system from flooding. Flooding is
problematic as it is a discontinuous point from the viewpoint of the algorithm.

Reinforcement learning (with a neural net) would probably be quite good for this,
although collecting training data could take time.
"""

import time
from machine import Pin
from DHT22 import DHT22


def log_details(current_humidity,
                humidification_rate,
                error,
                integral_err):
    """
    Function for logging details
    
    Args:
    current_humidity (float): Last measured humidity
    humidification_rate (float): In [0, 100] [%]. How
     large part of the cycle the humidifier stays on.
    error (float): Last measured deviation from target
     humidity.
    integral (float): Accumulated error
    """
    try:
        # First check for existence of file. If it exists,
        # the below overwrites it (like when you are plugging
        # the Pico to your computer and it does not go into
        # REPL-model).
        with open('log.csv', 'a') as handle:
            handle.write('"{}","{}","{}","{}"\n'.format(current_humidity,
                                                        humidification_rate,
                                                        error,
                                                        integral_err))
    except:
        # Create file for logging:
        with open('log.csv', 'w') as handle:
            handle.write('"Humidity","Rate","Error","Integral error"\n')
            handle.write('"{}","{}","{}","{}"\n'.format(current_humidity,
                                                        humidification_rate,
                                                        error,
                                                        integral_err))


def linear_regression(t, y):
    """
    Ordinary least squares regression (univariate).
    Only the coefficient is needed.
    
    Args:
    t (float): Independent variable
    y (float): Dependent variable
    
    Notes:
    f(t) = coef * t + constant (\approx y)
    y = coef * t + constant + err
    err ~ N(0,.)
    min_{coef, constant) sum((f(t)-y)^2)

    Formulas from: https://datacadamia.com/data_mining/simple_regression#ordinary_least_squares_method
    -Perhaps the problem would be better modeled by a 2nd degree polynomial?
    """
    mean_t = sum([item for item in t]) / len(t)
    mean_y = sum([item for item in y]) / len(y)
    coef = sum([(item_1 - mean_t)*(item_2 - mean_y) for item_1, item_2
                in zip(t, y)]) /\
                sum([(item - mean_t)**2 for item in t])
    constant = mean_y - coef * mean_t
    return coef, constant


class FakeSensor():
    """
    Fake temperature and humidity class for
    testing purposes.
    """
    def __init__(self):
        # Does not need to do anything.
        pass

    def read(self):
        # Make up some reasonable number pair
        # Could use random numbers for more realistic
        # testing.
        return 23, 55


def control_humidity(verbose=False, test=False):
    """
    A function for controlling relay (and humidifier). Currently the
    mist from a humidifier is directed into a chamber with a little
    water on the bottom and the stones of a bubbler. The bubbler is
    on for humidification_rate * cycle time, and the humidifier is
    on for half of that.

    Currently using 10 second cycles. The devices are on for some
    fraction of that cycle and are reset at the end of it.

    Args:
    verbose (bool): Prints out metrics every cycle
    test (bool): If True, uses a fake generator to generate sensor
     readings. For testing purposes (without device).
         
    Perhaps estimate derivative by fitting f(t) \approx c * t + err and use
     c as estimate for derivative. Using three to five points would provide
     a more stable estimate this way. Do something similar for the second
     derivative.

    Make some "reset" if humidity exceeds 99.9%. For a PID-controller,
     that is a discountinuous point as no amount of humidity changes
     anything. The droplets that have formed will keep the humidity
     high for a long time. Perhaps just wait it out? The PID-controller seems
     to handle it reasonably well.

    If the humidity is much too low, maybe make the humidifier climb up to the
    set target humidity in steps? E.g. starting at 20% aim for 50%, when
    that is reached, change parameters to 70% etc to reach the desired
    humidity in a more controlled fashion.
    
    Perhaps separate control of airpump and humidifier. Airpump running time
    would be defined by desired FAE and humidifier running time would then
    be a function of both airpump running time and target humidity. The
    humidifier would still be controlled by a PI-controller, though.
    """
    # Humidifier runs in short cycles to keep humidity constant better.
    cycle_time = 10  # seconds
    humidification_rate = 20  # % of the cycle
    # Can adjust the cycle times later if needed.
    c_i = 0.06  # Coefficient for integral. 0.01 Implies that a 40%
    # change in the previous 1000 seconds results in a 4 % increase
    # in humidification time.
    # c_i 0.01 and c_p 1.0 produced a fairly stable humidity around
    # 70% RH (+3-2) and reached equilibrium in one hour. Trying
    # c_i 0.06 to perhaps reach equilibrium faster. c_p might also
    # work better with a higher value to more aggressively counter
    # fluctuations.
    c_p = 1.0  # Coefficient for error. 0.25 implies that an error of
    # 100% would produce a 40% humidification rate next cycle.
    c_d = 0.0  # Coefficient for derivative
    # As we are not estimating derivatives, updating settings every
    # cycle or every 2 cycles seems reasonable.
    # Must be at least 2 if we want to estimate derivative.
    n_loops = 2  # Number of loops between adjusting settings

    # The actual target
    humidity_target = 70.0  # % RH. This is the target humidity.
    
    relay_1 = Pin(6, Pin.OUT)  # This is the relay above the usb-port
    relay_2 = Pin(7, Pin.OUT)  # This is the relay opposite from the usb-port
    if not test:
        sensor = DHT22(Pin(3, Pin.IN, Pin.PULL_UP))
    else:
        sensor = FakeSensor()
    # Sleep 2 seconds to ensure sensor is ready.
    time.sleep_ms(2000)
    if cycle_time < 2:
        print("Cycle time must be above 2 seconds to " +
              "ensure that the humidity sensor is ready.")
        raise Exception

    # Log details before starting loop:
    temperature, humidity = sensor.read()
    # Store an empty line for "restart".
    log_details(humidity, 0, 0, 0)
    
    # Initialize list
    # 25% RH is somewhat typical indoor air humidity
    humidity_list = [25.0 for _ in range(n_loops)]
    integral_err = 0.0

    while True:
        # Continuous loop
        # Proportional error:
        error =  humidity - humidity_target
        # Derivative as regression coefficient (now equal to difference
        # between two last measure points).
        tmp = [humidity_list[i] - humidity_list[j] for i, j in
               zip(range(1, 2), range(0, 1))]
               #zip(range(6, 10), range(5, 9))]
        # The regression approach is meant to remove random fluctuations
        # (both fluctuations in the air and in measurement accuracy).
        coef, _ = linear_regression([0, 1, 2], humidity_list[-3:])
        derivative = coef

        # Integral error:
        tmp = [item - humidity_target for item in humidity_list]
        integral_err += sum(tmp)
        # The min-max is meant to clip the error at the point where
        # the integral part would keep the humidifier on for 100% of
        # the time or 0% of the time. If the setup contained a dehumidifier,
        # and the target humidity was below exchange air humidity, then
        # positive values should also be allowed.
        integral_err = min(0.0, max(-1 / c_i * 100, integral_err))

        # Combine the results (PI-control):
        humidification_rate = - integral_err * c_i - error * c_p
        #Reset lists:
        humidity_list = []

        humidification_rate = max(0.0, min(100.0, humidification_rate))

        if verbose:
            print("=" * 40)
            print("Humidity: {}% RH".format(humidity))
            print("Proportional error: {}".format(error))
            print("Integral error: {}".format(integral_err))
            print("Humidification rate: {}% of cycle".format(humidification_rate))
            print("Cycle time: {} s".format(cycle_time))

        for j in range(n_loops):
            # Settings are re-estimated every n_loops * cycle_time.
            tmp = int(cycle_time * humidification_rate)
            for i in range(int(cycle_time * humidification_rate)):
                # Keep humidifier on half of the time the air pump
                # is kept on:
                if i < tmp * .5:
                    relay_1.value(1)
                else:
                    relay_1.value(0)
                relay_2.value(1)
                time.sleep_ms(10)  # 0.01 seconds
            for i in range(int(cycle_time * (100 - humidification_rate))):
                relay_1.value(0)
                relay_2.value(0)
                time.sleep_ms(10)
            # Log details every cycle (every 10 seconds)
            temperature, humidity = sensor.read()
            log_details(humidity, humidification_rate, error, integral_err)
            humidity_list.append(humidity)
            if verbose:
                print("Humidity: {}".format(humidity))
        


if __name__ == '__main__':
    # Run main program
    control_humidity()
