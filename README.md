# Greenhouse
*Software for Raspberry Pi Pico-based greenhouse automation.*

This software controls the power for a device (e.g. humidifier) based on humidity. The relay is controlled with a PID-controller (technically PI-controller as the derivative is not included). This setup reached the target RH of 93% in six minutes and kept a steady +-1.5% RH during the remainder of the test (1.5h). The setup consisted of a chamber (approx. 60l) that was not entirely airtight at the bottom, a humidifier connected with a hose to the upper part of the chamber, and the humidifier was controlled with the device described in this repository. A device for ventilation can also be controlled with the same software, but this was not included in the test to keep the setup as simple as possible.
The setup had difficulties keeping a steady humidity for target humidity of 98% RH, although 95% RH worked well. Further improvements migth be implemented later.

For comparison a test with the same setup where humidity was controlled so that the humidifier was turned on when the humidity dropped below 95% RH and turned off when it exceeded it was run. This resulted in maximum humidity hitting 100% RH and minimum value -10% of desired value. This is a common control logic for non-industrial humidifier control (e.g. https://www.amazon.com/Humidity-Controller-Inkbird-Humidistat-Pre-wired/dp/B01J1E5LWM).

The Raspberry Pi Pico *microcontroller* was chosen as Raspberry Pi *computers* werre sold out at the time of writing. The Pico is also easy to program and a much more beginner friendly than a Raspberry Pi computer.


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
- Instrictuions for setting PID-parameters (it might not work out of the box for every setup)
- ~~Adaptive algorithm for better control of humidity (done)~~
- ~~Ventilation (done)~~
- ~~Logging of sensor readings (done)~~

# Getting started with the Pico
https://hackspace.raspberrypi.com/books/micropython-pico/pdf/download
