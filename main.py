import asyncio
import gc
import json

from machine import ADC, Pin, Signal
from micropython import const

gc.collect()

input = Pin(16, Pin.IN)
led_pin = Pin(2, Pin.OUT)
led = Signal(led_pin, invert=True)
led.off()

class LDR:
    def __init__(self, adc_pin: int) -> None:
        self.ldr = ADC(adc_pin)

    def get_percent(self) -> float:
        return self.ldr.read_u16() / 65535 * 100

ldr = LDR(0)

HTML_HEAD = const("""
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
""")

async def response_file(writer, file_path: str, content_type: str):
    with open(file_path) as f:
        writer.write(f'HTTP/1.0 200 OK\r\nContent-type: text/{content_type}\r\n\r\n')
        writer.write(f.read())
    await writer.drain()
    await writer.wait_closed()

async def response_json(writer, json_dict: dict):
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/json\r\n\r\n')
    writer.write(json.dumps(json_dict))
    await writer.drain()
    await writer.wait_closed()

async def response_html(writer, html: str):
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(html)
    await writer.drain()
    await writer.wait_closed()

async def response_event(writer, generate):
    writer.write('HTTP/1.0 200 OK\nContent-type: text/event-stream\nCache-Control: no-cache\n\n')
    await writer.drain()
    counter = 0
    try:
        while True:
            writer.write(f'id: {counter}\n')
            writer.write('event: ldrData\n')
            data = { 
                'ldrData': ldr.get_percent(),
            }
            data_str = f'data: {json.dumps(data)}'
            writer.write(data_str)
            writer.write('\n\n')
            await writer.drain()
            await asyncio.sleep(0.25)
            counter += 1
    finally:
        await writer.wait_closed()

# HTML template for the webpage
def homepage(led_state, ldr_state):
    html = f"""
<!DOCTYPE html>
<html>
    {HTML_HEAD}
    <body>
        <h1>Helios</h1> 
        <h2>Led Control</h2>
        <p>LED state: {led_state}</p>
        <p><a href="/led/toggle"><button class="button">Toggle</button></a></p>
        <h2>Refresh LDR state</h2>
        <p><a href="/ldr"><button class="button">Fetch</button></a></p>
        <p>LDR state: <strong>{ldr_state}%</strong></p>
    </body>
</html>
"""
    return html 

async def handle_client(reader, writer):
    # global led_state
    # led_state = led.value()
    # global ldr_state
    # ldr_state = ldr.get_percent()
    
    request_line = await reader.readline()
    
    # Skip the rest of the HTTP headers
    while await reader.readline() != b"\r\n":
        pass
    
    verb, url, _ = str(request_line, 'utf-8').split()
    print(f'{verb} Request: {url}')
    
    # Process the request and update variables
    if url == '/events/ldr':
        return await response_event(writer, 9)
    elif url == '/style.css':
        return await response_file(writer, 'style.css', 'css')
    elif url == '/script.js':
        return await response_file(writer, 'script.js', 'javascript')
    elif url == '/led/toggle':
        led.off() if led.value() else led.on()
        led_state = 'ON' if led.value() else 'OFF'
        print(f'LED now {led_state}')
        return await response_json(writer, {"led": led_state})
    elif url == '/ldr':
        ldr_state = ldr.get_percent()
        print(f'LDR reads {ldr_state}')
        return await response_json(writer, {"graph1": ldr_state})

    with open('graph.html', 'r') as f:
        html = f.read()
    return await response_html(writer, html)
    
async def blink_led():
    while True:
        led.off() if led.value() else led.on()  # Toggle LED state
        await asyncio.sleep(0.5)  # Blink interval

async def main():    
    # Start the server and run the event loop
    server = asyncio.start_server(handle_client, "0.0.0.0", 80)
    asyncio.create_task(server)
    print('Server running...')
    
    # while True:
    #     # Add other tasks that you might need to do in the loop
    #     await asyncio.sleep(5)
        

# Create an Event Loop
loop = asyncio.get_event_loop()
# Create a task to run the main function
loop.create_task(main())

try:
    # Run the event loop indefinitely
    loop.run_forever()
except Exception as e:
    print('Error occured: ', e)
except KeyboardInterrupt:
    print('Program Interrupted by the user')
