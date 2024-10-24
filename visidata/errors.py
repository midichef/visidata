import traceback

from visidata import vd, VisiData

vd.option('debug', False, 'exit on error and display stacktrace')
vd.option('debug_stacktrace_full', False, 'for exceptions, show callstack levels above the catch')


class ExpectedException(Exception):
    'Controlled Exception from fail() or confirm().  Status or other interface update is done by raiser.'
    pass


def stacktrace(e=None):
    '''if options.debug_stacktrace_full is True, display all callstack
    levels above the level where the exception was caught, in addition
    to the standard exception.'''
    if not e:
        if vd.options.debug_stacktrace_full:
            trim_levels = 3   # calling function -> stacktrace() -> format_stack()
            stack = ''.join(traceback.format_stack()).strip().splitlines()
            trace_above = stack[:-2*trim_levels]
        else:
            trace_above = []
        return trace_above + traceback.format_exc().strip().splitlines()
    return traceback.format_exception_only(type(e), e)

@VisiData.api
def exceptionCaught(vd, exc=None, status=True, **kwargs):
    'Add *exc* to list of last errors and add to status history.  Show on left status bar if *status* is True.  Reraise exception if options.debug is True.'
    if isinstance(exc, ExpectedException):  # already reported, don't log
        return
    vd.lastErrors.append(stacktrace())
    if status:
        vd.status(f'{type(exc).__name__}: {exc}', priority=2)
    else:
        vd.addToStatusHistory(vd.lastErrors[-1][-1])
    if vd.options.debug:
        raise


vd.addGlobals(stacktrace=stacktrace, ExpectedException=ExpectedException)

# see textsheet.py for ErrorSheet and associated commands
