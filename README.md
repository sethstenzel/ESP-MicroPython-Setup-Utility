# ESP MicroPython Setup Utility
A utility for flashing firmware images of micro python to the ESP32/8266 and for uploading software to the filesystem.

## INTRO
This utility is meant as an easy way to flash new firmware images to and ESP as well as easily upload micropython files to that board after.
It is a simple GUI for flashing and uploading software packages which some could find useful especially when distributing MicroPython packages.

## ON THE SHOULDERS OF GIANTS
This utiliy imports other utilities such as esptool, as well as taking modifying some upload scripts intended for the pybaord.
While I have tested the utility on a few ESP32's, I can not vouche for it's effectiveness in flashing boards such as the ESP32-** varients. As I don't have these boards. Want a baord to be support, reach out to me and send me one :)

## Usage
This utility can be used to flash a firmware only, a software package only, which is a zip folder withe desired micropython file system, or both at the same time.

1. Start the utility.
2. Select your serial port.
3. Select your firmware file.
4. Select a software package if any. (see notes below)
5. If not flashing firmware, check the software only checkbox.
6. If flashing an 8266 select the 8266 checkbox (adjusts the flash offset value.)
7. Click install

