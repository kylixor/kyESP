import asyncio
import gc

from machine import Pin, Signal, ADC
from micropython import const

gc.collect()

input = Pin(16, Pin.IN)
led_pin = Pin(2, Pin.OUT)
led = Signal(led_pin, invert=True)
led.off()

ldr = ADC(0)

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

# HTML template for the webpage
def webpage(led_state, ldr_state):
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
        <p>LDR state: <strong>{ldr_state}</strong></p>
    </body>
</html>
"""
    return html

async def handle_client(reader, writer):
    global led_state
    led_state = led.value()
    global ldr_state
    ldr_state = ldr.read_u16()
    
    request_line = await reader.readline()
    print('Request:', request_line)
    
    # Skip HTTP request headers
    while await reader.readline() != b"\r\n":
        pass
    
    request = str(request_line, 'utf-8').split()[1]
    print('Request:', request)
    
    # Process the request and update variables
    if request == '/led/toggle':
        led.off() if led.value() else led.on()
        led_state = led.value()
        print(f'LED now {led_state}')
    elif request == '/ldr':
        ldr_state = ldr.read_u16()
        print(f'LDR reads {ldr_state}')

    # Generate HTML response
    response = webpage(led_state, ldr_state)  

    # Send the HTTP response and close the connection
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)
    await writer.drain()
    await writer.wait_closed()
    
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
