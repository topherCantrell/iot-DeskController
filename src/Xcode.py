# Circuit Python runs this on start

import asyncio
import os
import logging

from hardware import Hardware
from task_buttons import ExtraButtons
from task_desk_height import DeskHeight
from task_rfid import RFID
from task_web import WebServer
from task_led import LED

LOGGER = logging.getLogger(__name__)

use_sonar = os.getenv('USE_SONAR')
use_rfid = os.getenv('USE_RFID')
use_extra_buttons = os.getenv('USE_EXTRA_BUTTONS')
use_web = os.getenv('USE_WEB')
use_desk_buttons = os.getenv('USE_DESK_BUTTONS')
use_led = os.getenv('USE_LED')

hd = Hardware(use_rfid, use_sonar)

dh = DeskHeight()
rf = None
db = None
eb = None
ws = None
led = None
tasks = []

if use_led:
    led = LED()

if use_desk_buttons:
    # TODO implement this
    pass

if use_rfid:
    rf = RFID()

if use_extra_buttons:
    eb = ExtraButtons()

if use_web:
    ws = WebServer()

dh.set_dependencies(hd)
tasks.append(dh.run_task())

if led:
    led.set_dependencies(hd)
    tasks.append(led.run_task())

if db:
    db.set_dependencies(hd, led)
    tasks.append(db.run_task())

if rf:
    rf.set_dependencies(hd, dh, led)
    tasks.append(rf.run_task())

if eb:
    eb.set_dependencies(hd, dh, rf, led)
    tasks.append(eb.run_task())

if ws:
    ws.set_dependencies(hd, dh, rf)
    tasks.append(ws.run_task())

LOGGER.debug('Starting tasks')
asyncio.run(asyncio.gather(*tasks))
LOGGER.error('Tasks ended')
