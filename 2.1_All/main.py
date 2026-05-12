from machine import I2C, Pin
import time
from scd41 import SCD41
from dps310 import DPS310
from rpr0521rs import RPR0521RS
from bh1750 import BH1750

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)
print("I2C scan:", [hex(x) for x in i2c.scan()])

scd41 = SCD41(i2c)
scd41.start_periodic_measurement()
dps310 = DPS310(i2c)
rpr = RPR0521RS(i2c)
bh = BH1750(i2c)

time.sleep(5)

while True:
    if scd41.data_ready():
        co2, scd_t, scd_h = scd41.read_measurement()
    else:
        co2, scd_t, scd_h = None, None, None
    dps_t, dps_p = dps310.read()
    rpr_lux = rpr.read_lux()
    bh_lux = bh.read_lux()

    print("[SCD41]    CO2: {} ppm, 温度: {:.2f} C, 湿度: {:.2f} %RH".format(co2, scd_t, scd_h))
    print("[DPS310]   温度: {:.2f} C, 気圧: {:.2f} hPa".format(dps_t, dps_p / 100.0))
    print("[RPR-0521] 照度: {:.2f} lx".format(rpr_lux))
    print("[BH1750]   照度: {:.2f} lx".format(bh_lux))
    print()
    time.sleep(15)
