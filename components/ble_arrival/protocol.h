#pragma once
#include <array>
#include <algorithm>
#include <cstddef>
#include <cstdint>

namespace esphome::ble_arrival {
inline constexpr uint8_t PROTOCOL_VERSION = 2;
inline constexpr char AUTH_CONTEXT[] = "BLE-ARRIVAL-AUTH";
inline constexpr size_t IDENTITY_SIZE = 20;
inline constexpr size_t NONCE_SIZE = 16;
inline constexpr size_t REQUEST_SIZE = 17;
inline constexpr size_t MESSAGE_SIZE = sizeof(AUTH_CONTEXT) + IDENTITY_SIZE + NONCE_SIZE + 8;

inline bool build_message(const uint8_t *request, size_t size,
                          const std::array<uint8_t, IDENTITY_SIZE> &identity,
                          uint64_t uptime_seconds,
                          std::array<uint8_t, MESSAGE_SIZE> &message) {
  if (size != REQUEST_SIZE || request[0] != PROTOCOL_VERSION) return false;
  std::copy_n(reinterpret_cast<const uint8_t *>(AUTH_CONTEXT), sizeof(AUTH_CONTEXT), message.begin());
  std::copy(identity.begin(), identity.end(), message.begin() + sizeof(AUTH_CONTEXT));
  std::copy_n(request + 1, NONCE_SIZE, message.begin() + sizeof(AUTH_CONTEXT) + IDENTITY_SIZE);
  for (size_t i = 0; i < 8; ++i) message[MESSAGE_SIZE - 8 + i] = (uptime_seconds >> (8 * i)) & 0xff;
  return true;
}
}  // namespace esphome::ble_arrival
