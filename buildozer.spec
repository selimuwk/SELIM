[app]
title = Attendance Sync
package.name = attendancesync
package.domain = com.mohamedselim
source.dir = .
source.include_exts = py,kv,json,txt
version = 1.0.0
requirements = python3,kivy,requests,pyzk
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
android.api = 35
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
