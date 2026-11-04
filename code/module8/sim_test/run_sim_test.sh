#!/bin/sh
# Compile the real sketch against a fake Arduino and run the safety tests (macOS clang).
# Build products go to a temporary folder. Usage: sh code/module8/sim_test/run_sim_test.sh
here=$(cd "$(dirname "$0")" && pwd)
out=$(mktemp -d)
sdk=$(xcrun --show-sdk-path)
sed -e 's/isfinite/std::isfinite/g' -e 's/#include <Arduino.h>/#include "Arduino.h"/' \
    "$here/../module_08_angstrom_controller/module_08_angstrom_controller.ino" > "$out/sketch.cpp"
clang++ -std=c++17 -nostdinc++ -isystem "$sdk/usr/include/c++/v1" -isysroot "$sdk" \
    -I"$here" -I"$out" -Wno-everything -o "$out/simtest" "$here/test.cpp" && "$out/simtest"
