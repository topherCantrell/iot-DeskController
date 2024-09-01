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

services = {}

hard = Hardware()

services['desk'] = DeskHeight(hard, services)
services['led'] = LED(hard, services)
services['rfid'] = RFID(hard, services)
services['buttons'] = ExtraButtons(hard, services)
services['web'] = WebServer(hard, services)

asyncio.run(asyncio.gather(
    services['desk'].run_task(),
    services['led'].run_task(),
    services['rfid'].run_task(),
    services['buttons'].run_task(),
    services['web'].run_task()
))
