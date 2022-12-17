from aiohttp import web

async def get_handler_desk(request):
    # This is GET so you can use a browser. And so it
    # avoids CORS just in case.
    
    # desk              : both buttons released
    # /desk?raise       : "raise" button pressed
    # /desk?lower       : "lower" button pressed
    # /desk?raise&lower : both buttons pressed

    do_raise = False
    do_lower = False

    if 'raise' in request.query:        
        do_raise = True
        
    if 'lower' in request.query:
        do_lower = True            
    
    # TODO twiddle the GPIO pins
    
    return web.Response(text=f'raise={do_raise} lower={do_lower}')

app = web.Application()
app.router.add_route('GET', '/desk', get_handler_desk)
app.router.add_static('/', path='webroot/', name='static')

if __name__ == '__main__':
    web.run_app(app)
