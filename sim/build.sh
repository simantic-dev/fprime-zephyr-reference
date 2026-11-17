#!/bin/sh
# Rebuild sim/fprime-demo.elf and sim/dictionary.json from this checkout: the F'
# reference deployment plus Components/Satellite for the nucleo_h723zg Zephyr board
# (boards/nucleo_h723zg.overlay + .conf). ../demo does not need this; the outputs are committed.
#
# Needs: Zephyr SDK 0.17.0 (ZEPHYR_SDK_INSTALL_DIR), python3.12, git, cmake, ninja.
# env:   VENV  python venv for the F' and Zephyr tooling (default ../fprime-venv, git-ignored)
#        JOBS  parallel build jobs (default 4)
set -eu

ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
VENV=${VENV:-$ROOT/fprime-venv}
: "${ZEPHYR_SDK_INSTALL_DIR:?set ZEPHYR_SDK_INSTALL_DIR to a Zephyr SDK 0.17.0 install}"
export ZEPHYR_SDK_INSTALL_DIR
cd "$ROOT"

git submodule update --init --depth 1
[ -d "$VENV" ] || python3.12 -m venv "$VENV"
. "$VENV/bin/activate"
pip install -q -r requirements.txt
# Only the west modules this board needs (hal_st: the ST MEMS drivers under lis2dw12).
( cd lib/zephyr-workspace && west update hal_stm32 hal_st cmsis cmsis_6 picolibc && west zephyr-export )

fprime-util purge -f >/dev/null 2>&1 || true
fprime-util generate -DBOARD=nucleo_h723zg
fprime-util build -j "${JOBS:-4}"

# Debug info is dropped: it holds the build machine's paths, and sim needs only code and symbols.
"$ZEPHYR_SDK_INSTALL_DIR/arm-zephyr-eabi/bin/arm-zephyr-eabi-strip" --strip-debug \
  -o sim/fprime-demo.elf "$(find build-fprime-automatic-zephyr -name zephyr.elf | head -1)"
cp "$(find build-artifacts -name ReferenceDeploymentTopologyDictionary.json | head -1)" sim/dictionary.json
echo "built sim/fprime-demo.elf and sim/dictionary.json"
