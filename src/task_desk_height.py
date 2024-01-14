
import asyncio
import time
import os
import logging

LOGGER = logging.getLogger(__name__)

BUMP_UP_TIME = 0.5
BUMP_DOWN_TIME = 0.5

DRIFT_UP_DISTANCE = 1.25
DRIFT_DOWN_DISTANCE = 1.25

DESK_MIN_HEIGHT = float(os.getenv('DESK_MIN_HEIGHT'))
DESK_MAX_HEIGHT = float(os.getenv('DESK_MAX_HEIGHT'))
PRESET_TOP = float(os.getenv('PRESET_TOP'))
PRESET_BOTTOM = float(os.getenv('PRESET_BOTTOM'))


class DeskHeight:

    MODE_IDLE = 'idle'  # When the desk is still
    MODE_GOTO = 'goto'  # When the desk is moving to a spot
    MODE_MANUAL = 'manually'  # When the desk is manually moving

    def __init__(self):
        self._hardware = None
        self._mode = None
        self._target_height = None
        # Trigger to restart the goto process (with a new target)
        self._restart_goto = False
        self._set_point_up = None
        self._set_point_down = None
        self._up_was_last_target = False
        self._set_point_up = PRESET_TOP
        self._set_point_down = PRESET_BOTTOM

    def set_dependencies(self, hardware):
        self._hardware = hardware
        # Make sure the desk is not moving
        self.stop()

    def set_point_up(self, value):
        # Make sure the hardware can go to this height
        if value >= DESK_MIN_HEIGHT and value <= DESK_MAX_HEIGHT:
            self._set_point_up = value
            # Make sure the down endpoint is at or below this
            if self._set_point_down > value:
                self._set_point_down = value
        else:
            LOGGER.debug('UP POINT is out of range: '+str(value) +
                         ' '+str(DESK_MIN_HEIGHT)+' '+str(DESK_MAX_HEIGHT))

    def set_point_down(self, value):
        # Make sure the hardware can go to this height
        if value >= DESK_MIN_HEIGHT and value <= DESK_MAX_HEIGHT:
            self._set_point_down = value
            # Make sure the up endpoint is at or above this
            if self._set_point_up < value:
                self._set_point_up = value
        else:
            LOGGER.debug('DOWN POINT is out of range: '+str(value) +
                         ' '+str(DESK_MIN_HEIGHT)+' '+str(DESK_MAX_HEIGHT))

    def set_up_last_target(self, value):
        # Which button was the last target? True=up, False=down
        self._up_was_last_target = value

    def is_up_last_target(self):
        # Which button was the last target? True=up, False=down
        return self._up_was_last_target

    def get_set_points(self):
        # The up and down endpoints in that order
        return (self._set_point_up, self._set_point_down)

    def get_mode(self):
        return self._mode

    def get_height(self):
        if self._mode == DeskHeight.MODE_GOTO:
            return self._hardware.get_last_height()
        return self._hardware.get_height()

    def stop(self):
        # Stop all motion and return to IDLE
        self._hardware.set_motors(go_up=False, go_down=False)
        self._mode = DeskHeight.MODE_IDLE

    def get_motors(self):
        # Return the state of the motors: up/down -- True for running
        return self._hardware.get_motors()

    def set_motors(self, go_up, go_down):
        # Manually control the motors
        self._hardware.set_motors(go_up, go_down)
        self._mode = DeskHeight.MODE_MANUAL

    def goto(self, height_cm):
        self._target_height = height_cm
        self._restart_goto = True
        self._mode = DeskHeight.MODE_GOTO
        LOGGER.debug('GOING TO HEIGHT '+str(height_cm))

    def _get_average_height(self, samples=10, delay=0.05):
        ret = 0
        org = samples
        while samples > 0:
            ret += self._hardware.get_height()
            time.sleep(delay)  # No async here
            samples -= 1
        return ret/org

    async def run_task(self):
        LOGGER.info('Starting run_task for DeskHeight')
        LOGGER.debug('MIN/MAX: '+str(DESK_MIN_HEIGHT)+' '+str(DESK_MAX_HEIGHT))
        LOGGER.debug('PRESETS: '+str(PRESET_BOTTOM)+' '+str(PRESET_TOP))
        LOGGER.debug('Current height: '+str(self._hardware.get_height()))

        while True:
            if self._mode != DeskHeight.MODE_GOTO:
                await asyncio.sleep(0.5)
                continue

            # We only move in one direction during GOTO. If/when we over-shoot, we stop.
            # The goal is to get close and make a bump or two for fine adjustments.
            # We also look at "restart_goto" to break us out of current search.

            height = self._get_average_height()
            if height < self._target_height:
                LOGGER.debug('moving up from '+str(height) +
                             ' to '+str(self._target_height))
                adj_target_height = self._target_height - DRIFT_UP_DISTANCE
                # TODO watch for restarts
                # TODO if we are too close, skip straight to the bumps
                self._hardware.set_motors(True, False)
                while height < adj_target_height:
                    await asyncio.sleep(0.1)
                    height = self._hardware.get_height()
                self._hardware.set_motors(False, False)
                await asyncio.sleep(1)
                # TODO bumps at the end
                LOGGER.debug('final '+str(self._get_average_height()))
            else:
                LOGGER.debug('moving down from '+str(height) +
                             ' to '+str(self._target_height))
                adj_target_height = self._target_height + DRIFT_DOWN_DISTANCE
                # TODO watch for restarts
                # TODO if we are too close, skip straight to the bumps
                self._hardware.set_motors(False, True)
                while height > adj_target_height:
                    await asyncio.sleep(0.1)
                    height = self._hardware.get_height()
                self._hardware.set_motors(False, False)
                await asyncio.sleep(1)
                # TODO bumps at the end
                LOGGER.debug('final '+str(self._get_average_height()))

            # Done with goto
            self._mode = DeskHeight.MODE_IDLE
