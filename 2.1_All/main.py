from machine import I2C, Pin
import time
from scd41 import SCD41
from dps310 import DPS310
from rpr0521rs import RPR0521RS
from bh1750 import BH1750

i2c = I2C(0, sda=Pin(1), scl=Pin(0), freq=100000)


def safe_init(name, fn):
    try:
        return fn()
    except Exception as e:
        print("{} 初始化失败: {}".format(name, e))
        return None


scd41  = safe_init("SCD41",   lambda: SCD41(i2c))
dps310 = safe_init("DPS310",  lambda: DPS310(i2c))
rpr    = safe_init("RPR0521", lambda: RPR0521RS(i2c))
bh     = safe_init("BH1750",  lambda: BH1750(i2c))

time.sleep(1)

if rpr and bh:
    try:
        ref = bh.read_lux()
        if ref > 5:
            d0, d1 = rpr.read_raw()
            if d0 == 0 and d1 == 0:
                rpr.reinit()
                time.sleep_ms(600)
            rpr.calibrate_with(ref)
    except Exception:
        pass


# SCD41 上次成功读到的值(用于读取失败时复用)
last_scd41 = None


while True:
    # SCD41(读失败就沿用上次)
    if scd41:
        try:
            scd41.wake_up()
            scd41.measure_single_shot()
            time.sleep(5)
            co2, scd_t, scd_h = scd41.read_measurement()
            last_scd41 = (co2, scd_t, scd_h)
        except Exception:
            pass   # 失败时不报错,沿用 last_scd41

        if last_scd41 is not None:
            co2, scd_t, scd_h = last_scd41
            print("SCD41 co2: {} ppm, temperature: {:.2f} C, humidity: {:.2f} %RH".format(
                co2, scd_t, scd_h))

    # DPS310
    if dps310:
        try:
            dps_t, dps_p = dps310.read()
            print("DPS310 temperature: {:.2f} C, air_pressure: {:.2f} hPa".format(
                dps_t, dps_p / 100.0))
        except Exception as e:
            print("DPS310 读取出错:", e)

    # RPR-0521
    if rpr:
        try:
            d0, d1 = rpr.read_raw()
            if d0 == 0 and d1 == 0:
                rpr.reinit()
                time.sleep_ms(600)
                d0, d1 = rpr.read_raw()
            vis_lux = rpr.read_lux()
            print("RPR0521 illumination: {:.2f} lx, infrared_illumination: {} count".format(
                vis_lux, d1))
        except Exception as e:
            print("RPR0521 读取出错:", e)

    # BH1750
    if bh:
        try:
            print("BH1750 illumination: {:.2f} lx".format(bh.read_lux()))
        except Exception as e:
            print("BH1750 读取出错:", e)

    print()
    time.sleep(10)
