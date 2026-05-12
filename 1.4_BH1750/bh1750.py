from machine import I2C
import time

class BH1750:
    PWR_ON          = 0x01
    RESET           = 0x07
    CONT_HRES_MODE2 = 0x11

    def __init__(self, i2c, addr=0x23):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto(self.addr, bytes([self.PWR_ON]))
        time.sleep_ms(10)
        self.i2c.writeto(self.addr, bytes([self.RESET]))
        time.sleep_ms(10)
        self.i2c.writeto(self.addr, bytes([self.CONT_HRES_MODE2]))
        time.sleep_ms(180)

    def read_lux(self):
        data = self.i2c.readfrom(self.addr, 2)
        raw = (data[0] << 8) | data[1]
        return raw / 2.4
