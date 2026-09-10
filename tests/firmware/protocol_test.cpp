#include "protocol.h"
#include <cassert>
#include <cstdio>
using namespace esphome::ble_arrival;
int main() {
  std::array<uint8_t, IDENTITY_SIZE> identity{};
  identity[0] = 1;
  for (int i = 0; i < 16; i++) identity[i+1] = i;
  identity[18] = 1;
  uint8_t request[17] = {1};
  for (int i = 0; i < 16; i++) request[i+1] = i+16;
  std::array<uint8_t, MESSAGE_SIZE> message{};
  assert(!build_message(request, 0, identity, message));
  assert(!build_message(request, 16, identity, message));
  assert(!build_message(request, 18, identity, message));
  request[0] = 2;
  assert(!build_message(request, 17, identity, message));
  request[0] = 1;
  assert(build_message(request, 17, identity, message));
  for (auto b : message) std::printf("%02x", b);
  std::printf("\n");
}
