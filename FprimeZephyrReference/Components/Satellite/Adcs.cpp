#include "FprimeZephyrReference/Components/Satellite/Adcs.hpp"

#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/kernel.h>

// Detumble (10 Hz thread) also reads magn0; a fetch interleaved with another thread's
// fetch/get of the same device reads back zeros.
K_MUTEX_DEFINE(magn_lock);

namespace {
// sensor indices in SensorError: 0 accel0, 1 accel1, 2 magn0, 3 magn1, 4.. sun ADC channel
const struct device* const sensors[4] = {
    DEVICE_DT_GET(DT_ALIAS(accel0)), DEVICE_DT_GET(DT_ALIAS(accel1)),
    DEVICE_DT_GET(DT_ALIAS(magn0)), DEVICE_DT_GET(DT_ALIAS(magn1))};

#define SUN_SPEC(node, prop, idx) ADC_DT_SPEC_GET_BY_IDX(node, idx),
const struct adc_dt_spec sun[] = {DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), io_channels, SUN_SPEC)};
static_assert(sizeof(sun) / sizeof(sun[0]) == Components::SunMv::SIZE, "six sun-sensor channels");
}  // namespace

namespace Components {

Adcs::Adcs(const char* compName) : AdcsComponentBase(compName) {}

void Adcs::run_handler(FwIndexType portNum, U32 context) {
    Vec3 v[4];
    for (U8 i = 0; i < 4; i++) {
        const enum sensor_channel chan = i < 2 ? SENSOR_CHAN_ACCEL_XYZ : SENSOR_CHAN_MAGN_XYZ;
        struct sensor_value xyz[3];
        int err = 0;
        for (U8 attempt = 0; attempt < 2; attempt++) {
            if (attempt) {
                // IST8310 takes 6 ms per conversion; a fetch that lands in Detumble's conversion returns -EIO.
                k_msleep(6);
            }
            k_mutex_lock(&magn_lock, K_FOREVER);
            err = sensor_sample_fetch(sensors[i]);
            if (!err) {
                err = sensor_channel_get(sensors[i], chan, xyz);
            }
            k_mutex_unlock(&magn_lock);
            if (!err) {
                break;
            }
        }
        if (err) {
            this->log_WARNING_HI_SensorError(i, err);
            continue;
        }
        v[i] = Vec3({sensor_value_to_float(&xyz[0]), sensor_value_to_float(&xyz[1]), sensor_value_to_float(&xyz[2])});
    }
    this->tlmWrite_accel0(v[0]);
    this->tlmWrite_accel1(v[1]);
    this->tlmWrite_magn0(v[2]);
    this->tlmWrite_magn1(v[3]);

    if (!m_adcReady) {
        for (const auto& s : sun) {
            const int err = adc_channel_setup_dt(&s);
            if (err) {
                this->log_WARNING_HI_SensorError(U8(4 + s.channel_id), err);
                return;
            }
        }
        m_adcReady = true;
    }
    SunMv mv;
    U8 brightest = 0;
    for (U8 i = 0; i < SunMv::SIZE; i++) {
        U16 raw = 0;
        struct adc_sequence seq = {.buffer = &raw, .buffer_size = sizeof(raw)};
        adc_sequence_init_dt(&sun[i], &seq);
        int err = adc_read_dt(&sun[i], &seq);
        int32_t val = raw;
        if (!err) {
            err = adc_raw_to_millivolts_dt(&sun[i], &val);
        }
        if (err) {
            this->log_WARNING_HI_SensorError(U8(4 + sun[i].channel_id), err);
            val = 0;
        }
        mv[i] = U16(val);
        if (mv[i] > mv[brightest]) {
            brightest = i;
        }
    }
    this->tlmWrite_sun_mV(mv);
    this->tlmWrite_brightest_panel(U8(brightest + 1));
}

}  // namespace Components
