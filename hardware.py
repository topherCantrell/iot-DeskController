import sys
import time

import RPi.GPIO as GPIO

PIN_RAISE = 24
PIN_LOWER = 23
PIN_TRIGGER = 5
PIN_ECHO = 6

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_RAISE, GPIO.OUT)
GPIO.setup(PIN_LOWER, GPIO.OUT)
GPIO.output(PIN_RAISE, False)
GPIO.output(PIN_LOWER, False)

GPIO.setup(PIN_TRIGGER, GPIO.OUT)
GPIO.setup(PIN_ECHO, GPIO.IN)
GPIO.output(PIN_TRIGGER, False)


def set_switches(do_raise, do_lower):
    GPIO.output(PIN_RAISE, do_raise)
    GPIO.output(PIN_LOWER, do_lower)


def get_avg_height(samples=10):
    height = 0
    for i in range(samples):
        a = get_height()
        # print(a)
        time.sleep(0.01)
        height += a
    return height / samples


def get_height():
    GPIO.output(PIN_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(PIN_TRIGGER, False)
    while not GPIO.input(PIN_ECHO):
        pulse_start = time.time()
    while GPIO.input(PIN_ECHO):
        pulse_end = time.time()
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    return distance


LAG = 1  # cm to add/subtract height for stopping point (determined experimentally)


def move_to(height):
    current_height = get_avg_height()
    if height > current_height:
        # Need to raise the desk
        height -= LAG  # Stopping a little early (coasting)
        set_switches(do_raise=True, do_lower=False)
        while get_avg_height() < height:
            time.sleep(0.00001)
        set_switches(do_raise=False, do_lower=False)
    else:
        # Need to lower the desk
        height += LAG  # Stopping a little early (coasting)
        set_switches(do_raise=False, do_lower=True)
        while get_avg_height() > height:
            time.sleep(0.00001)
        set_switches(do_raise=False, do_lower=False)


def bump(up):
    if up:
        set_switches(do_raise=True, do_lower=False)
    else:
        set_switches(do_raise=False, do_lower=True)
    time.sleep(0.5)
    set_switches(False, False)


if __name__ == '__main__':

    if sys.argv[1] == 'switches':
        do_raise = sys.argv[2].upper()[0] == 'T'
        do_lower = sys.argv[3].upper()[0] == 'T'
        set_switches(do_raise, do_lower)
    elif sys.argv[1] == 'goto':
        height = float(sys.argv[2])
        move_to(height)
    elif sys.argv[1] == 'bump':
        bump(sys.argv[2].upper()[0] == 'U')
    else:
        pass

    distance = get_avg_height()
    print(f'Distance: {distance}cm')
