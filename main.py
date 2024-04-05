import asyncio
import gc

import json
from machine import Pin, Signal, ADC
from micropython import const

gc.collect()

input = Pin(16, Pin.IN)
led_pin = Pin(2, Pin.OUT)
led = Signal(led_pin, invert=True)
led.off()

class LDR:
    def __init__(self, adc_pin: int) -> None:
        self.ldr = ADC(adc_pin)

    def get_percent(self) -> int:
        return int(self.ldr.read_u16() / 65535 * 100)

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

GRAPH_HTML = const("""
<!DOCTYPE html>
<html>
  <head>
    <title>ESP IOT DASHBOARD</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/png" href="favicon.png">
    <link rel="stylesheet" type="text/css" href="style.css">
    <script src="https://code.highcharts.com/highcharts.js"></script>
  </head>
  <body>
    <div class="topnav">
      <h1>ESP WEB SERVER CHARTS</h1>
    </div>
    <div class="content">
      <div class="card-grid">
        <div class="card">
          <p class="card-title">Temperature Chart</p>
          <div id="chart-temperature" class="chart-container"></div>
        </div>
      </div>
    </div>
    <script src="script.js"></script>
  </body>
</html>
""")

GRAPH_CSS = const("""
html {
    font-family: Arial, Helvetica, sans-serif;
    display: inline-block;
    text-align: center;
}

h1 {
    font-size: 1.8rem;
    color: white;
}

p {
    font-size: 1.4rem;
}

.topnav {
    overflow: hidden;
    background-color: #0A1128;
}

body {
    margin: 0;
}

.content {
    padding: 5%;
}

.card-grid {
    max-width: 1200px;
    margin: 0 auto;
    display: grid;
    grid-gap: 2rem;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.card {
    background-color: white;
    box-shadow: 2px 2px 12px 1px rgba(140, 140, 140, .5);
}

.card-title {
    font-size: 1.2rem;
    font-weight: bold;
    color: #034078
}

.chart-container {
    padding-right: 5%;
    padding-left: 5%;
}
""")

GRAPH_JS = const("""
// Complete project details: https://randomnerdtutorials.com/esp32-plot-readings-charts-multiple/

// Get current sensor readings when the page loads
window.addEventListener('load', function() {
    setInterval(function() {
        getReadings();
    }, 1000);
});

// Create Temperature Chart
var chartT = new Highcharts.Chart({
  chart:{
    renderTo:'chart-temperature'
  },
  series: [
    {
      name: 'Light',
      type: 'line',
      color: '#101D42',
      marker: {
        symbol: 'circle',
        radius: 3,
        fillColor: '#101D42',
      }
    },
  ],
  title: {
    text: undefined
  },
  xAxis: {
    type: 'datetime',
    dateTimeLabelFormats: { second: '%H:%M:%S' }
  },
  yAxis: {
    title: {
      text: 'Percent of Light'
    }
  },
  credits: {
    enabled: false
  }
});


//Plot temperature in the temperature chart
function plotTemperature(jsonValue) {

  var keys = Object.keys(jsonValue);
  console.log(keys);
  console.log(keys.length);

  for (var i = 0; i < keys.length; i++){
    var x = (new Date()).getTime();
    console.log(x);
    const key = keys[i];
    var y = Number(jsonValue[key]);
    console.log(y);

    if(chartT.series[i].data.length > 40) {
      chartT.series[i].addPoint([x, y], true, true, true);
    } else {
      chartT.series[i].addPoint([x, y], true, false, true);
    }

  }
}

// Function to get current readings on the webpage when it loads for the first time
function getReadings(){
  var xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      var myObj = JSON.parse(this.responseText);
      console.log(myObj);
      plotTemperature(myObj);
    }
  };
  xhr.open("GET", "/ldr", true);
  xhr.send();
}

if (!!window.EventSource) {
  var source = new EventSource('/events');

  source.addEventListener('open', function(e) {
    console.log("Events Connected");
  }, false);

  source.addEventListener('error', function(e) {
    if (e.target.readyState != EventSource.OPEN) {
      console.log("Events Disconnected");
    }
  }, false);

  source.addEventListener('message', function(e) {
    console.log("message", e.data);
  }, false);

  source.addEventListener('new_readings', function(e) {
    console.log("new_readings", e.data);
    var myObj = JSON.parse(e.data);
    console.log(myObj);
    plotTemperature(myObj);
  }, false);
}
""")

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
    global led_state
    led_state = led.value()
    global ldr_state
    ldr_state = ldr.get_percent()
    
    request_line = await reader.readline()
    
    # Skip HTTP request headers
    while await reader.readline() != b"\r\n":
        pass
    
    verb, url, _ = str(request_line, 'utf-8').split()
    print(f'{verb} Request: {url}')
    
    # Process the request and update variables
    if url == '/style.css':
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/css\r\n\r\n')
        writer.write(GRAPH_CSS)
        await writer.drain()
        await writer.wait_closed()
        return
    elif url == '/script.js':
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/javascript\r\n\r\n')
        writer.write(GRAPH_JS)
        await writer.drain()
        await writer.wait_closed()
        return
    elif url == '/led/toggle':
        led.off() if led.value() else led.on()
        led_state = 'ON' if led.value() else 'OFF'
        print(f'LED now {led_state}')
    elif url == '/ldr':
        ldr_state = ldr.get_percent()
        print(f'LDR reads {ldr_state}')
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/json\r\n\r\n')
        writer.write(json.dumps({"graph1": ldr_state}))
        await writer.drain()
        await writer.wait_closed()
        return

    # Generate HTML response
    response = homepage(led_state, ldr_state)
    response = GRAPH_HTML

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
