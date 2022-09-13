#!/bin/sh

# package name, e.g. com.example.helloandroid expected as first arguemtn
# ./pull.sh com.example.helloandroid
# apktool expected on $PATH env var

adb shell pm path $1 | awk -F: '{print $2}' | xargs -L1 adb pull

ALL_APKS=$(ls -1 *.apk)
SPLIT_CONFIG_APKS=$(ls -1 split_config*.apk | sed -e 's/\.apk//g')

for apk in ${ALL_APKS}; do
    echo "Decompiling ${apk}";
    apktool d -f ${apk};
done
