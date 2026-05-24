from machine import I2C
import time

class SCD41:
    ADDR = 0x62

    CMD_START_PERIODIC      = 0x21B1
    CMD_STOP_PERIODIC       = 0x3F86
    CMD_GET_DATA_READY      = 0xE4B8
    CMD_READ_MEASUREMENT    = 0xEC05
    CMD_REINIT              = 0x3646
    CMD_MEASURE_SINGLE_SHOT = 0x219D
    CMD_WAKE_UP             = 0x36F6
    CMD_POWER_DOWN          = 0x36E0

    def __init__(self, i2c):
        self.i2c = i2c
        try:
            self._send_cmd(self.CMD_STOP_PERIODIC)
        except Exception:
            pass
        time.sleep_ms(500)

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

    def measure_single_shot(self):
        self._send_cmd(self.CMD_MEASURE_SINGLE_SHOT)

    def wake_up(self):
        """唤醒 SCD41。datasheet 第 19 页:max 30ms。
        注意 datasheet 说 wake_up 命令不会被 ACK,所以要忽略 I2C 错误。"""
        try:
            self._send_cmd(self.CMD_WAKE_UP)
        except Exception:
            pass
        time.sleep_ms(30)

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
