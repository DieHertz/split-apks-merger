#!/usr/bin/env python3

import glob
import os
import pathlib
import re
import shutil
import xmltodict


# TODO(hertz@): abstract these out, use a glob or something like that
APK_DIRS = (
    'base',
    'split_config.en',
    'split_config.xxhdpi',
    'split_config.arm64_v8a',
)


# for some reason these files seem to be redundant, maybe it's apktool's fault they are created?
BLACKLIST = [
    'base/res/values-xhdpi/drawables.xml',
    'base/res/values-hdpi/styles.xml'
]


dry_run = False


def filter_out_dirs(files):
    return [path for path in files if not os.path.isdir(path)]


def load_all_public():
    result = {}

    for apk in APK_DIRS:
        public_filename = f'{apk}/res/values/public.xml'
        if not os.path.exists(public_filename):
            continue

        with open(public_filename) as f:
            result[apk] = xmltodict.parse(f.read())['resources']['public']

    return result


def is_dummy(name):
    return 'APKTOOL_DUMMY_' in name


def get_dummies(public):
    return [
        item for item in public if is_dummy(item['@name'])
    ]


def get_all_dummies(publics):
    return {
        apk: get_dummies(public) for apk, public in publics.items()
    }


def get_apk_contents():
    return {
        apk: filter_out_dirs(glob.glob(f'{apk}/**/*', recursive=True))
        for apk in APK_DIRS
    }


def collect_all_ids(publics):
    id_to_name = {}

    for apk, public in publics.items():
        for item in public:
            name = item['@name']
            if not is_dummy(name):
                id_to_name[item['@id']] = name

    return id_to_name


def get_mappings(dummies, all_ids):
    dummy_res_to_name = {apk: {} for apk, _ in dummies.items()}
    unresolved = False

    for apk, dummy in dummies.items():
        for item in dummy:
            res_id = item['@id']
            res_name = item['@name']
            res_type = item['@type']

            if res_id in all_ids:
                dummy_res_to_name[apk][(res_type, res_name)] = all_ids[res_id]
            else:
                unresolved = True
                print(f'Could not resolve {apk}/@{res_type}/{res_name} = {res_id}')

    if unresolved:
        raise Exception('Could not resolve some resources')

    return dummy_res_to_name


def get_rules_from_mappings(mappings):
    rules = []

    def first_pattern(res_type, res_name):
        return f'type="{res_type}" name="{res_name}"'

    def second_pattern(res_type, res_name):
        return f'"@{res_type}/{res_name}"'

    def third_pattern(res_type, res_name):
        return f'>@{res_type}/{res_name}<'

    for (res_type, res_name), resolved_res_name in mappings.items():
        for pattern in (first_pattern, second_pattern, third_pattern):
            rules.append((pattern(res_type, res_name), pattern(res_type, resolved_res_name)))

    return rules


def patch_xmls(mappings):
    for apk, mapping in mappings.items():
        rules = get_rules_from_mappings(mapping)
        for filename in glob.glob(f'{apk}/res/**/*.xml', recursive=True):
            patch_xml(filename, rules)


def patch_xml(filename, rules):
    with open(filename) as f:
        xml = f.read()

    if not is_dummy(xml):
        return

    print(f'Patching {filename}')

    for rule in rules:
        xml = xml.replace(*rule)

    if is_dummy(xml):
        print(f'Could not fully patch {filename}')

    if dry_run:
        return

    with open(filename, 'w') as f:
        f.write(xml)


def merge_directories():
    apk_contents = get_apk_contents()
    base_files = apk_contents['base']

    for apk, files in apk_contents.items():
        if apk == 'base':
            continue

        for from_file in files:
            to_file = pathlib.Path('base', *pathlib.Path(from_file).parts[1:])

            if str(to_file) in BLACKLIST:
                print(f'File {to_file} is blacklisted')
                continue

            if str(to_file) not in base_files:
                directory_name = os.path.dirname(to_file)
                if not os.path.exists(directory_name):
                    print(f'Creating {directory_name}')
                    if not dry_run:
                        os.makedirs(directory_name)
                print(f'Copying {from_file} to {to_file}')
                if not dry_run:
                    shutil.copy2(from_file, to_file)


def main():
    publics = load_all_public()
    dummies = get_all_dummies(publics)

    if not any(bool(dummy) for dummy in dummies.values()):
        print('Nothing to patch')
        return

    all_ids = collect_all_ids(publics)
    mappings = get_mappings(dummies, all_ids)

    # TODO(hertz@): copy everything to tmp dir, then move back
    patch_xmls(mappings)

    # copy all files without overwrites
    merge_directories()


if __name__ == '__main__':
    main()
