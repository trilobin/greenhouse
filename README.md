# Greenhouse
*Software for Raspberry Pi Pico-based greenhouse automation.*

Currently in version 6 (development version). This can control the humidity better than previous versions. This software controls the power for a device (e.g. humidifier) based on humidity. The relay is controlled based on an adaptive algorithm that predicts the humidity if everything is kept constant and makes adjustments as needed.
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
- Adaptive algorithm for better control of humidity (work in progress, newest version already here!)
- Detailed build instructions for everything
- Touch screen: A touch screen would enable the device to be controlled during runtime and also give basic info on status
- Watering. Maybe directions on how to build a water level sensor with some hot glue, two wires, and suitable electronics to wire it up to a Raspberry Pi Pico.
- Light. Scheduled light cycle. The problem here is that the Pico does not come with a way to set the clock. Dependency: Screen (or buttons)
- Heat control
- Ventilation
~~- Logging of sensor readings (done)~~

# Getting started with the Pico
https://hackspace.raspberrypi.com/books/micropython-pico/pdf/download
