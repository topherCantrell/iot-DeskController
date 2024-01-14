import asyncio
import logging

LOGGER = logging.getLogger(__name__)


class ExtraButtons:

    def __init__(self):
        self._hardware = None
        self._desk = None
        self._rfid = None
        self._mode = 'goto'  # or 'record'

    def set_dependencies(self, hardware, desk, rfid, led):
        self._hardware = hardware
        self._desk = desk
        self._rfid = rfid
        self._led = led

    def _handle_change(self, change):
        # BOTH buttons: switch mode (record or goto)
        # Single button (record mode): set the button's height point and write ring
        # Single button (goto): goto button's height point
        LOGGER.debug('Button event: '+change)
        set_points = self._desk.get_set_points()
        LOGGER.debug('Set points: '+str(set_points))
        height = self._desk.get_height()
        if change == 'SingleUp':
            LOGGER.debug('SingleUp: '+self._mode)
            if self._mode == 'goto':
                self._desk.goto(set_points[0])
            else:
                self._desk.set_point_up(height)
                LOGGER.debug('Set up to '+str(height))
                self._rfid.write_heights(0)  # Twiddles the LED
                self._mode = 'goto'
        elif change == 'SingleDown':
            LOGGER.debug('SingleDown: '+self._mode)
            if self._mode == 'goto':
                self._desk.goto(set_points[1])
            else:
                self._desk.set_point_down(height)
                LOGGER.debug('Set down to '+str(height))
                self._rfid.write_heights(1)  # Twiddles the LED
                self._mode = 'goto'
        elif change == 'SingleBoth':
            LOGGER.debug('SingleBoth: '+self._mode)
            if self._mode == 'goto':
                self._mode = 'record'
                self._led.set_mode(self._led.MODE_WROTE_RING)
            else:
                self._rfid.write_heights(2)  # Twiddles the LED
                self._mode = 'goto'
        else:
            LOGGER.error('Software error. Unknown change mode: '+change)
            self._led.set_mode(self._led.MODE_ERROR)

    async def _wait_on_button_release(self, org_up, org_down):
        # This is called when one or both buttons are pressed.
        # We return when any pressed button has been released.
        while True:
            up, down = self._hardware.get_extra_buttons()
            if org_up and not up:
                return (org_up, org_down, up, down)
            if org_down and not down:
                return (org_up, org_down, up, down)
            # We can add the other button
            org_up = org_up | up
            org_down = org_down | down
            await asyncio.sleep(0.1)

    async def _wait_on_button_cycle(self):
        # Wait for a full down/up cycle of the buttons. We stay in this function
        # until both buttons are released. We return the buttons that were down (one
        # or both) just before the release happened.
        while True:
            up, down = self._hardware.get_extra_buttons()
            if up or down:
                break
            await asyncio.sleep(0.1)
        org_up, org_down, up, down = await self._wait_on_button_release(up, down)
        while up or down:
            up, down = self._hardware.get_extra_buttons()
            if not up and not down:
                break
            await asyncio.sleep(0.1)
        return (org_up, org_down)

    async def run_task(self):
        LOGGER.info('Starting run_task for ExtraButtons')
        # We are looking for:
        # - Single-click of up or down
        # - Double-click of up or down
        # - Single-click of both
        # - Double-click of both
        # We call "_handle_change" with one of the above conditions as they come in
        while True:
            # Wait on a button cycle (down and back up)
            up, down = await self._wait_on_button_cycle()
            await asyncio.sleep(0.1)
            up2, down2 = self._hardware.get_extra_buttons()
            if up2 or down2:
                up2, down2 = await self._wait_on_button_cycle()
            if up and down and up2 and down2:
                self._handle_change('DoubleBoth')
            elif up and up2:
                self._handle_change('DoubleUp')
            elif down and down2:
                self._handle_change('DoubleDown')
            elif up and down:
                self._handle_change('SingleBoth')
            elif up:
                self._handle_change('SingleUp')
            elif down:
                self._handle_change('SingleDown')
            else:
                # Should never happen
                LOGGER.error('SoftwareError. Unknown button state.')
                self._led.set_mode(self._led.MODE_ERROR)
