# ESP MicroPython Setup Utility
A utility for flashing firmware images of micro python to the ESP32/8266 and for uploading software to the filesystem.

![alt text](https://github.com/seth-c-stenzel/ESP-MicroPython-Setup-Utility/blob/main/screenshots/ESP%20MicroPython%20Setup%20Utility.jpg?raw=true)

## INTRO
This utility is meant as an easy way to flash new firmware images to an ESP as well as easily upload MicroPython files to that board after.
It is a simple GUI for flashing and uploading software packages which some could find useful, especially when distributing MicroPython packages.

## ON THE SHOULDERS OF GIANTS
This utility imports other utilities such as esptool, as well as taking modifying some upload scripts intended for the pyboard.
While I have tested the utility on a few ESP32's, I can not vouch for it's effectiveness in flashing boards such as the ESP32-** variants. As I don't have these boards. Want a board to be supported, reach out to me and send me one :)

## Usage
This utility can be used to flash firmware only, a software package only, which is a zip folder with desired MicroPython file system, or both simultaneously.

1. Start the utility.
2. Select your serial port.
3. Select your firmware file, you want to update, if any.
4. Select a software package, you want to update, if any. (see notes below)
5. If not flashing firmware, check the software-only checkbox.
6. Select your board from the drop down, or input it yourself.
7. Click install

## Notes
Concerning the software package / zip archive. The root of the zip archive is relational to the root of the ESP, you'll just need to keep that in mind that you would not zip your project folder, you would ctrl+a everything in the folder, and add that to an archive.

The original version I made for work is for does not have the chip select, buad, and offset selection since it is used for a POC device with a spesific board and we wanted it to be as easy as possible for our testers to update the device.

I have only tested this against a handful of ESP32's and ESP8266's so if you come accross a bug for a baord, open an issue. If the board is only $10 USD or something I'll pick it up and try and make sure things work with it.
