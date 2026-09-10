"""ESP-IDF Bluetooth credential component."""

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import esp32_ble_server
from esphome.const import CONF_ID

AUTO_LOAD = ["esp32_ble_server"]
DEPENDENCIES = ["esp32"]
CONFLICTS_WITH = ["esp32_ble_beacon"]
ns = cg.esphome_ns.namespace("ble_arrival")
BLEArrival = ns.class_("BLEArrival", cg.Component)


def hex_bytes(length):
    def validate(value):
        value = cv.string_strict(value)
        if len(value) != length * 2 or any(c not in "0123456789abcdefABCDEF" for c in value):
            raise cv.Invalid(f"Expected exactly {length * 2} hexadecimal characters")
        if length == 32 and len(set(bytes.fromhex(value))) < 8:
            raise cv.Invalid("Use a randomly generated key, not a placeholder")
        return value.lower()

    return validate


CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(BLEArrival),
            cv.GenerateID("ble_server_id"): cv.use_id(esp32_ble_server.BLEServer),
            cv.Required("device_id"): hex_bytes(16),
            cv.Required("secret_key"): hex_bytes(32),
        }
    ).extend(cv.COMPONENT_SCHEMA),
    cv.only_with_framework("esp-idf"),
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    server = await cg.get_variable(config["ble_server_id"])
    cg.add(var.set_server(server))
    cg.add(var.set_device_id(list(bytes.fromhex(config["device_id"]))))
    cg.add(var.set_secret_key(list(bytes.fromhex(config["secret_key"]))))
