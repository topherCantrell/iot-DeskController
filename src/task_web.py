import time
import biplane
import asyncio
import os

import logging

LOGGER = logging.getLogger(__name__)


server = biplane.Server()

_hardware = None
_desk = None
_rfid = None


@server.route("/", "GET")
def do_root(query_parameters, headers, body):
    with open('index.html') as f:
        content = f.read()
    return biplane.Response(content, content_type="text/html")


@server.route("/desk", "GET")
def do_desk(query_parameters, headers, body):
    # Always returns the current state in the body
    # URL params (commands):
    #   motors=up+down,0.25 (if ",time" is given, motors are turned off after time)
    #   goto=35.2 (height in cm)
    #   write=both (up, down, or both)
    #   setpoints=22.4,33.5
    # Only one command is processed
    try:
        query_parameters = query_parameters.split('&')
        for param in query_parameters:
            if param:
                a, b = param.split('=')
                if a == 'goto':
                    LOGGER.debug('GOTO '+b)
                    b = float(b)
                    _desk.goto(b)
                elif a == 'setUp':
                    height = float(b)
                    LOGGER.debug('WRITE UP '+b)
                    _desk.set_point_up(height)
                    _rfid.write_heights(0)
                elif a == 'setDown':
                    LOGGER.debug('WRITE DOWN '+b)
                    height = float(b)
                    _desk.set_point_down(height)
                    _rfid.write_heights(1)
                elif a == 'writeBoth':
                    LOGGER.debug('WRITE BOTH TO RING')
                    _rfid.write_heights(2)
                elif a == 'motors':
                    LOGGER.debug('MOTORS '+b)
                    up = False
                    down = False
                    timeout = None
                    i = b.find(',')
                    if i >= 0:
                        timeout = float(b[i+1:])
                    if 'up' in b:
                        up = True
                    if 'down' in b:
                        down = True
                    _desk.set_motors(up, down)
                    if timeout:
                        time.sleep(timeout)
                        _desk.set_motors(False, False)
                        LOGGER.debug('STOPPED AFTER TIME')
    except Exception as ex:
        LOGGER.debug('Error reading query params: ' +
                     str(query_parameters)+' '+str(ex))
        return biplane.Response("Invalid query parameters", status_code=400, content_type="text/html")

    up, down = _desk.get_motors()
    mode = _desk.get_mode()
    height = _desk.get_height()
    set_up, set_down = _desk.get_set_points()

    # Return lines key=value:
    ret = '{\n'
    ret += '"up":'+str(up)+',\n'
    ret += '"down":'+str(down)+',\n'
    ret += '"mode":"'+str(mode)+'",\n'
    ret += '"current_height":"'+str(height)+'",\n'
    ret += '"set_up":"'+str(set_up)+'",\n'
    ret += '"set_down":"'+str(set_down)+'"\n'
    ret += '}'

    return biplane.Response(ret.lower(), content_type="text/plain")


class WebServer:

    def __init__(self):
        pass

    def set_dependencies(self, hardware, desk, rfid):
        global _hardware, _desk, _rfid
        _hardware = hardware
        _desk = desk
        _rfid = rfid

    async def run_task(self):
        LOGGER.info('Starting run_task for WebServer')
        for _ in server.circuitpython_start_wifi_station(
                os.getenv('CIRCUITPY_WIFI_SSID'),
                os.getenv('CIRCUITPY_WIFI_PASSWORD'), 'app'):
            await asyncio.sleep(0)  # let other tasks run
