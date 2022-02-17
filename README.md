# Greenhouse
*Software for Raspberry Pi Pico-based greenhouse automation.*

This software controls the power for a device (e.g. humidifier) based on humidity. The relay is controlled with a PID-controller (technically PI-controller as the derivative is not included). 
The Raspberry Pi Pico *microcontroller* was chosen for this project as Raspberry Pi *computers* werre sold out at the time. The Pico is also easy to program and much more beginner friendly than a Raspberry Pi computer.
This software can control both a humidifier and a ventilator. If both are used, controlling them both by the same software will prevent the ventilator from destabilizing the humidity whenever it turns on.


## Performance notes
This setup reached target humidities of 95% RH and below in five minutes from start and kept a steady humidity within +-1.5% of target RH after that. For target humidities above 95%, the target humidity was typically reached in 10 minutes followed by some fluctuation, and the humidity stayed within +-2% after the first 20 minutes. Setting the target humidity to 99% resulted in the humidity staying between 97.1% and 100% without flooding the chamber. No condensation formed on the walls during a 1.5 hour test run.
The setup consisted of a chamber (approx. 60l) that was not entirely airtight at the bottom, a humidifier connected with a hose to the upper part of the chamber, and the humidifier was controlled with the device described in this repository. A device for ventilation can also be controlled with the same software, but this was not included in the test to keep the setup as simple as possible.

For comparison a test with the same setup where humidity was controlled so that the humidifier was turned on when the humidity dropped below 95% RH and turned off when it exceeded the same value was run. This resulted in maximum humidity hitting 100% RH and a minimum value of -10% below desired value. This is a common control logic for non-industrial humidifier control (e.g. https://www.amazon.com/Humidity-Controller-Inkbird-Humidistat-Pre-wired/dp/B01J1E5LWM).


## Assembly
- Solder the headers to the Pico
- Connect the data wire (yellow) of the DHT22-sensor to pin GPIO 3, the red wire to 3V3(OUT), and the black wire to GND. You might want to consider connecting the DHT22-cables to jumper wires and the jumper wires to the board.
- Attach the relay board
- Cut one of the two cables in the power line of the humidifier and connect the ends to COM and NO on the relay opposite to the USB-port. If you do not know what you are doing here, find a friend who does. Don't burn down your house. Depending on the power line, you will have anywhere between 12V and 230V running in that cable. Put everything in a box so that you will not accidentally touch this during operation.
- Upload the .uf2-file to your Pico (see "Getting started with the Pico" below)
- Upload main.py and DHT22.py to the Pico (see "Getting started with the Pico" below)
- Put the sensor and humidifier in a greenhouse and plug in the power. Remember that the Pico also needs power through the USB-port.
- The humidifier will now run whenever the relative humidity drops below 95%.


## Bill of materials
- Raspberry Pi Pico: https://thepihut.com/collections/raspberry-pi/products/raspberry-pi-pico
- Headers for Pico: https://thepihut.com/products/stacking-header-set-for-raspberry-pi-pico
- Humidity and temperature sensor DHT22: https://thepihut.com/products/am2302-wired-dht22-temperature-humidity-sensor
- Relay board: https://thepihut.com/products/dual-channel-relay-hat-for-raspberry-pi-pico
- Jumpers (optional): https://thepihut.com/products/premium-female-male-extension-jumper-wires-20-x-6


## External libraries
The DHT22.py -file from this repository needs to be uploaded to your Pico:
https://github.com/danjperron/PicoDHT22/blob/main/DHT22.py

# Backlog
- Touch screen: A touch screen would enable the device to be controlled during runtime and also give basic info on status
- Detailed build instructions for everything
- Watering. Maybe directions on how to build a water level sensor with some hot glue, two wires, and suitable electronics to wire it up to a Raspberry Pi Pico.
- Light. Scheduled light cycle. The problem here is that the Pico does not come with a way to set the clock. Dependency: Screen (or buttons)
- Heat control
- Instructions for setting PID-parameters (it might not work out of the box for every setup)
- ~~Adaptive algorithm for better control of humidity (done)~~
- ~~Ventilation (done)~~
- ~~Logging of sensor readings (done)~~

# Getting started with the Pico
https://hackspace.raspberrypi.com/books/micropython-pico/pdf/download
