from machine import I2C
import time

class DPS310:
    ADDR = 0x77

    def __init__(self, i2c):
        self.i2c = i2c
        self.i2c.writeto_mem(self.ADDR, 0x0C, bytes([0x09]))
        time.sleep_ms(50)
        while True:
            mc = self.i2c.readfrom_mem(self.ADDR, 0x08, 1)[0]
            if mc & 0xC0:
                break
            time.sleep_ms(10)
        self._read_coefficients()
        src = self.i2c.readfrom_mem(self.ADDR, 0x28, 1)[0]
        tmp_src = (src & 0x80) >> 7
        self.i2c.writeto_mem(self.ADDR, 0x06, bytes([0x34]))
        self.i2c.writeto_mem(self.ADDR, 0x07, bytes([(tmp_src << 7) | 0x34]))
        self.i2c.writeto_mem(self.ADDR, 0x09, bytes([0x0C]))
        self.i2c.writeto_mem(self.ADDR, 0x08, bytes([0x07]))
        self.kP = 253952
        self.kT = 253952
        time.sleep_ms(100)

    @staticmethod
    def _twos(value, bits):
        if value & (1 << (bits - 1)):
            value -= (1 << bits)
        return value

    def _read_coefficients(self):
        c = self.i2c.readfrom_mem(self.ADDR, 0x10, 18)
        self.c0  = self._twos((c[0] << 4) | ((c[1] >> 4) & 0x0F), 12)
        self.c1  = self._twos(((c[1] & 0x0F) << 8) | c[2], 12)
        self.c00 = self._twos((c[3] << 12) | (c[4] << 4) | ((c[5] >> 4) & 0x0F), 20)
        self.c10 = self._twos(((c[5] & 0x0F) << 16) | (c[6] << 8) | c[7], 20)
        self.c01 = self._twos((c[8] << 8) | c[9], 16)
        self.c11 = self._twos((c[10] << 8) | c[11], 16)
        self.c20 = self._twos((c[12] << 8) | c[13], 16)
        self.c21 = self._twos((c[14] << 8) | c[15], 16)
        self.c30 = self._twos((c[16] << 8) | c[17], 16)

    def read(self):
        d = self.i2c.readfrom_mem(self.ADDR, 0x00, 6)
        raw_p = self._twos((d[0] << 16) | (d[1] << 8) | d[2], 24)
        raw_t = self._twos((d[3] << 16) | (d[4] << 8) | d[5], 24)
        Psc = raw_p / self.kP
        Tsc = raw_t / self.kT
        temperature = self.c0 * 0.5 + self.c1 * Tsc
        pressure = (self.c00
                    + Psc * (self.c10 + Psc * (self.c20 + Psc * self.c30))
                    + Tsc * self.c01
                    + Tsc * Psc * (self.c11 + Psc * self.c21))
        return temperature, pressure
