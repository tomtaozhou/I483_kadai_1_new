from machine import I2C
import time

class RPR0521RS:
    ADDR = 0x38

    REG_MODE_CONTROL   = 0x41
    REG_ALS_PS_CONTROL = 0x42
    REG_PS_DATA_LSB    = 0x44
    REG_ALS_DATA0_LSB  = 0x46
    REG_MANUFACT_ID    = 0x92

    def __init__(self, i2c):
        self.i2c = i2c
        self.i2c.readfrom_mem(self.ADDR, self.REG_MANUFACT_ID, 1)
        self.i2c.writeto_mem(self.ADDR, self.REG_MODE_CONTROL, bytes([0xC6]))
        self.i2c.writeto_mem(self.ADDR, self.REG_ALS_PS_CONTROL, bytes([0x02]))
        self.gain0 = 1
        self.gain1 = 1
        self.meas_time = 100
        time.sleep_ms(200)

    def read_ps(self):
        data = self.i2c.readfrom_mem(self.ADDR, self.REG_PS_DATA_LSB, 2)
        return (data[0] | (data[1] << 8)) & 0x0FFF

    def read_lux(self):
        data = self.i2c.readfrom_mem(self.ADDR, self.REG_ALS_DATA0_LSB, 4)
        data0 = data[0] | (data[1] << 8)
        data1 = data[2] | (data[3] << 8)
        if data0 == 0:
            return 0.0
        d0 = data0 / self.gain0 * (100.0 / self.meas_time)
        d1 = data1 / self.gain1 * (100.0 / self.meas_time)
        ratio = d1 / d0
        if ratio < 0.595:
            lux = 1.682 * d0 - 1.877 * d1
        elif ratio < 1.015:
            lux = 0.644 * d0 - 0.132 * d1
        elif ratio < 1.352:
            lux = 0.756 * d0 - 0.243 * d1
        elif ratio < 3.053:
            lux = 0.766 * d0 - 0.250 * d1
        else:
            lux = 0.0
        return max(0.0, lux)
