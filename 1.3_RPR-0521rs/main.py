from machine import I2C, Pin
import time
from rpr0521rs import RPR0521RS

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)
sensor = RPR0521RS(i2c)

while True:
    lux = sensor.read_lux()
    print("[RPR-0521] 照度: {:.2f} lx".format(lux))
    time.sleep(15)
