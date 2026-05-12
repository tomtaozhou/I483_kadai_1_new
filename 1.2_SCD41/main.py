from machine import I2C, Pin
import time
from scd41 import SCD41

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)
sensor = SCD41(i2c)
sensor.start_periodic_measurement()

while True:
    while not sensor.data_ready():
        time.sleep_ms(200)
    co2, t, h = sensor.read_measurement()
    print("[SCD41] CO2: {} ppm, 温度: {:.2f} C, 湿度: {:.2f} %RH".format(co2, t, h))
    time.sleep(15)
