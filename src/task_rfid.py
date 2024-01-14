import asyncio

import logging

LOGGER = logging.getLogger(__name__)


class RFID:

    MODE_IGNORE = 'IGNORE'
    MODE_GOTO = 'GOTO'
    MODE_WRITE_HEIGHT = 'WRITE'
    DATA_BLOCK = 8

    def __init__(self):
        self._hardware = None
        self._desk = None
        self._mode = RFID.MODE_GOTO
        self._button = None

    def set_dependencies(self, hardware, desk, led):
        self._hardware = hardware
        self._desk = desk
        self._led = led

    def write_heights(self, button):
        self._button = button
        self._mode = RFID.MODE_WRITE_HEIGHT

    async def run_task(self):
        LOGGER.info('Starting run_task for RFID')
        while True:
            try:

                # The user only has 5 seconds to write the ring. After that, the
                # write is cancelled.
                write_timeout = 0

                # Wait for a ring to appear
                self._hardware.start_listen_for_rfid()
                while True:
                    if write_timeout:
                        # There is a timeout running. Count it down.
                        write_timeout -= 1
                        if write_timeout == 0:
                            # We reached 0 ... cancel the write
                            self._mode = RFID.MODE_GOTO
                            self._led.set_mode(self._led.MODE_OFF)
                    else:
                        # No timeout is running, but we might need to start one.
                        if self._mode == RFID.MODE_WRITE_HEIGHT:
                            write_timeout = 50
                            self._led.set_mode(self._led.MODE_READY_RING)
                        # Stop waiting as soon as we see a ring
                    if self._hardware.is_rfid():
                        break
                    await asyncio.sleep(0.1)

                # Get the UUID
                data = self._hardware.read_rfid_id()
                LOGGER.debug('RFID ring uuid:'+str(data))

                # Read or write based on the mode
                if self._mode == RFID.MODE_WRITE_HEIGHT:
                    data = [0xBE, 0xEE, 0xEF, self._button]
                    LOGGER.debug('Writing block 8')
                    self._hardware.write_rfid_block(RFID.DATA_BLOCK, data)
                    a, b = self._desk.get_set_points()
                    LOGGER.debug('points are '+str(a)+' '+str(b))
                    a = int(a*100)
                    b = int(b*100)
                    if self._button == 0:
                        # Only write one value: button up
                        b = 0
                    elif self._button == 1:
                        # Only write one value: button down
                        a = b
                        b = 0
                    data = [a//256, a % 256, b//256, b % 256]
                    LOGGER.debug('Writing block 9')
                    self._hardware.write_rfid_block(RFID.DATA_BLOCK+1, data)
                    self._led.set_mode(self._led.MODE_WROTE_RING)
                    await asyncio.sleep(3)  # Brief pause to show the led
                    self._led.set_mode(self._led.MODE_OFF)
                    self._mode = RFID.MODE_GOTO
                elif self._mode == RFID.MODE_GOTO:
                    # Read the set point (up or down) from the ring and GOTO that spot.
                    data1 = self._hardware.read_rfid_block(RFID.DATA_BLOCK)
                    # Make sure we have written this data (magic 0xBEEEEF)
                    data2 = self._hardware.read_rfid_block(RFID.DATA_BLOCK+1)
                    LOGGER.debug('Data blocks: '+str(data1)+' '+str(data2))
                    if data1 and data2:
                        if data1[0] == 0xBE and data1[1] == 0xEE and data1[2] == 0xEF:
                            button = data1[3]
                            a = (data2[0]*256 + data2[1]) / 100
                            b = (data2[2]*256 + data2[3]) / 100
                            LOGGER.debug('this is our ring ' +
                                         str(button)+' '+str(a)+' '+str(b))
                            if button == 0:  # UP
                                self._desk.set_point_up(a)
                                self._desk.goto(a)
                                LOGGER.debug('GOTO UP '+str(a))
                            elif button == 1:  # DOWN
                                self._desk.set_point_down(a)
                                self._desk.goto(a)
                                LOGGER.debug('GOTO DOWN '+str(a))
                            elif button == 2:  # BOTH
                                self._desk.set_point_up(a)
                                self._desk.set_point_down(b)
                                if self._desk.is_up_last_target():
                                    # Last time we went up. Go down now.
                                    self._desk.set_up_last_target(False)
                                    self._desk.goto(b)
                                    LOGGER.debug('GOTO TOGGLE DOWN '+str(b))
                                else:
                                    # Last time we went down. Go up now.
                                    self._desk.set_up_last_target(True)
                                    self._desk.goto(a)
                                    LOGGER.debug('GOTO TOGGLE UP '+str(a))
                            else:
                                LOGGER.error('Unknown button mode from ring'+str(data1)+' '+str(data2))

                elif self._mode == RFID.MODE_IGNORE:
                    # Ignoring rfid rings.
                    pass
                else:
                    # We should never get here
                    LOGGER.error('Unknown mode:', self._mode)

                # Wait for the ring to go away
                while True:
                    data = self._hardware.read_rfid_id()
                    if not data:
                        break
                    await asyncio.sleep(0.25)
                await asyncio.sleep(1)

            except Exception as ex:
                # If something goes wrong, we hope it is transient
                LOGGER.debug(
                    'ignoring an exception talking to the RFID ring'+str(ex))
                await asyncio.sleep(1)
