import time
from threading import Thread, Event
import logging
from colorlog import ColoredFormatter
from utils import get_args
import sys
import os
from getVNCPic import getVNCPic
from detect_text import check_login, check_message, check_Xbutton, check_speedmessage, check_quitbutton, check_raidscreen
from copyMons import runAll
from  scanner import start_detect

class LogFilter(logging.Filter):

    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno < self.level

console = logging.StreamHandler()
args = get_args()

if not (args.verbose):
    console.setLevel(logging.INFO)

formatter = ColoredFormatter(
    '%(log_color)s [%(asctime)s] [%(threadName)16s] [%(module)14s]' +
    ' [%(levelname)8s] %(message)s',
    datefmt='%m-%d %H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG': 'purple',
        'INFO': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
    )

console.setFormatter(formatter)

# Redirect messages lower than WARNING to stdout
stdout_hdlr = logging.StreamHandler(sys.stdout)
stdout_hdlr.setFormatter(formatter)
log_filter = LogFilter(logging.WARNING)
stdout_hdlr.addFilter(log_filter)
stdout_hdlr.setLevel(5)

# Redirect messages equal or higher than WARNING to stderr
stderr_hdlr = logging.StreamHandler(sys.stderr)
stderr_hdlr.setFormatter(formatter)
stderr_hdlr.setLevel(logging.WARNING)

log = logging.getLogger()
log.addHandler(stdout_hdlr)
log.addHandler(stderr_hdlr)

def main():

    sys.excepthook = handle_exception
    args = get_args()
    print(args.vncip)
    set_log_and_verbosity(log)
    log.info("Starting TheRaidMap")

    # Check for MonPics
    runAll()

    #thread.start_new_thread(main_thread, ('test'))

    t = Thread(target=main_thread,
                       name='main')
    t.daemon = True
    t.start()
    log.info('Starting Thread....')
    while True:
        pass
    #loop = asyncio.get_event_loop()
    #tasks = [
    #    asyncio.async(getVNCPic()),
    #    asyncio.async(check_login()),
    #    asyncio.async(check_message()),
    #    asyncio.async(check_Xbutton())]

    #loop.run_until_complete(asyncio.wait(tasks))
    #loop.run_forever()
    #loop.close()

    # Hier muss noch der Async Job starter rein. Aktuell nur einzelne Jobs zum testen


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    log.error("Uncaught exception", exc_info=(
        exc_type, exc_value, exc_traceback))

def set_log_and_verbosity(log):
    # Always write to log file.
    args = get_args()
    # Create directory for log files.
    if not os.path.exists(args.log_path):
        os.mkdir(args.log_path)
    if not args.no_file_logs:
        filename = os.path.join(args.log_path, args.log_filename)
        filelog = logging.FileHandler(filename)
        filelog.setFormatter(logging.Formatter(
            '%(asctime)s [%(threadName)18s][%(module)14s][%(levelname)8s] ' +
            '%(message)s'))
        log.addHandler(filelog)

    if args.verbose:
            log.setLevel(logging.DEBUG)

            # Let's log some periodic resource usage stats.
            t = Thread(target=log_resource_usage_loop, name='res-usage')
            t.daemon = True
            t.start()
    else:
            log.setLevel(logging.INFO)

def main_thread():
    while True:
        getVNCPic('screenshot.png')
        check_login('screenshot.png', 123)
        check_message('screenshot.png', 123)
        check_Xbutton('screenshot.png', 123)
        check_speedmessage('screenshot.png', 123)
        check_quitbutton('screenshot.png', 123)
        check_raidscreen('screenshot.png', 123)
        start_detect('screenshot.png', 123)
        time.sleep(2)


if __name__ == '__main__':
    main()
