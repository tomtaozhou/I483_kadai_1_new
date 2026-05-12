from machine import I2C, Pin
import time
from bh1750 import BH1750

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)
sensor = BH1750(i2c)

while True:
    lux = sensor.read_lux()
    print("[BH1750] 照度: {:.2f} lx".format(lux))
    time.sleep(15)
