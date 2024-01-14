import aiohttp.web  # python3 -m pip install aiohttp
import hardware

"""
My standard run-on-startup for pi:
  - Add this line to /etc/rc.local (before the exit 0):
  -   /home/pi/ONBOOT.sh 2> /home/pi/ONBOOT.errors > /home/pi/ONBOOT.stdout &
  - Add the following ONBOOT.sh script to /home/pi and make it executable with "chmod +x ONBOOT.sh":

#!/bin/bash
cd /home/pi/??directory??
/usr/bin/python3 ??name??
"""


async def root_handler(request):
    # Redirect to index.html
    return aiohttp.web.HTTPFound('/index.html')


async def get_handler_desk(request):
    # This is GET so you can use a browser. And so it
    # avoids CORS just in case.

    # desk              : both buttons released
    # /desk?raise       : "raise" button pressed
    # /desk?lower       : "lower" button pressed
    # /desk?raise&lower : both buttons pressed
    # /desk?goto=30.5   : set an absolute height

    if 'goto' in request.rel_url.query:
        do_goto = request.rel_url.query['goto']
        resp = f'goto={do_goto}'
        print(resp)
        hardware.move_to(float(do_goto))
    else:
        do_raise = 'raise' in request.rel_url.query
        do_lower = 'lower' in request.rel_url.query
        hardware.set_switches(do_raise, do_lower)
        resp = f'raise={do_raise} lower={do_lower}'
        print(resp)

    return aiohttp.web.Response(text=resp)


app = aiohttp.web.Application()
app.router.add_route('*', '/', root_handler)
app.router.add_route('GET', '/desk', get_handler_desk)
app.router.add_static('/', path='webroot/', name='static')

if __name__ == '__main__':
    aiohttp.web.run_app(app, port=80)
