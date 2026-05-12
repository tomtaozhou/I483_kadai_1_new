#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/i2c.h"
#include "esp_log.h"

#define I2C_MASTER_SCL_IO    22
#define I2C_MASTER_SDA_IO    21
#define I2C_MASTER_NUM       I2C_NUM_0
#define I2C_MASTER_FREQ_HZ   100000
#define DPS310_ADDR          0x77

#define DPS310_REG_PSR_B2    0x00
#define DPS310_REG_PRS_CFG   0x06
#define DPS310_REG_TMP_CFG   0x07
#define DPS310_REG_MEAS_CFG  0x08
#define DPS310_REG_CFG_REG   0x09
#define DPS310_REG_RESET     0x0C
#define DPS310_REG_PID       0x0D
#define DPS310_REG_COEF      0x10
#define DPS310_REG_COEF_SRCE 0x28

static const char *TAG = "DPS310";

static int32_t c0, c1, c00, c10, c01, c11, c20, c21, c30;
static int32_t kP = 253952;
static int32_t kT = 253952;

static esp_err_t i2c_master_init(void) {
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };
    i2c_param_config(I2C_MASTER_NUM, &conf);
    return i2c_driver_install(I2C_MASTER_NUM, conf.mode, 0, 0, 0);
}

static esp_err_t dps310_write_reg(uint8_t reg, uint8_t data) {
    uint8_t buf[2] = {reg, data};
    return i2c_master_write_to_device(I2C_MASTER_NUM, DPS310_ADDR, buf, 2, pdMS_TO_TICKS(100));
}

static esp_err_t dps310_read_regs(uint8_t reg, uint8_t *data, size_t len) {
    return i2c_master_write_read_device(I2C_MASTER_NUM, DPS310_ADDR, &reg, 1, data, len, pdMS_TO_TICKS(100));
}

static int32_t two_complement(int32_t value, uint8_t bits) {
    if (value & (1 << (bits - 1))) {
        value -= (1 << bits);
    }
    return value;
}

static void dps310_read_coefficients(void) {
    uint8_t coef[18];
    dps310_read_regs(DPS310_REG_COEF, coef, 18);

    c0  = ((int32_t)coef[0] << 4) | ((coef[1] >> 4) & 0x0F);
    c0  = two_complement(c0, 12);
    c1  = (((int32_t)coef[1] & 0x0F) << 8) | coef[2];
    c1  = two_complement(c1, 12);
    c00 = ((int32_t)coef[3] << 12) | ((int32_t)coef[4] << 4) | ((coef[5] >> 4) & 0x0F);
    c00 = two_complement(c00, 20);
    c10 = (((int32_t)coef[5] & 0x0F) << 16) | ((int32_t)coef[6] << 8) | coef[7];
    c10 = two_complement(c10, 20);
    c01 = ((int32_t)coef[8] << 8) | coef[9];
    c01 = two_complement(c01, 16);
    c11 = ((int32_t)coef[10] << 8) | coef[11];
    c11 = two_complement(c11, 16);
    c20 = ((int32_t)coef[12] << 8) | coef[13];
    c20 = two_complement(c20, 16);
    c21 = ((int32_t)coef[14] << 8) | coef[15];
    c21 = two_complement(c21, 16);
    c30 = ((int32_t)coef[16] << 8) | coef[17];
    c30 = two_complement(c30, 16);
}

static void dps310_init(void) {
    dps310_write_reg(DPS310_REG_RESET, 0x09);
    vTaskDelay(pdMS_TO_TICKS(50));

    uint8_t pid;
    dps310_read_regs(DPS310_REG_PID, &pid, 1);
    ESP_LOGI(TAG, "DPS310 PID: 0x%02X", pid);

    uint8_t meas_cfg = 0;
    while (!(meas_cfg & 0xC0)) {
        dps310_read_regs(DPS310_REG_MEAS_CFG, &meas_cfg, 1);
        vTaskDelay(pdMS_TO_TICKS(10));
    }

    dps310_read_coefficients();

    uint8_t coef_src;
    dps310_read_regs(DPS310_REG_COEF_SRCE, &coef_src, 1);
    uint8_t tmp_src = (coef_src & 0x80) >> 7;

    dps310_write_reg(DPS310_REG_PRS_CFG, 0x34);
    dps310_write_reg(DPS310_REG_TMP_CFG, (tmp_src << 7) | 0x34);
    dps310_write_reg(DPS310_REG_CFG_REG, 0x0C);
    dps310_write_reg(DPS310_REG_MEAS_CFG, 0x07);

    vTaskDelay(pdMS_TO_TICKS(100));
}

static void dps310_read_measurement(float *temperature, float *pressure) {
    uint8_t data[6];
    dps310_read_regs(DPS310_REG_PSR_B2, data, 6);

    int32_t raw_p = ((int32_t)data[0] << 16) | ((int32_t)data[1] << 8) | data[2];
    raw_p = two_complement(raw_p, 24);
    int32_t raw_t = ((int32_t)data[3] << 16) | ((int32_t)data[4] << 8) | data[5];
    raw_t = two_complement(raw_t, 24);

    float Praw_sc = (float)raw_p / kP;
    float Traw_sc = (float)raw_t / kT;

    *temperature = c0 * 0.5f + c1 * Traw_sc;
    *pressure = c00 + Praw_sc * (c10 + Praw_sc * (c20 + Praw_sc * c30))
              + Traw_sc * c01 + Traw_sc * Praw_sc * (c11 + Praw_sc * c21);
}

void app_main(void) {
    ESP_ERROR_CHECK(i2c_master_init());
    dps310_init();
    ESP_LOGI(TAG, "DPS310 init done");

    while (1) {
        float temperature, pressure;
        dps310_read_measurement(&temperature, &pressure);

        printf("[DPS310] 温度: %.2f C, 気圧: %.2f hPa\n",
               temperature, pressure / 100.0f);

        vTaskDelay(pdMS_TO_TICKS(15000));
    }
}
