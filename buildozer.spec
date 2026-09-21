[app]
title = RICHARD Electronica OT
package.name = richardot
package.domain = org.richardelectronica

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0

requirements = python3,kivy,reportlab,plyer,pillow

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/logo.png


android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
