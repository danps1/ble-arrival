import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cpp_and_python_build_identical_signed_message(tmp_path):
    executable = tmp_path / "protocol-test"
    subprocess.run(
        [
            "c++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I" + str(ROOT / "components/ble_arrival"),
            str(ROOT / "tests/firmware/protocol_test.cpp"),
            "-o",
            str(executable),
        ],
        check=True,
    )
    result = subprocess.check_output([str(executable)], text=True).strip()
    vector = json.loads((ROOT / "tests/vectors/auth_v2.json").read_text())
    assert result == vector["message"]
