import gc
from machine import ADC, Pin, Signal

from microdot import Microdot, redirect

gc.collect()

input = Pin(16, Pin.IN)

class LDR:
    def __init__(self, pin_int: int) -> None:
        self.pin = ADC(pin_int)
    def get_raw_value(self):
        return self.pin.read_u16()
    def get_light_perc(self):
        return round(self.get_raw_value()/65535*100,2)

app = Microdot()

ldr = LDR(0)

led_pin = Pin(2, Pin.OUT)
led = Signal(led_pin, invert=True)
led.off()


@app.route('/')
async def index(request):
    status = 'on' if led.value() else 'off'

    html = """
<html>
    <head> 
        <title>Helios</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" href="data:,">
        <style>
        html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
        h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none; 
        border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
        .button2{background-color: #4286f4;}
        </style>
    </head>
    <body>
        <h1>Helios</h1> 
        <p>LDR state: <strong>""" + f'{ldr.get_light_perc()}' + """</strong></p>
        <p>LED state: <strong>""" + status + """</strong></p>
        <p><a href="/led/toggle"><button class="button">Toggle</button></a></p>
    </body>
</html>"""

    return html, {'Content-Type': 'text/html'}


@app.route('/led/toggle')
async def led_toggle(request):
    led.off() if led.value() else led.on()
    return redirect('/')

app.run(port=80, debug=False)
