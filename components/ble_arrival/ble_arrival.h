#pragma once
#include "esphome/core/component.h"
#include "esphome/components/esp32_ble_server/ble_server.h"
#include "protocol.h"

namespace esphome::ble_arrival {
class BLEArrival : public Component {
 public:
  void set_server(esp32_ble_server::BLEServer *server) { server_ = server; }
  void set_device_id(const std::vector<uint8_t> &value);
  void set_secret_key(const std::vector<uint8_t> &value);
  void setup() override;
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::BLUETOOTH + 1; }
 protected:
  esp32_ble_server::BLEServer *server_{nullptr};
  esp32_ble_server::BLECharacteristic *response_{nullptr};
  std::array<uint8_t, 32> key_{};
  std::array<uint8_t, IDENTITY_SIZE> identity_{};
  bool key_valid_{false};
  bool identity_valid_{false};
  bool response_valid_{false};
  uint32_t last_request_{0};
  uint32_t connected_at_{0};
  uint32_t response_at_{0};
  uint16_t connection_id_{0};
  bool connected_{false};
  void clear_response_();
  void on_challenge_(std::span<const uint8_t> request, uint16_t connection_id);
};
}  // namespace esphome::ble_arrival
