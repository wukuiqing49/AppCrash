"""Build an isolated R8 consumer and inspect the resulting class names (no device use)."""

from __future__ import annotations

import json
import argparse
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile
import uuid


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "build/r8-verification"


def write(root: Path, path: str, value: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def groovy_path(path: Path) -> str:
    return "'" + path.as_posix().replace("'", "\\'") + "'"


def dex_classes(data: bytes) -> dict[str, str | None]:
    """Read class definitions, not arbitrary strings that may contain debug metadata."""
    if not data.startswith(b"dex\n"):
        raise AssertionError("Invalid DEX header")
    string_count, string_offset = struct.unpack_from("<II", data, 56)
    strings = []
    for index in range(string_count):
        offset = struct.unpack_from("<I", data, string_offset + index * 4)[0]
        while data[offset] & 0x80:
            offset += 1
        offset += 1
        end = data.index(b"\0", offset)
        strings.append(data[offset:end].decode("utf-8", errors="replace"))
    type_count, type_offset = struct.unpack_from("<II", data, 64)
    types = [strings[struct.unpack_from("<I", data, type_offset + i * 4)[0]]
             for i in range(type_count)]
    class_count, class_offset = struct.unpack_from("<II", data, 96)
    definitions = {}
    for i in range(class_count):
        offset = class_offset + i * 32
        descriptor = types[struct.unpack_from("<I", data, offset)[0]]
        source_index = struct.unpack_from("<I", data, offset + 16)[0]
        definitions[descriptor] = None if source_index == 0xFFFFFFFF else strings[source_index]
    return definitions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device-apk', action='store_true', help='Build a debug-signed, R8-enabled verification variant; never installs it.')
    args = parser.parse_args()
    variant = 'verification' if args.device_apk else 'release'
    package = 'verification.crash.r' + uuid.uuid4().hex[:12]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write(OUTPUT, "result.json", '{"status": "running"}\n')
    # 夹具不注册进实际模块图，也不创建可交付的演示功能。
    with tempfile.TemporaryDirectory(prefix="lib-crash-r8-") as directory:
        host = Path(directory)
        write(host, "settings.gradle", """
pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
    versionCatalogs { libs { from(files(CATALOG)) } }
}
rootProject.name = 'CrashR8Verification'
include ':app', ':lib_crash'
project(':lib_crash').projectDir = file(LIBRARY)
""".replace("CATALOG", groovy_path(ROOT / "gradle/libs.versions.toml"))
            .replace("LIBRARY", groovy_path(ROOT / "lib_crash")))
        write(host, "build.gradle", """
plugins {
    alias(libs.plugins.android.library) apply false
    alias(libs.plugins.kotlin.android) apply false
}
""")
        # app 与库共用已有版本目录，避免夹具另建技术版本基线。
        write(host, "app/build.gradle", """
apply plugin: 'com.android.application'
android {
    namespace 'verification.crash'
    compileSdk libs.versions.compileSdk.get().toInteger()
    defaultConfig {
        applicationId 'PACKAGE'
        minSdk libs.versions.minSdk.get().toInteger()
        targetSdk libs.versions.compileSdk.get().toInteger()
        versionCode 1
        versionName '1'
    }
    buildTypes {
        release {
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'host.pro'
        }
        verification {
            initWith release
            signingConfig signingConfigs.debug
            matchingFallbacks = ['release']
        }
    }
}
dependencies { implementation project(':lib_crash') }
""".replace('PACKAGE', package))
        shutil.copyfile(ROOT / "gradle/crash-obfuscation.pro", host / "app/host.pro")
        write(host, "app/src/main/AndroidManifest.xml", """
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:label="R8 verification">
        <activity android:name=".VerificationActivity" android:exported="true" />
    </application>
</manifest>
""")
        write(host, "app/src/main/java/verification/crash/VerificationActivity.java", """
package verification.crash;
import android.app.Activity;
import android.os.Bundle;
import com.wkq.crash.CrashThread;
import com.wkq.crash.CrashType;
import com.wkq.crash.CrashUtils;
import com.wkq.crash.NativeCrashType;
public final class VerificationActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        String selected = getIntent().getStringExtra("scenario");
        if (selected != null) {
            String runId = getIntent().getStringExtra("runId");
            String threadName = getIntent().getStringExtra("thread");
            CrashThread thread = threadName == null ? CrashThread.MAIN : CrashThread.valueOf(threadName);
            if (runId == null) runId = "r8-verification";
            if (getIntent().getBooleanExtra("native", false)) {
                CrashUtils.triggerNative(NativeCrashType.valueOf(selected), thread, runId);
            } else {
                CrashUtils.trigger(CrashType.valueOf(selected), thread, runId);
            }
        }
    }
}
""")
        write(host, "gradle.properties", "org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8\n")
        if (ROOT / "local.properties").exists():
            shutil.copyfile(ROOT / "local.properties", host / "local.properties")
        wrapper = ROOT / ("gradlew.bat" if os.name == "nt" else "gradlew")
        command = [str(wrapper), "-p", str(host), ":app:assemble" + variant.capitalize(),
                   ":lib_crash:assembleRelease", "--console=plain"]
        result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        write(OUTPUT, "build.log", result.stdout)
        if result.returncode:
            raise RuntimeError(f"Gradle failed ({result.returncode}); see {OUTPUT / 'build.log'}\n{result.stdout[-6000:]}")
        mapping_file = host / f"app/build/outputs/mapping/{variant}/mapping.txt"
        mapping_text = mapping_file.read_text(encoding="utf-8")
        mappings = dict(re.findall(r"^(com\.wkq\.crash\.[^ ]+) -> ([^ :]+):$", mapping_text, re.M))
        scenarios = sorted(path.stem for path in
                           (ROOT / "lib_crash/src/main/java/com/wkq/crash").glob("*Crash.kt")
                           if not path.stem.startswith('Native'))
        for name in scenarios:
            original = "com.wkq.crash." + name
            renamed = mappings.get(original)
            if not renamed or renamed.startswith("com.wkq.crash.") or name in renamed:
                raise AssertionError(f"Scenario was not renamed: {original} -> {renamed}")
            block = mapping_text.split(original + " -> ", 1)[1].split("\n", 1)[1]
            block = re.split(r"\n(?=[^\s#])", block, maxsplit=1)[0]
            methods = [line.rsplit(" -> ", 1)[-1].strip() for line in block.splitlines()
                       if "causeCrash" in line and " -> " in line]
            if not methods or any("causeCrash" in name for name in methods):
                raise AssertionError(f"Fault method was not renamed: {original}")
        apk_name = 'app-verification.apk' if args.device_apk else 'app-release-unsigned.apk'
        apk = host / f"app/build/outputs/apk/{variant}/{apk_name}"
        classes: dict[str, str | None] = {}
        with zipfile.ZipFile(apk) as archive:
            for name in archive.namelist():
                if re.fullmatch(r"classes\d*\.dex", name):
                    classes.update(dex_classes(archive.read(name)))
        bridge = 'Lcom/wkq/crash/NativeBridge;'
        retained = {name for name in classes if name.startswith('Lcom/wkq/crash/')}
        if not classes or retained != {bridge}:
            raise AssertionError(f"Only the JNI bridge may retain its name: {retained}")
        for name in scenarios:
            descriptor = "L" + mappings["com.wkq.crash." + name].replace(".", "/") + ";"
            if descriptor not in classes:
                raise AssertionError(f"Renamed scenario missing in DEX: {name}")
            if classes[descriptor] not in {None, "SourceFile"}:
                raise AssertionError(f"Original source filename remains: {name}: {classes[descriptor]}")
        aar = ROOT / "lib_crash/build/outputs/aar/lib_crash-release.aar"
        with zipfile.ZipFile(aar) as archive:
            if "allowobfuscation" not in archive.read("proguard.txt").decode("utf-8"):
                raise AssertionError("Consumer rules not bundled in AAR")
        shutil.copyfile(mapping_file, OUTPUT / "mapping.txt")
        output_apk = OUTPUT / ('verification-device.apk' if args.device_apk else 'verification-unsigned.apk')
        shutil.copyfile(apk, output_apk)
        summary = {"status": "passed", "scenarioCount": len(scenarios), "renamedScenariosPresentInDex": True,
                   "faultMethodsRenamed": True, "originalSourceFileNamesAbsent": True,
                   "originalScenarioClassDescriptorsAbsent": True, "retainedJniBridge": bridge,
                   "consumerRulesBundled": True, "applicationId": package,
                   "apk": output_apk.relative_to(ROOT).as_posix(), "variant": variant,
                   "deviceTestExecuted": False, "classMappings": mappings}
        write(OUTPUT, "result.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        print(f"R8 verification passed: {len(scenarios)} renamed scenarios present in DEX; evidence: {OUTPUT}")


if __name__ == "__main__":
    main()
