import asyncio

import logging

LOGGER = logging.getLogger(__name__)


class LED:

    MODE_OFF = 'OFF'
    MODE_MANUAL = 'MANUAL'
    MODE_READY_RING = 'READY_RING'
    MODE_WROTE_RING = 'WROTE_RING'
    MODE_ERROR = 'ERROR'

    PARAMS = {
        MODE_MANUAL: [10, 10],  # Slow blink (1s/1s)
        MODE_READY_RING: [2, 2],  # Fast blink (0.3s/0.3s)
        MODE_WROTE_RING: [10, 0],  # Solid on
        MODE_ERROR: [30, 1],  # Long on, short off (3s/0.1s)
    }

    def __init__(self):
        self._hardware = None
        self._mode = None
        self._counter_on_reload = None
        self._count_off_reload = None
        self._count = None
        self._led_on = None

    def set_dependencies(self, hardware):
        self._hardware = hardware
        self.set_mode(LED.MODE_OFF)

    def set_mode(self, mode):
        if self._mode == LED.MODE_ERROR:
            # Hold the error mode indicator
            return
        self._mode = mode
        if mode == LED.MODE_OFF:
            self._hardware.set_led(False)
        else:
            counts = LED.PARAMS[mode]
            self._counter_on_reload = counts[0]
            self._counter_off_reload = counts[1]
            # Always start on
            self._count = counts[0]
            self._led_on = True
            self._hardware.set_led(True)

    async def run_task(self):
        LOGGER.info('Starting run_task LED')
        while True:
            if self._mode == LED.MODE_OFF:
                # Nothing happening in "off" mode
                await asyncio.sleep(0.5)
                continue

            # For solid LEDs
            if self._counter_off_reload == 0:
                await asyncio.sleep(0.5)
                continue

            await asyncio.sleep(0.1)

            self._count -= 1
            if self._count:
                continue

            if self._counter_off_reload == 0:
                self._count = self._counter_on_reload
                continue

            self._led_on = not self._led_on
            if self._led_on:
                self._hardware.set_led(True)
                self._count = self._counter_on_reload
            else:
                self._hardware.set_led(False)
                self._count = self._counter_off_reload
