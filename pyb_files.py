import textwrap
import sys

from pyboard import PyboardError

BUFFER_SIZE = 1024


class DirectoryExistsError(Exception):
    ...


class Files(object):
    def __init__(self, pyboard):
        self._pyboard = pyboard

    def mkdir(self, directory=None, exists_okay=True, directory_list: list = None):
        try:
            self._pyboard.enter_raw_repl()
        except PyboardError:
            raise PyboardError

        if directory_list is not None:
            if directory is not None:
                directory_list.append(directory)
            for dir in directory_list:

                # Execute os.mkdir command on the board.
                command = """
                    try:
                        import os
                    except ImportError:
                        import uos as os
                    os.mkdir('{0}')
                """.format(
                    dir
                )
                try:
                    self._pyboard.exec_(textwrap.dedent(command))
                    print(f"Directory Created: {dir}")
                except PyboardError as ex:
                    # Check if this is an OSError #17, i.e. directory already exists.
                    if (
                        ex.args[2].decode("utf-8").find("OSError: [Errno 17] EEXIST")
                        != -1
                    ):
                        if not exists_okay:
                            raise DirectoryExistsError(
                                "Directory already exists: {0}".format(directory)
                            )
                        if exists_okay:
                            print(f"Directory already exists -> Verified: {dir}")
                    else:
                        raise ex

        self._pyboard.exit_raw_repl()

    def put(
        self,
        files_and_data_to_bulk_write,
    ):
        try:
            self._pyboard.enter_raw_repl()
        except PyboardError:
            raise PyboardError
        try:
            file_count = len(files_and_data_to_bulk_write.keys())
            current_file = 0
            for file, data in files_and_data_to_bulk_write.items():
                current_file += 1
                self._pyboard.exec_("f = open('{0}', 'wb')".format(file))
                size = len(data)
                written = 0
                # Loop through and write a buffer size chunk of data at a time.
                for i in range(0, size, BUFFER_SIZE):
                    sys.stdout.write(
                        f'\r[{current_file} of {file_count}]  "{file}"  >>>  {written} of {size}'
                    )
                    sys.stdout.flush()
                    chunk_size = min(BUFFER_SIZE, size - i)
                    chunk = repr(data[i : i + chunk_size])
                    # Make sure to send explicit byte strings (handles python 2 compatibility).
                    if not chunk.startswith("b"):
                        chunk = "b" + chunk
                    self._pyboard.exec_("f.write({0})".format(chunk))
                    written = i
                self._pyboard.exec_("f.close()")
                sys.stdout.write(
                    f'\r[{current_file} of {file_count}]  "{file}"  >>>  {size} of {size}\n'
                )
        except PyboardError as ex:
            print(ex.args[2].decode("utf-8"))
            raise ex
        self._pyboard.exit_raw_repl()
