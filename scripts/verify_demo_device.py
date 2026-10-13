"""Exercise the demo controls and one fatal fault per process on an explicitly selected device."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET

from verify_native_device import matches_failure

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ['RUNTIME_EXCEPTION', 'NULL_POINTER', 'ARRAY_INDEX_OUT_OF_BOUNDS',
             'LIST_INDEX_OUT_OF_BOUNDS', 'STRING_INDEX_OUT_OF_BOUNDS', 'CLASS_CAST',
             'INTEGER_DIVISION_BY_ZERO', 'NUMBER_FORMAT', 'ILLEGAL_ARGUMENT',
             'ILLEGAL_STATE', 'UNINITIALIZED_PROPERTY', 'ABORT', 'SEGMENTATION_FAULT']
JAVA_CLASSES = ['RuntimeExceptionCrash', 'NullPointerCrash', 'ArrayIndexOutOfBoundsCrash',
                'ListIndexOutOfBoundsCrash', 'StringIndexOutOfBoundsCrash', 'ClassCastCrash',
                'ArithmeticCrash', 'NumberFormatCrash', 'IllegalArgumentCrash',
                'IllegalStateCrash', 'UninitializedPropertyCrash']
JAVA_ERRORS = ['java.lang.RuntimeException', 'java.lang.NullPointerException',
               'java.lang.ArrayIndexOutOfBoundsException',
               'java.lang.(?:IndexOutOfBoundsException|ArrayIndexOutOfBoundsException)',
               'java.lang.(?:IndexOutOfBoundsException|StringIndexOutOfBoundsException)',
               'java.lang.ClassCastException', 'java.lang.ArithmeticException',
               'java.lang.NumberFormatException', 'java.lang.IllegalArgumentException',
               'java.lang.IllegalStateException', 'kotlin.UninitializedPropertyAccessException']
SIGNALS = ['SIGABRT', 'SIGSEGV', 'SIGSEGV', 'SIGABRT', 'SIGABRT', 'SIGABRT',
           'SIGFPE', 'SIGABRT', 'SIGABRT', 'SIGABRT', 'SIGABRT', 'SIGABRT', 'SIGSEGV']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--ui-only', action='store_true', help='Run nonfatal control and landscape checks only')
    args = parser.parse_args()
    run = uuid.uuid4().hex[:12]
    package = 'verification.crash.demo.r' + run
    remote_xml = '/sdcard/crash-demo-' + run + '.xml'
    output = ROOT / 'build/demo-device' / run
    output.mkdir(parents=True)
    result = {'status': 'running', 'applicationId': package, 'checks': [], 'cases': [],
              'scope': 'Debug demo UI and fault/process behavior; no collection SDK'}

    def save():
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')

    def adb(*command, check=True, binary=False):
        proc = subprocess.run(['adb', '-s', args.serial, *command], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=30)
        if check and proc.returncode:
            raise RuntimeError(proc.stderr.decode('utf-8', errors='replace'))
        return proc.stdout if binary else proc.stdout.decode('utf-8', errors='replace').strip()

    def nodes():
        adb('shell', 'uiautomator', 'dump', remote_xml)
        hierarchy = adb('shell', 'cat', remote_xml)
        (output / 'last-ui.xml').write_text(hierarchy, encoding='utf-8')
        return ET.fromstring(hierarchy)

    def find(tree, resource):
        return next((node for node in tree.iter('node') if node.get('resource-id') == resource), None)

    def tap_node(node):
        bounds = list(map(int, re.findall(r'\d+', node.get('bounds', ''))))
        if len(bounds) != 4 or bounds[3] <= bounds[1]:
            raise AssertionError('Control has no visible bounds')
        adb('shell', 'input', 'tap', str((bounds[0] + bounds[2]) // 2), str((bounds[1] + bounds[3]) // 2))

    def tap(resource, scroll=False):
        for _ in range(5):
            tree = nodes()
            node = find(tree, resource)
            if node is not None and node.get('enabled') == 'true':
                bounds = list(map(int, re.findall(r'\d+', node.get('bounds', ''))))
                if len(bounds) == 4 and bounds[3] > bounds[1]:
                    tap_node(node)
                    return
            if scroll:
                screen = list(map(int, re.findall(r'\d+', list(tree)[0].get('bounds'))))
                adb('shell', 'input', 'swipe', str(screen[2] // 2), str(screen[3] * 3 // 4),
                    str(screen[2] // 2), str(screen[3] // 3), '250')
            time.sleep(0.2)
        raise AssertionError('Control not found: ' + resource)

    def launch(mode='java', scenario='RUNTIME_EXCEPTION', thread='MAIN', run_id='ui-smoke'):
        adb('shell', 'am', 'force-stop', package)
        adb('shell', 'am', 'start', '-W', '-n', package + '/com.wkq.crash.demo.CrashTestActivity',
            '--es', 'mode', mode, '--es', 'scenario', scenario, '--es', 'thread', thread,
            '--es', 'runId', run_id)

    def screenshot(name):
        (output / name).write_bytes(adb('exec-out', 'screencap', '-p', binary=True))

    installed = False
    save()
    try:
        result.update({'api': adb('shell', 'getprop', 'ro.build.version.sdk'),
                       'abi': adb('shell', 'getprop', 'ro.product.cpu.abi'),
                       'pageSize': adb('shell', 'getconf', 'PAGE_SIZE')})
        if 'package:' in adb('shell', 'pm', 'path', package, check=False):
            raise RuntimeError('Refusing to overwrite an installed package')
        wrapper = ROOT / ('gradlew.bat' if os.name == 'nt' else 'gradlew')
        command = [str(wrapper), '--no-daemon', ':demo:assembleDebug', '-PdemoApplicationId=' + package]
        if os.name != 'nt':
            command.insert(0, 'bash')
        build = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               encoding='utf-8', errors='replace', timeout=600)
        (output / 'build.log').write_text(build.stdout, encoding='utf-8')
        if build.returncode:
            raise RuntimeError('Demo build failed; see build.log')
        apk = output / 'demo-debug.apk'
        shutil.copy2(ROOT / 'demo/build/outputs/apk/debug/demo-debug.apk', apk)
        result['apkSha256'] = hashlib.sha256(apk.read_bytes()).hexdigest()
        if 'Success' not in adb('install', str(apk)):
            raise RuntimeError('Demo installation failed')
        installed = True
        launch()
        tree = nodes()
        assert find(tree, package + ':id/mode_java').get('checked') == 'true'
        assert adb('shell', 'pidof', package, check=False), 'Startup unexpectedly crashed'
        screenshot('page-java.png')
        tap(package + ':id/mode_native')
        assert find(nodes(), package + ':id/mode_native').get('checked') == 'true'
        tap(package + ':id/thread_background')
        assert find(nodes(), package + ':id/thread_background').get('checked') == 'true'
        tap(package + ':id/scenario')
        labels = ET.parse(ROOT / 'demo/src/main/res/values/strings.xml').find("string-array[@name='scenario_names']")
        selected = next(node for node in nodes().iter('node') if node.get('text') == labels[2].text)
        tap_node(selected)
        assert 'native-array-index-out-of-bounds' in find(nodes(), package + ':id/scenario_details').get('text')
        if args.ui_only:
            tap(package + ':id/run_id', scroll=True)
            adb('shell', 'input', 'keyevent', 'KEYCODE_MOVE_END')
            adb('shell', 'input', 'text', '_edited')
            screenshot('page-keyboard.png')
            adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
            assert find(nodes(), package + ':id/run_id').get('text') == 'ui-smoke_edited'
            result['checks'].append({'id': 'editable-run-id-keyboard', 'status': 'passed'})
        screenshot('page-native.png')
        # 对话框取消必须保留进程，不能产生测试记录。
        tap(package + ':id/trigger', scroll=True)
        screenshot('confirmation.png')
        tap('android:id/button2')
        assert adb('shell', 'pidof', package, check=False)
        preferences = adb('shell', 'run-as', package, 'cat', 'shared_prefs/crash_test.xml', check=False)
        assert 'ui-smoke' not in preferences
        result['checks'].append({'id': 'startup-mode-scenario-thread-cancel', 'status': 'passed'})
        save()
        for mode, count in (() if args.ui_only else (('java', 11), ('native', 13))):
            for index, scenario in enumerate(SCENARIOS[:count]):
                for thread in ('MAIN', 'BACKGROUND'):
                    run_id = 'demo-' + uuid.uuid4().hex
                    case_id = mode + '-' + scenario.lower() + '-' + thread.lower()
                    record = {'id': case_id, 'runId': run_id, 'status': 'running'}
                    result['cases'].append(record)
                    save()
                    launch(mode, scenario, thread, run_id)
                    tree = nodes()
                    assert find(tree, package + ':id/mode_' + mode).get('checked') == 'true'
                    assert find(tree, package + ':id/thread_' + ('main' if thread == 'MAIN' else 'background')).get('checked') == 'true'
                    details = find(tree, package + ':id/scenario_details').get('text')
                    record['scenarioDetails'] = details
                    pid = adb('shell', 'pidof', package).split()[0]
                    tap(package + ':id/trigger', scroll=True)
                    tap('android:id/button1')
                    start = time.monotonic()
                    passed = False
                    log = ''
                    while time.monotonic() - start < 18:
                        log = adb('logcat', '-d', '-v', 'threadtime', '--pid', pid)
                        exited = not adb('shell', 'pidof', package, check=False)
                        if mode == 'native':
                            evidence = matches_failure(log, index + 1, SIGNALS[index], thread, run_id)
                        else:
                            thread_name = 'main' if thread == 'MAIN' else 'lib_crash-'
                            evidence = (run_id in log and re.search(JAVA_ERRORS[index] + r'(?=:|\s|$)', log)
                                        and ('FATAL EXCEPTION: ' + thread_name) in log
                                        and ('com.wkq.crash.' + JAVA_CLASSES[index] + '.causeCrash') in log)
                        if evidence and exited:
                            passed = True
                            break
                        time.sleep(0.3)
                    (output / (case_id + '.log')).write_text(log, encoding='utf-8')
                    assert passed, 'Missing crash evidence: ' + case_id
                    preferences = ET.fromstring(adb('shell', 'run-as', package, 'cat', 'shared_prefs/crash_test.xml'))
                    assert next(n.text for n in preferences if n.get('name') == 'runId') == run_id
                    assert next(n.text for n in preferences if n.get('name') == 'scenarioId') in log
                    record.update({'status': 'passed', 'durationSeconds': round(time.monotonic() - start, 2),
                                   'evidence': case_id + '.log'})
                    save()
                    print(case_id + ': PASS', flush=True)
        if result['cases']:
            # 最后一次故障后重启页面，读取持久化记录。
            adb('shell', 'am', 'start', '-W', '-n', package + '/com.wkq.crash.demo.CrashTestActivity')
            tap(package + ':id/trigger', scroll=True)
            tap('android:id/button2')
            tree = nodes()
            assert run_id in find(tree, package + ':id/last_run').get('text')
            screenshot('last-run.png')
            result['checks'].append({'id': 'restart-last-run', 'status': 'passed'})
        if args.ui_only:
            adb('shell', 'am', 'force-stop', package)
            adb('shell', 'am', 'start', '-W', '-n', package + '/com.wkq.crash.demo.CrashTestActivity',
                '--es', 'orientation', 'landscape', '--es', 'mode', 'native',
                '--es', 'scenario', 'UNINITIALIZED_PROPERTY')
            tap(package + ':id/trigger', scroll=True)
            tap('android:id/button2')
            screenshot('page-landscape.png')
            assert adb('shell', 'pidof', package, check=False)
            result['checks'].append({'id': 'landscape-scroll-cancel', 'status': 'passed'})
        result['status'] = 'passed'
    except Exception as error:
        result.update({'status': 'failed', 'error': str(error)})
        if installed:
            try:
                screenshot('failure.png')
            except (RuntimeError, subprocess.TimeoutExpired):
                pass
        raise
    finally:
        if installed:
            result['fixtureRemoved'] = 'Success' in adb('uninstall', package, check=False)
        adb('shell', 'rm', '-f', remote_xml, check=False)
        save()
    print(f'Demo device verification passed: {len(result["cases"])} crashes; {output}')


if __name__ == '__main__':
    main()
