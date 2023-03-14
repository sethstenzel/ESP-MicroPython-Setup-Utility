import sys
import time

_rawdelay = None

stdout = sys.stdout.buffer


def stdout_write_bytes(b):
    b = b.replace(b"\x04", b"")
    stdout.write(b)
    stdout.flush()


class PyboardError(BaseException):
    def __init__(self, *args: object, **kwargs) -> None:
        super().__init__(*args)


class Pyboard:
    def __init__(
        self,
        device,
        baudrate=115200,
        wait=0,
        rawdelay=0,
    ):
        global _rawdelay
        _rawdelay = rawdelay
        if True:
            import serial

            delayed = False
            for attempt in range(wait + 1):
                try:
                    self.serial = serial.Serial(
                        device,
                        baudrate=baudrate,  # interCharTimeout=1
                    )
                    break
                except (OSError, IOError):  # Py2 and Py3 have different errors
                    if wait == 0:
                        continue
                    if attempt == 0:
                        sys.stdout.write("Waiting {} seconds for pyboard ".format(wait))
                        delayed = True
                time.sleep(1)
                sys.stdout.write(".")
                sys.stdout.flush()
            else:
                if delayed:
                    print("")
                raise PyboardError("failed to access " + device)
            if delayed:
                print("")

    def close(self):
        self.serial.close()

    def read_until(self, min_num_bytes, ending, timeout=10, data_consumer=None):
        data = self.serial.read(min_num_bytes)
        if data_consumer:
            data_consumer(data)
        timeout_count = 0
        while True:
            if data.endswith(ending):
                break
            elif self.serial.inWaiting() > 0:
                new_data = self.serial.read(1)
                data = data + new_data
                if data_consumer:
                    data_consumer(new_data)
                timeout_count = 0
            else:
                timeout_count += 1
                if timeout is not None and timeout_count >= 100 * timeout:
                    break
                time.sleep(0.02)
        return data

    def soft_reset(self):
        # ctrl-C twice: interrupt any running program
        self.serial.write(b"\x03")
        time.sleep(0.3)
        self.serial.write(b"\x03")
        time.sleep(1)

        # ctrl-D: soft reset the board
        # print("Performing Soft Reset")
        # self.serial.write(b"\x04")  # ctrl-D: soft reset
        self.serial.write(b"import machine\r\n")
        self.serial.write(b"machine.reset()\r\n")

    def enter_raw_repl(self, soft_reset=False):
        # Brief delay before sending RAW MODE char if requests
        if _rawdelay > 0:
            time.sleep(_rawdelay)

        if soft_reset:
            self.soft_reset()
            spam_ctrl_c_time = 20
            while spam_ctrl_c_time > 0:
                spam_ctrl_c_time -= 1
                self.serial.write(b"\r\x03")
                time.sleep(0.2)
            time.sleep(1)
            self.serial.write(b"\r\x03")

        # ctrl-C twice: interrupt any running program

        self.serial.write(b"\r\x03")
        time.sleep(1)
        self.serial.write(b"\r\x03")
        time.sleep(1)

        # flush input (without relying on serial.flushInput())
        n = self.serial.inWaiting()
        while n > 0:
            self.serial.read(n)
            n = self.serial.inWaiting()

        for retry in range(0, 5):
            self.serial.write(b"\r\x01")  # ctrl-A: enter raw REPL
            data = self.read_until(1, b"raw REPL; CTRL-B to exit\r\n>")
            if data.endswith(b"raw REPL; CTRL-B to exit\r\n>"):
                break
            else:
                if retry >= 10:
                    print(data)
                    raise PyboardError("could not enter raw repl")
                time.sleep(0.2)

        self.serial.write(b"\x04")  # ctrl-D: soft reset
        data = self.read_until(1, b"soft reboot\r\n")
        if not data.endswith(b"soft reboot\r\n"):
            raise PyboardError("could not enter raw repl")
        # By splitting this into 2 reads, it allows boot.py to print stuff,
        # which will show up after the soft reboot and before the raw REPL.
        # Modification from original pyboard.py below:
        #   Add a small delay and send Ctrl-C twice after soft reboot to ensure
        #   any main program loop in main.py is interrupted.
        time.sleep(0.5)
        self.serial.write(b"\x03")
        time.sleep(0.1)  # (slight delay before second interrupt
        self.serial.write(b"\x03")
        # End modification above.
        data = self.read_until(1, b"raw REPL; CTRL-B to exit\r\n")
        if not data.endswith(b"raw REPL; CTRL-B to exit\r\n"):
            print(data)
            raise PyboardError("could not enter raw repl")

    def exit_raw_repl(self):
        self.serial.write(b"\r\x02")  # ctrl-B: enter friendly REPL

    def follow(self, timeout, data_consumer=None):
        # wait for normal output
        data = self.read_until(1, b"\x04", timeout=timeout, data_consumer=data_consumer)
        if not data.endswith(b"\x04"):
            raise PyboardError("timeout waiting for first EOF reception")
        data = data[:-1]

        # wait for error output
        data_err = self.read_until(1, b"\x04", timeout=timeout)
        if not data_err.endswith(b"\x04"):
            raise PyboardError("timeout waiting for second EOF reception")
        data_err = data_err[:-1]

        # return normal and error output
        return data, data_err

    def exec_raw_no_follow(self, command):
        if isinstance(command, bytes):
            command_bytes = command
        else:
            command_bytes = bytes(command, encoding="utf8")

        # check we have a prompt
        data = self.read_until(1, b">")
        if not data.endswith(b">"):
            raise PyboardError("could not enter raw repl")

        # write command
        for i in range(0, len(command_bytes), 256):
            self.serial.write(command_bytes[i : min(i + 256, len(command_bytes))])
            time.sleep(0.01)
        self.serial.write(b"\x04")

        # check if we could exec command
        data = self.serial.read(2)
        if data != b"OK":
            raise PyboardError("could not exec command")

    def exec_raw(self, command, timeout=10, data_consumer=None):
        self.exec_raw_no_follow(command)
        return self.follow(timeout, data_consumer)

    def eval(self, expression):
        ret = self.exec_("print({})".format(expression))
        ret = ret.strip()
        return ret

    def exec_(self, command, stream_output=False):
        data_consumer = None
        if stream_output:
            data_consumer = stdout_write_bytes
        ret, ret_err = self.exec_raw(command, data_consumer=data_consumer)
        if ret_err:
            raise PyboardError("exception", ret, ret_err)
        return ret

    def execfile(self, filename, stream_output=False):
        with open(filename, "rb") as f:
            pyfile = f.read()
        return self.exec_(pyfile, stream_output=stream_output)

    def get_time(self):
        t = str(self.eval("pyb.RTC().datetime()"), encoding="utf8")[1:-1].split(", ")
        return int(t[4]) * 3600 + int(t[5]) * 60 + int(t[6])


# in Python2 exec is a keyword so one must use "exec_"
# but for Python3 we want to provide the nicer version "exec"
setattr(Pyboard, "exec", Pyboard.exec_)


def execfile(
    filename, device="/dev/ttyACM0", baudrate=115200, user="micro", password="python"
):
    pyb = Pyboard(device, baudrate, user, password)
    pyb.enter_raw_repl()
    output = pyb.execfile(filename)
    stdout_write_bytes(output)
    pyb.exit_raw_repl()
    pyb.close()
