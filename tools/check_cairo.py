# scripts/check_cairo.py
import platform, sys, ctypes

if platform.system() == "Darwin" and platform.machine() == "arm64":
    ctypes.CDLL("/opt/homebrew/lib/libcairo.2.dylib")
    print("cairo ok (arm64) with", sys.version)
else:
    print("skip cairo check, platform=", platform.system(), platform.machine())