import board
import digitalio
import busio
from adafruit_pn532.i2c import PN532_I2C
import adafruit_hcsr04
import time

# Motors
pin_motor_up = digitalio.DigitalInOut(board.GP2)
pin_motor_up.direction = digitalio.Direction.OUTPUT
pin_motor_down = digitalio.DigitalInOut(board.GP3)
pin_motor_down.direction = digitalio.Direction.OUTPUT

# Desk buttons (usable if configured through jumpers)
pin_desk_button_up = digitalio.DigitalInOut(board.GP4)
pin_desk_button_up.direction = digitalio.Direction.INPUT
pin_desk_button_up.pull = digitalio.Pull.UP
pin_desk_button_down = digitalio.DigitalInOut(board.GP5)
pin_desk_button_down.direction = digitalio.Direction.INPUT
pin_desk_button_down.pull = digitalio.Pull.UP

# Extra buttons
pin_extra_button_up = digitalio.DigitalInOut(board.GP6)
pin_extra_button_up.direction = digitalio.Direction.INPUT
pin_extra_button_up.pull = digitalio.Pull.UP
pin_extra_button_down = digitalio.DigitalInOut(board.GP7)
pin_extra_button_down.direction = digitalio.Direction.INPUT
pin_extra_button_down.pull = digitalio.Pull.UP

# LED
pin_led = digitalio.DigitalInOut(board.GP10)
pin_led.direction = digitalio.Direction.OUTPUT

# Distance
pin_sonar_trigger = board.GP8
pin_sonar_echo = board.GP9

# RFID (optional)
pin_rfid_irq = digitalio.DigitalInOut(board.GP11)
pin_rfid_reset = digitalio.DigitalInOut(board.GP15)
pin_rfid_reset.direction = digitalio.Direction.OUTPUT


class Hardware:

    def __init__(self, has_rfid, has_sonar):
        self._last_height = -1
        self._sonar = None
        self._pn532 = None

        # Connect to the sonar
        if has_sonar:
            self._sonar = adafruit_hcsr04.HCSR04(
                trigger_pin=pin_sonar_trigger, echo_pin=pin_sonar_echo)

        # Connect to the rfid reader
        if has_rfid:
            rfid_i2c = busio.I2C(scl=board.GP13, sda=board.GP12)
            # Sometimes, when the board starts up, we have trouble talking to the rfid
            # reader. This loop retries 3 times.
            for i in range(3):
                try:
                    self._pn532 = PN532_I2C(
                        rfid_i2c, debug=False, reset=pin_rfid_reset)
                    break
                except Exception:
                    if i == 2:
                        # Retry 3 times, then let the exception go
                        print('Could not connect to PN532.')
                        raise
                    time.sleep(0.5)
                    print('Trouble connecting to RFID. Trying again.')

    # Button functions

    def get_extra_buttons(self):
        return (not pin_extra_button_up.value, not pin_extra_button_down.value)

    def get_desk_buttons(self):
        return (not pin_desk_button_up.value, not pin_desk_button_down.value)

    # LED functions

    def set_led(self, led_on=True):
        pin_led.value = led_on

    # Height functions

    def get_height(self):
        if self._sonar:
            self._last_height = self._sonar.distance  # This is a method call
        return self._last_height

    def get_last_height(self):
        # Use this when the goto state is MOVING. GOTO reads
        # the height, and you don't want to interfere.
        return self._last_height

    # Motor functions

    def get_motors(self):
        return (pin_motor_up.value, pin_motor_down.value)

    def set_motors(self, go_up=None, go_down=None):
        if go_up is not None:
            pin_motor_up.value = go_up
        if go_down is not None:
            pin_motor_down.value = go_down

    # RFID functions

    def debug_wait_for_rfid(self):
        # THIS METHOD BLOCKS -- good for debugging
        while True:
            g = self._pn532.read_passive_target(timeout=0.5)
            if g:
                return list(g)

    def start_listen_for_rfid(self):
        # This sets the IRQ pin to True. When a target is seen,
        # the pin goes low and stays low until the next rfid
        # operation.
        self._pn532.listen_for_passive_target()

    def is_rfid(self):
        # When you "start_listen", this pin goes low and stays
        # low until you talk to the rfid board.
        return not pin_rfid_irq.value

    def read_rfid_id(self):
        # Returns 4 bytes
        data = self._pn532.read_passive_target(timeout=0.5)
        if data is None:
            return data
        return list(data)

    def write_rfid_block(self, number, data):
        # Pass in a list of 4 integers
        self._pn532.read_passive_target(timeout=0.5)
        self._pn532.ntag2xx_write_block(number, bytes(data))

    def read_rfid_block(self, number):
        # Returns a list of 4 integers
        self._pn532.read_passive_target(timeout=0.5)
        return list(self._pn532.ntag2xx_read_block(number))
