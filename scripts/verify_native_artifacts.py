"""Check packaged native ABIs, 16 KB ELF/APK alignment and public exports."""
from pathlib import Path
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def verify_apk(apk, libraries):
    expected = {name.replace('jni/', 'lib/', 1): data for name, data in libraries.items()}
    with zipfile.ZipFile(apk) as archive:
        entries = [info for info in archive.infolist() if info.filename.endswith('.so')]
        if len(entries) != len(expected) or {info.filename for info in entries} != set(expected):
            raise AssertionError(f'Unexpected APK native libraries: {[info.filename for info in entries]}')
        apk_data = apk.read_bytes()
        for info in entries:
            if archive.read(info) != expected[info.filename]:
                raise AssertionError(f'APK/AAR library mismatch: {info.filename}')
            if info.compress_type != zipfile.ZIP_STORED:
                raise AssertionError(f'Expected uncompressed native library: {info.filename}')
            name_size, extra_size = struct.unpack_from('<HH', apk_data, info.header_offset + 26)
            data_offset = info.header_offset + 30 + name_size + extra_size
            if data_offset % 16384:
                raise AssertionError(f'APK entry is not 16 KB aligned: {info.filename}')


def main():
    versions = (ROOT / 'gradle/libs.versions.toml').read_text(encoding='utf-8')
    ndk = re.search(r'^ndk = "([^"]+)"', versions, re.M).group(1)
    sdk_value = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    sdk = Path(sdk_value) if sdk_value else Path(shutil.which('adb')).resolve().parent.parent
    host = 'windows-x86_64' if os.name == 'nt' else 'linux-x86_64'
    readelf = sdk / f'ndk/{ndk}/toolchains/llvm/prebuilt/{host}/bin/llvm-readelf'
    if os.name == 'nt':
        readelf = readelf.with_suffix('.exe')
    output = ROOT / 'build/native-artifacts'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'result.json').write_text('{"status":"running"}', encoding='utf-8')
    result = {}
    libraries = {}
    with tempfile.TemporaryDirectory(prefix='lib-crash-elf-') as temp:
        with zipfile.ZipFile(ROOT / 'lib_crash/build/outputs/aar/lib_crash-release.aar') as aar:
            libs = [name for name in aar.namelist() if name.endswith('.so')]
            expected = {f'jni/{abi}/libcrash_native.so' for abi in ('armeabi-v7a', 'arm64-v8a', 'x86_64')}
            if set(libs) != expected:
                raise AssertionError(f'Unexpected native libraries: {libs}')
            for name in libs:
                data = aar.read(name)
                libraries[name] = data
                is64 = data[4] == 2
                phoff = struct.unpack_from('<Q' if is64 else '<I', data, 32 if is64 else 28)[0]
                entsize, count = struct.unpack_from('<HH', data, 54 if is64 else 42)
                alignments = []
                for i in range(count):
                    offset = phoff + i * entsize
                    if struct.unpack_from('<I', data, offset)[0] == 1:
                        alignments.append(struct.unpack_from('<Q' if is64 else '<I', data,
                                                             offset + (48 if is64 else 28))[0])
                if not alignments or any(value < 16384 for value in alignments):
                    raise AssertionError(f'{name}: incompatible ELF alignment {alignments}')
                library = Path(temp) / name.replace('/', '_')
                library.write_bytes(data)
                symbols = subprocess.check_output([str(readelf), '--dyn-syms', '--wide', str(library)], text=True)
                exports = []
                for line in symbols.splitlines():
                    fields = line.split()
                    if len(fields) >= 8 and fields[0].endswith(':') and fields[4] in {'GLOBAL', 'WEAK'} and fields[6] != 'UND':
                        exports.append(fields[7])
                if set(exports) != {'JNI_OnLoad'}:
                    raise AssertionError(f'{name}: unexpected exports {exports}')
                result[name] = {'loadAlignments': alignments, 'exports': exports, 'size': len(data)}
    fixture = json.loads((ROOT / 'build/r8-verification/result.json').read_text(encoding='utf-8'))
    if fixture.get('status') != 'passed':
        raise AssertionError('R8 fixture verification has not passed')
    apk = ROOT / fixture['apk']
    # AGP 应按 16 KB 对齐 ZIP 中未压缩的 so，独立于 ELF 内部对齐。
    verify_apk(apk, libraries)
    summary = {'status': 'passed', 'libraries': result, 'apk16KbAligned': True,
               'apkMatchesAar': True}
    (output / 'result.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print('Native artifact verification passed: 3 ABIs, 16 KB ELF/APK alignment, JNI_OnLoad-only exports')


if __name__ == '__main__':
    main()
