import PySimpleGUI as sg
import os.path
from zipfile import ZipFile
from tempfile import TemporaryDirectory
from serial_tools import get_com_ports
from serial_tools import port_is_avaiable
import esptool
import pyboard
import os
import pyb_files
from pyb_files import DirectoryExistsError
import pathlib
import sys
import time
from simple_timer import SimpleTimer
from pyboard import PyboardError

APP_NAME = "ESP MicroPython Setup Utility (v1.0.7)"

CHIPS = [
    "esp8266",
    "esp32",
    "esp32s2",
    "esp32s3beta2",
    "esp32s3",
    "esp32c3",
    "esp32c6beta",
    "esp32h2beta1",
    "esp32h2beta2",
    "esp32c2",
    "esp32c6",
]

BAUD_RATES = [9600, 19200, 28800, 38400, 57600, 115200, 230400, 460800, 576000, 921600]

COMMON_COM_CHIP_SAFE_BAUD_RATES = {
    "ch340": 921600,
}

FLASH_OFFSETS = ["0x0", "0x1000"]

# This has to do with how pyinstaller links files
if hasattr(sys, "_MEIPASS"):
    app_icon = sys._MEIPASS + "/logo.ico"
else:
    app_icon = "logo.ico"


sg.theme("SystemDefault")

com_ports_available = list()
default_com_port = None
default_baud_rate = None
for com_port_entry in get_com_ports():
    com_ports_available.append(
        f"{com_port_entry[0]}{(5 - len(com_port_entry[0])) * ' '} : {com_port_entry[1]}"
    )
for port in com_ports_available:
    if "CH340" in port.upper():
        default_com_port = port
        default_baud_rate = 921600
        break
    elif "CP210" in port.upper():
        default_com_port = port
        default_baud_rate = 921600
        break
    else:
        default_com_port = com_ports_available[0]


layout = [
    [sg.Text("Serial Port", font=("Courier New", 12))],
    [
        sg.Combo(
            com_ports_available,
            default_value=default_com_port,
            font=("Courier New", 10),
            size=(60, 1),
            key="port",
        )
    ],
    [sg.Text("Firmware Image", font=("Courier New", 12))],
    [
        sg.InputText(font=("Courier New", 10), size=(50, 1), key="firmware"),
        sg.FileBrowse(
            font=("Courier New", 10),
            size=(10, 1),
            file_types=(("Firmware Image", "*.bin"),),
        ),
    ],
    [sg.Text("Software Package", font=("Courier New", 12))],
    [
        sg.InputText(font=("Courier New", 10), size=(50, 1), key="software"),
        sg.FileBrowse(
            font=("Courier New", 10),
            size=(10, 1),
            file_types=(("Software Package", "*.zip"),),
        ),
    ],
    [sg.Text("Chip Select   Baud Rate     Flash Offset", font=("Courier New", 12))],
    [
        sg.Combo(
            CHIPS,
            default_value=CHIPS[0],
            font=("Courier New", 10),
            size=(14, 1),
            key="chip",
        ),
        sg.Combo(
            BAUD_RATES,
            default_value=default_baud_rate or 115200,
            font=("Courier New", 10),
            size=(14, 1),
            key="baud_rate",
        ),
        sg.Combo(
            FLASH_OFFSETS,
            default_value="0x0",
            font=("Courier New", 10),
            size=(14, 1),
            key="flash_offset",
        ),
    ],
    [
        sg.Checkbox(
            "Software upload only (skip erase & flash)", default=False, key="skip"
        )
    ],
    [
        sg.Button("Install", font=("Courier New", 12), size=(10, 3)),
        sg.Multiline(
            font=("Courier New", 10),
            no_scrollbar=True,
            disabled=True,
            size=(48, 4),
            key="output",
            autoscroll=True,
        ),
    ],
]

window = sg.Window(APP_NAME, icon=app_icon).Layout(layout)

while True:
    try:
        event, values = window.read()
        if event == "Install":
            output_text = ""
            window["output"].update(output_text)
            port = values["port"].split(":")[0].strip()
            firmware = values["firmware"].replace("'", "").replace('"', "")
            software = values["software"].replace("'", "").replace('"', "")
            if not port:
                print("ERROR: missing port.\n")
                window["output"].update("ERROR: missing port.\n", append=True)
                window.refresh()
                continue

            if not port_is_avaiable(port):
                window["output"].update("ERROR: port is unavailable.\n", append=True)
                window["output"].update(
                    "(port is already in use or device is no longer connected)\n",
                    append=True,
                )
                window.refresh()
                continue

            if not firmware and not values["skip"]:
                print("ERROR: missing firmware image.\n")
                window["output"].update("ERROR: missing firmware image.\n", append=True)
                continue

            window.Hide()

            total_timer = SimpleTimer()
            total_timer.start()
            timer = SimpleTimer()

            if not values["skip"]:
                print("Erasing Flash.\n")
                window["output"].update("Erasing Flash.\n", append=True)
                window.refresh()
                if str(values["baud_rate"]) in str(BAUD_RATES):
                    baud_rate = values["baud_rate"]
                else:
                    baud_rate = 115200
                esptool_command = [
                    "--baud",
                    f"{ baud_rate }",
                    "--port",
                    port,
                    "erase_flash",
                ]

                timer = SimpleTimer()
                timer.start()
                esptool.main(esptool_command)
                print(f"\nFlash erased in: {(timer.end_with_results()):.1f}s\n")
                print("ERASE FIRMWARE SUCCESSFUL!\n\n")
                window["output"].update("ERASE FIRMWARE SUCCESSFUL!\n\n", append=True)
                window.refresh()
                print("Flashing NEW firmware.\n")
                window["output"].update("Flashing NEW firmware.\n", append=True)
                window.refresh()
                flash_offset = values["flash_offset"]
                if str(values["chip"]).lower() == "esp8266":
                    chip = "esp8266"
                    esptool_command = [
                        "--baud",
                        f"{baud_rate}",
                        "--port",
                        port,
                        "--chip",
                        f"{chip}",
                        "write_flash",
                        "--flash_mode",
                        "dout",
                        "--flash_size",
                        "detect",
                        f"{flash_offset}",
                        firmware,
                    ]
                else:
                    chip = str(values["chip"]).lower()
                    esptool_command = [
                        "--baud",
                        f"{baud_rate}",
                        "--port",
                        port,
                        "--chip",
                        f"{chip}",
                        "write_flash",
                        "-z",
                        f"{flash_offset}",
                        firmware,
                    ]

                timer.start()
                print(*esptool_command)
                esptool.main(esptool_command)
                print(f"\nFirmware flashed in: {(timer.end_with_results()):.1f}s\n")
                print("FIRMWARE FLASH SUCCESSFUL!\n\n")
                window["output"].update("FIRMWARE FLASH SUCCESSFUL!\n\n", append=True)
                window.refresh()
            print("Uploading software package.\n")
            window["output"].update("Uploading software package.\n", append=True)

            if not software:
                print("WARNING: missing software package!\n")
                window["output"].update(
                    "WARNING: missing software package!\n", append=True
                )
                window.refresh()
                window.UnHide()
                continue

            zf = ZipFile(software)
            timer.start()
            with TemporaryDirectory() as tempdir:
                zf.extractall(tempdir)
                pyb = pyboard.Pyboard(port, 115200)
                directories_to_make = ["."]
                files_and_data_to_bulk_write = dict()

                print("Generating directories list.\n")
                window["output"].update("Generating directories list.\n", append=True)
                try:
                    for path, currentDirectory, files in os.walk(tempdir):
                        for file in files:
                            dir = path.replace(tempdir, "")
                            new_path = pathlib.Path(dir).as_posix()
                            fh = pyb_files.Files(pyb)
                            if new_path not in directories_to_make:
                                try:
                                    directories = new_path.split("/")
                                    path_part = ""
                                    for d in directories[1::]:
                                        path_part += "/" + d
                                        if path_part in directories_to_make:
                                            continue
                                        window["output"].update(
                                            f"{path_part}\n", append=True
                                        )
                                        window.refresh()
                                        print(path_part)
                                        directories_to_make.append(path_part)
                                except DirectoryExistsError:
                                    pass
                                except Exception as e:
                                    print(e)
                            with open(os.path.join(path, file), "rb") as f:
                                data = f.read()
                            new_file_name = pathlib.Path(
                                os.path.join(dir, file)
                            ).as_posix()
                            files_and_data_to_bulk_write[str(new_file_name)] = data

                    window.refresh()
                    print(f"\nCreating and/or verifying directories.\n")
                    window["output"].update(
                        f"\nCreating and/or verifying directories.\n", append=True
                    )
                    window.refresh()

                    fh.mkdir(directory_list=directories_to_make)

                    print(f"\nUploading Files.\n")
                    window["output"].update(f"\nUploading Files.\n", append=True)
                    window.refresh()

                    fh.put(
                        files_and_data_to_bulk_write
                    )  # We don't need to enter raw because we will still be in raw repl from folder creation.
                    print(
                        f"\nSoftware package uploaded in: {(timer.end_with_results()):.1f}s"
                    )
                    window["output"].update(
                        "SOFTWARE PACKAGE UPLOAD SUCCESSFUL!\n", append=True
                    )
                    window.refresh()
                    total_timer_result = total_timer.end_with_results()
                    print(
                        f"Total time: {total_timer_result:.1f}s   ({total_timer_result/60:.1f}m)\n"
                    )
                    pyb.soft_reset()
                    pyb.close()
                except PyboardError:
                    print("\n\nERROR: something went wrong talking to the device.")
                    print("(It is recommended to unplug the device and plug in again.)")
                    window["output"].update(
                        "ERROR: something went wrong talking to the device.\n",
                        append=True,
                    )
                    window["output"].update(
                        "Unplug device and plug in and try again.)\n", append=True
                    )
                    window.refresh()
                    pyb.close()
                    continue
                except KeyboardInterrupt:
                    print(
                        "\n\nERROR: user forcefully bailed, file system may be corrupt due to partial software upload.\n"
                    )
                    window["output"].update(
                        "ERROR: user forcefully bailed, file system may be corrupt due to partial software upload.\n",
                        append=True,
                    )
                    window.refresh()
                    pyb.close()
                    continue
                except Exception as e:
                    print("\n\nERROR: something went wrong...\n")
                    window["output"].update(
                        "ERROR: something went wrong...\n", append=True
                    )
                    window.refresh()
                    pyb.close()
                    continue
                finally:
                    window.UnHide()

    except Exception as e:
        window["output"].update(f"{e}\n", append=True)
        window.refresh()
        crash = ["Error on line {}".format(sys.exc_info()[-1].tb_lineno), "\n", e]
        print(crash)
        import time

        current_time = str(time.time())
        with open("error_" + current_time + ".log", "w") as crash_log:
            for i in crash:
                i = str(i)
                crash_log.write(i)

    window.UnHide()

    if event == sg.WIN_CLOSED:
        break
window.close()
