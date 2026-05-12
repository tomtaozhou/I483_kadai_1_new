from machine import I2C
import time

class SCD41:
    ADDR = 0x62

    CMD_START_PERIODIC   = 0x21B1
    CMD_READ_MEASUREMENT = 0xEC05
    CMD_STOP_PERIODIC    = 0x3F86
    CMD_GET_DATA_READY   = 0xE4B8
    CMD_REINIT           = 0x3646

    def __init__(self, i2c):
        self.i2c = i2c
        self._send_cmd(self.CMD_STOP_PERIODIC)
        time.sleep_ms(500)
        self._send_cmd(self.CMD_REINIT)
        time.sleep_ms(30)

    @staticmethod
    def _crc8(data):
        crc = 0xFF
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    def _send_cmd(self, cmd):
        self.i2c.writeto(self.ADDR, bytes([cmd >> 8, cmd & 0xFF]))

    def _read(self, cmd, length, delay_ms=1):
        self._send_cmd(cmd)
        time.sleep_ms(delay_ms)
        return self.i2c.readfrom(self.ADDR, length)

    def start_periodic_measurement(self):
        self._send_cmd(self.CMD_START_PERIODIC)

    def data_ready(self):
        data = self._read(self.CMD_GET_DATA_READY, 3)
        return (((data[0] & 0x07) << 8) | data[1]) != 0

    def read_measurement(self):
        data = self._read(self.CMD_READ_MEASUREMENT, 9)
        for i in range(0, 9, 3):
            if self._crc8(data[i:i+2]) != data[i+2]:
                raise ValueError("CRC mismatch")
        co2 = (data[0] << 8) | data[1]
        temp_raw = (data[3] << 8) | data[4]
        hum_raw = (data[6] << 8) | data[7]
        temperature = -45 + 175 * temp_raw / 65535
        humidity = 100 * hum_raw / 65535
        return co2, temperature, humidity
