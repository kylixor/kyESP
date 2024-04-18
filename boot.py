import gc
from time import sleep
gc.collect()

from machine import Pin, Signal
gc.collect()
from network import STA_IF, WLAN
gc.collect()

print('Reading in WiFi credentials...')
with open('.env') as file:
    SSID = file.readline().rstrip("\n")
    WIFI_KEY = file.readline().rstrip("\n")

led_pin = Pin(2, Pin.OUT)
led = Signal(led_pin, invert=True)
led.off()

w = WLAN(STA_IF)
w.active(True)
print(f'Connecting to "{SSID}" with key "{WIFI_KEY}"')
w.connect(SSID, WIFI_KEY)
while not w.isconnected():
    pass
print('Connected to network')
print(w.ifconfig()[0])
led.on()
sleep(0.25)
led.off()
sleep(0.25)
led.on()

gc.collect()