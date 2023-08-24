#!/usr/bin/python3

# import contextlib
import curses
import math
import os
import string
import time

pendingKeys = []
curses_timeout = 100
escdelay = 25
#escdelay = 200   # didn't help
allPrefixes = ['g', 'z', 'Alt+']
y = 0

# write a string to the screen and update the draw location to be just below the written string
def screen_log(scr, s):
    global y
    h, w = scr.getmaxyx()
    if y >= h:
        scr.clear()
        y = y % h
    scr.addstr(y, 0, s)
    # make the next draw be 1 or more lines lower on the screen
    y += math.ceil(len(s)/w)

def initCurses():
    # reduce ESC timeout to 25ms. http://en.chys.info/2009/09/esdelay-ncurses/
    os.putenv('ESCDELAY', str(escdelay))
    curses.use_env(True)
    #curses.set_escdelay(escdelay)      # python >= 3.9

    scr = curses.initscr()
    curses.noecho()
    scr.keypad(True)
    curses.raw()    # get control keys instead of signals
    scr.timeout(curses_timeout)
#     scr.notimeout(True)

# get rid of all keys pressed so far - it lessens the chance of the problem but does not fully prevent it
#     curses.flushinp()
# an alternate way to do instead of curses.flushinp():
    drainPendingKeys(scr)
    global pendingKeys
    s = f'keysrokes pending on curses init:  {pendingKeys}'
    pendingKeys = []

# commenting all these out does not stop the problem:
#    curses.start_color()
#    curses.use_default_colors()
#    curses.meta(1)  # allow "8-bit chars"
    curses.def_prog_mode()

    scr.refresh()
    screen_log(scr, s)

#  Checking for more keys here never caught any keys.
#     drainPendingKeys(scr)
#     pendingKeys = []

    return scr



def mainloop(scr):
#     with contextlib.suppress(curses.error):
#         curses.curs_set(0)

    numTimeouts = 0
    prefixWaiting = False

    keystrokes = ''
    while True:
        keystroke = getkeystroke(scr)

        if not keystroke and prefixWaiting and "Alt+" in keystrokes:  # timeout ESC
            keystrokes = ''

        if keystroke:  # wait until next keystroke to clear statuses and previous keystrokes
            numTimeouts = 0
            if not prefixWaiting:
                keystrokes = ''

            if keystroke and keystroke in allPrefixes and keystroke in keystrokes[:-1]:
#                 vd.warning('duplicate prefix: ' + keystroke)
                keystrokes = ''
            else:
                keystroke = prettykeys(keystroke)
                keystrokes += keystroke

        if not keystroke:  # timeout instead of keypress
            pass
        elif keystroke == 'Ctrl+Q':
            exit(1)
        elif is_a_command(keystrokes):
            prefixWaiting = False
        elif keystroke in allPrefixes:
#             screen_log(scr, 'prefixWaiting->True')
            prefixWaiting = True
        else:
            screen_log(scr, 'keystroke:  ' + str(keystrokes))
#             screen_log(scr, 'prefixWaiting->False')
            prefixWaiting = False

def is_a_command(keystrokes):
    return False

def run():
    scr = None
    try:
        scr = initCurses()
        ret = mainloop(scr)
    except curses.error as e:
        print(f'run():  curses error {e}')
        pass
    finally:
        if scr:
            curses.endwin()

def drainPendingKeys(scr):
    '''Call scr.get_wch() until no more keypresses are available.  Return True if any keypresses are pending.'''
    scr.timeout(0)
# tried this to stop the curses error, did not fix it
#    scr.timeout(10)
    try:
        while True:
            k = scr.get_wch()
            if k:
                pendingKeys.append(k)
            else:
                break
    except curses.error as e:
        # test for a no input error
        is_no_input_error = "error('no input')" in repr(e)
        if is_no_input_error:
            pass
        else:
            print(f'drainPendingKeys():  curses error: {repr(e)}')
    finally:
        scr.timeout(curses_timeout)

    return bool(pendingKeys)

def getkeystroke(scr):
    'Get keystroke and display it on status bar.'
    drainPendingKeys(scr)
    k = None
    if pendingKeys:
        k = pendingKeys.pop(0)
    else:
#   commenting this out doesn't change fix it
        curses.reset_prog_mode()  #1347
        try:
            # switching the order doesn't help:  doing scr.get_wch() before scr.refresh()
            # commenting out scr.refresh() doesn't help
            scr.refresh()
            k = scr.get_wch()
#         except curses.error:
#             return ''  # curses timeout
        except curses.error as e:
            is_no_input_error = "error('no input')" in repr(e)
            if is_no_input_error:
                return ''
            else:
                print(f'getkeystroke():  curses error: {repr(e)}')
                return ''

    if isinstance(k, str):
        if ord(k) >= 32 and ord(k) != 127:  # 127 == DEL or ^?
            return k
        k = ord(k)
    return curses.keyname(k).decode('utf-8')



prettykeys_trdict = {
        ' ': 'Space',  # must be first
        '^[': 'Alt+',
        '^J': 'Enter',
        '^M': 'Enter',
        '^I': 'Tab',
        'KEY_UP':    'Up',
        'KEY_DOWN':  'Down',
        'KEY_LEFT':  'Left',
        'KEY_RIGHT': 'Right',
        'KEY_HOME':  'Home',
        'KEY_END':   'End',
        'KEY_EOL':   'End',
        'KEY_PPAGE': 'PgUp',
        'KEY_NPAGE': 'PgDn',

        'kUP':       'Shift+Up',
        'kDN':       'Shift+Down',
        'kUP5':      'Ctrl+Up',
        'kDN5':      'Ctrl+Down',
        'kLFT5':     'Ctrl+Left',
        'kRIT5':     'Ctrl+Right',
        'kHOM5':     'Ctrl+Home',
        'kEND5':     'Ctrl+End',
        'kPRV5':     'Ctrl+PgUp',
        'kNXT5':     'Ctrl+PgDn',
        'KEY_IC5':   'Ctrl+Ins',
        'KEY_DC5':   'Ctrl+Del',

        'KEY_IC':    'Ins',
        'KEY_DC':    'Del',

        'KEY_SRIGHT':'Shift+Right',
        'KEY_SR':    'Shift+Up',
        'KEY_SF':    'Shift+Down',
        'KEY_SLEFT': 'Shift+Left',
        'KEY_SHOME': 'Shift+Home',
        'KEY_SEND':  'Shift+End',
        'KEY_SPREVIOUS': 'Shift+PgUp',
        'KEY_SNEXT': 'Shift+PgDn',

        'KEY_BACKSPACE': 'Bksp',
        'BUTTON1_PRESSED': 'LeftClick',
        'BUTTON2_PRESSED': 'MiddleClick',
        'BUTTON3_PRESSED': 'RightClick',
        'BUTTON4_PRESSED': 'ScrollwheelUp',
        'BUTTON5_PRESSED': 'ScrollwheelDown',
        'REPORT_MOUSE_POSITION': 'ScrollwheelDown',
        '2097152': 'ScrollwheelDown',
        'KEY_F(1)': 'F1',
        'KEY_F(2)': 'F2',
        'KEY_F(3)': 'F3',
        'KEY_F(4)': 'F4',
        'KEY_F(5)': 'F5',
        'KEY_F(6)': 'F6',
        'KEY_F(7)': 'F7',
        'KEY_F(8)': 'F8',
        'KEY_F(9)': 'F9',
        'KEY_F(10)': 'F10',
        'KEY_F(11)': 'F11',
        'KEY_F(12)': 'F12',
    }

def prettykeys(key):
    if not key:
        return key

    for k, v in prettykeys_trdict.items():
        key = key.replace(k, v)

    # replace ^ with Ctrl but not if ^ is last char
    key = key[:-1].replace('^', 'Ctrl+')+key[-1]
    # 1497: allow Shift+ for Alt keys
    if key[-1] in string.ascii_uppercase and ('+' not in key or 'Alt+' in key) and '_' not in key:
        key = key[:-1] + 'Shift+' + key[-1]

    return key.strip()



def main():
    interval = 1
    print(f'sleeping for {interval} seconds to allow user keypress')
    time.sleep(interval)
    run()
main()
