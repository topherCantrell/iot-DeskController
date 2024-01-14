import asyncio

from hardware import Hardware
from task_buttons import ExtraButtons
from task_desk_height import DeskHeight
from task_rfid import RFID
from task_web import WebServer
from task_led import LED

desk = DeskHeight()
rfid = None
buttons = None
web = None
led = None

tasks = []

hard = Hardware()
desk = DeskHeight()
led = LED()
rfid = RFID()
buttons = ExtraButtons()
web = WebServer()

desk.set_dependencies(hard)
tasks.append(desk.run_task())

led.set_dependencies(hard)
tasks.append(led.run_task())

rfid.set_dependencies(hard, desk, led)
tasks.append(rfid.run_task())

buttons.set_dependencies(hard, desk, rfid, led)
tasks.append(buttons.run_task())

web.set_dependencies(hard, desk, rfid)
tasks.append(web.run_task())

asyncio.run(asyncio.gather(*tasks))
