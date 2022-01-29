# Greenhouse
*Software for Pico-based greenhouse automation.*

This initial version can control the power for a device (e.g. humidifier) based on humidity. Once the humidity drops below some threshold (95% RH in the code), the relay is turned on for one minute. The Raspberry Pi Pico *microcontroller* was chosen as Raspberry Pi *computers* werre sold out at the time of writing. The Pico is also easy to program and a much more beginner friendly than a Raspberry Pi computer.


## Bill of materials
- Raspberry Pi Pico: https://thepihut.com/collections/raspberry-pi/products/raspberry-pi-pico
- Headers for Pico: https://thepihut.com/products/stacking-header-set-for-raspberry-pi-pico
- Humidity and temperature sensor DHT22: https://thepihut.com/products/am2302-wired-dht22-temperature-humidity-sensor
- Relay board: https://thepihut.com/products/dual-channel-relay-hat-for-raspberry-pi-pico


## External libraries
The DHT22.py -file from this library needs to be uploaded to your Pico:
https://github.com/danjperron/PicoDHT22/blob/main/DHT22.py

# Future plans
- Adaptive algorithm for better control of humidity
- Logging of sensor readings
- Build instructions for everything
- Touch screen: A touch screen would enable the device to be controlled during runtime and also give basic info on status
- Watering. Maybe directions on how to build a water level sensor with some hot glue, two wires, and suitable electronics to wire it up to a Raspberry Pi Pico.
- Light. Scheduled light cycle. The problem here is that the Pico does not come with a way to set the clock. Dependency: Screen (or buttons)
- Heat control
- Ventilation

# Get started with the Pico
https://hackspace.raspberrypi.com/books/micropython-pico/pdf/download
