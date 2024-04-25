# Create a sheet type that will trigger the thread-related bug #1964

from visidata import vd, VisiData, SequenceSheet, JsonSheet, AttrDict
import datetime
import time

# create a loader for files with the extension ".slow", that will trigger the bug
@VisiData.api
def open_slow(vd, p):
    return SlowJsonSheet(p.name, source=p)

vd.slow_row_interval = 0.5

class SlowJsonSheet(JsonSheet):
    _rowtype = AttrDict  # rowdef: dict of values
    def __init__(self, *names, **kwargs):
        self.start_time = datetime.datetime.now()
        super().__init__(*names, **kwargs)

    def iterload(self):
        file = 'sample_data/sample.tsv'
        line1 = AttrDict({"longname": "no-op",   "input": f'command_1', "keystrokes": ""})
        line2 = AttrDict({"longname": "no-op",   "input": f'command_2', "keystrokes": ""})
        line3 = AttrDict({"longname": "open-file", "input": file,         "keystrokes": "o"})
        line4 = AttrDict({"longname": "no-op",   "input": f'command_4', "keystrokes": ""})
        line5 = AttrDict({"longname": "no-op",   "input": f'command_5', "keystrokes": ""})
        lines = [line1, line2, line3, line4, line5]

        self.loop_time = datetime.datetime.now()
        i = 0
        while True:
            t = (datetime.datetime.now() - self.loop_time).total_seconds()
            if t > vd.slow_row_interval:
                if i >= len(lines):
                    return
                self.loop_time = datetime.datetime.now()
                try:
                    yield lines[i]
                    i += 1
                except StopIteration:
                    return
            else:
                time.sleep(0.1)

vd.addGlobals({
    'SlowJsonSheet': SlowJsonSheet
})
