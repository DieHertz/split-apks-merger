This script is an attempt at compiling split APKs decompiled using `apktool` into a single base.apk which contains all of the necessary resources, with APKTOOL_DUMMY_ids resolved to actual resource names.

**Installation**

I'm using python3.8, you may try any version of python3 if it contains necessary packages.
```
git clone https://github.com/DieHertz/split-apks-merger.git
cd split-apks-merger
python3 -m pip install -r requirements.txt
```

**Usage**
A bash script called `pull.sh` is provided to pull split APK files from your device and unpack them, e.g.:
```
./pull.sh com.example.helloandroid
```

Then invoke `merge_split_apks.py` in a directory which contains unpacked `base` and `split_config.*` directories coming out of `apktool`
You still need to go into `base/AndroidManifest.xml` and take care of `splitsRequired`, as well as `extractNativeLibraries` in some cases.