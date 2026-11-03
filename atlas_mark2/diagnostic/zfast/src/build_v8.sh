#!/bin/sh
# build_v8.sh SRCDIR VERSION : PREDICTIONS_M13.  Exactly build_v7.sh (which calls build_v6.sh: the same flag set
# -O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math, snapshot bin/src_VERSION, CLIs, libzfast.VERSION.dylib and the separate
# -DZF_TEST_HOOKS libzfast.VERSION_testhooks.dylib, SHA256.VERSION), then records the toolchain and library environment of the build
# in bin/BUILD_ENV.VERSION.txt.  build_v6.sh / build_v7.sh are not modified.  Never overwrites.
set -e
SD=${1:?srcdir}; V=${2:?version}
cd "$(dirname "$0")"
[ -e ../bin/BUILD_ENV.$V.txt ] && { echo "exists ../bin/BUILD_ENV.$V.txt"; exit 1; }
sh ./build_v7.sh "$SD" "$V"
{ echo "build_v8.sh $SD $V  $(date)"; cc --version | head -1; sw_vers | tr '\n' ' '; echo; sysctl -n kern.osversion hw.model
  shasum -a 256 build_v6.sh build_v7.sh build_v8.sh; otool -L ../bin/libzfast.$V.dylib; } > ../bin/BUILD_ENV.$V.txt
echo built_v8 $V
