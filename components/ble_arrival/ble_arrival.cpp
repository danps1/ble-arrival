#include "ble_arrival.h"
#include "esphome/core/log.h"
#include "esphome/core/hal.h"
#include <mbedtls/md.h>
#include <esp_gatts_api.h>
#include <esp_timer.h>

namespace esphome::ble_arrival {
static const char *const TAG = "ble_arrival";
using esp32_ble::ESPBTUUID;
using esp32_ble_server::BLECharacteristic;

void BLEArrival::set_device_id(const std::vector<uint8_t> &value) {
  if (value.size() != 16) return;
  identity_[0] = PROTOCOL_VERSION;
  std::copy(value.begin(), value.end(), identity_.begin() + 1);
  identity_[17] = 0; identity_[18] = 2; identity_[19] = 0;
  identity_valid_ = true;
}
void BLEArrival::set_secret_key(const std::vector<uint8_t> &value) {
  if (value.size() != key_.size()) return;
  std::copy(value.begin(), value.end(), key_.begin());
  key_valid_ = true;
}
void BLEArrival::clear_response_() {
  response_valid_ = false;
  if (response_ != nullptr) response_->set_value(std::vector<uint8_t>{});
}
void BLEArrival::setup() {
  if (server_ == nullptr || !key_valid_ || !identity_valid_) {
    mark_failed();
    return;
  }
  // One client owns the response buffer. Additional clients cannot race it.
  server_->set_max_clients(1);
  auto *service = server_->create_service(
      ESPBTUUID::from_raw("9aa8b570-27e5-45fb-86a1-4c9608431070"), true, 12);
  auto *identity = service->create_characteristic(
      "9aa8b571-27e5-45fb-86a1-4c9608431070", BLECharacteristic::PROPERTY_READ);
  identity->set_value(std::vector<uint8_t>(identity_.begin(), identity_.end()));
  auto *challenge = service->create_characteristic(
      "9aa8b572-27e5-45fb-86a1-4c9608431070", BLECharacteristic::PROPERTY_WRITE);
  response_ = service->create_characteristic(
      "9aa8b573-27e5-45fb-86a1-4c9608431070", BLECharacteristic::PROPERTY_READ);
  challenge->on_write([this](std::span<const uint8_t> data, uint16_t conn) { on_challenge_(data, conn); });
  server_->on_connect([this](uint16_t conn) {
    connected_ = true; connection_id_ = conn; connected_at_ = millis(); clear_response_();
  });
  server_->on_disconnect([this](uint16_t conn) {
    if (conn == connection_id_) { connected_ = false; clear_response_(); }
  });
  server_->enqueue_start_service(service);
}
void BLEArrival::on_challenge_(std::span<const uint8_t> request, uint16_t conn) {
  clear_response_();
  if (!connected_ || conn != connection_id_ || millis() - last_request_ < 200) return;
  std::array<uint8_t, MESSAGE_SIZE> message{};
  const uint64_t uptime_seconds = static_cast<uint64_t>(esp_timer_get_time()) / 1000000ULL;
  if (!build_message(request.data(), request.size(), identity_, uptime_seconds, message)) return;
  last_request_ = millis();
  std::vector<uint8_t> response(40);
  std::copy(message.end() - 8, message.end(), response.begin());
  const auto *md = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
  if (md == nullptr || mbedtls_md_hmac(md, key_.data(), key_.size(),
                                      message.data(), message.size(), response.data() + 8) != 0) return;
  response_->set_value(std::move(response));
  response_at_ = millis();
  response_valid_ = true;
}
void BLEArrival::loop() {
  if (response_valid_ && millis() - response_at_ >= 5000) clear_response_();
  if (connected_ && millis() - connected_at_ >= 10000) {
    esp_ble_gatts_close(server_->get_gatts_if(), connection_id_);
    connected_at_ = millis();
  }
}
void BLEArrival::dump_config() {
  ESP_LOGCONFIG(TAG, "BLE Arrival protocol 2; firmware 0.2.0; credential configured: %s",
                key_valid_ ? "yes" : "no");
}
}  // namespace esphome::ble_arrival
