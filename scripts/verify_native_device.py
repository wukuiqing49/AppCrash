"""Run one native fault per process in the isolated R8 fixture, with explicit device selection."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]

# 类型和诊断信息同时核对，区分同为 SIGABRT 的场景。
CPP_FAILURES = {
    1: ('std::runtime_error', 'Intentional native runtime exception'),
    4: ('std::out_of_range', 'vector'),
    5: ('std::out_of_range', 'basic_string'),
    6: ('std::bad_cast', None),
    8: ('std::invalid_argument', 'stoi'),
    9: ('std::invalid_argument', 'Intentional negative argument'),
    10: ('std::logic_error', 'Intentional invalid state'),
    11: ('std::bad_optional_access', None),
}


def matches_failure(log, code, expected_signal, thread, run_id):
    marker = next((line for line in log.splitlines() if f'runId={run_id} ' in line), '')
    expected_thread = 'thread=main' if thread == 'MAIN' else 'thread=lib_crash-native-'
    entered = re.search(r'native-entry code=' + str(code) + r'(?:\s|$)', log)
    signal = re.search(r'Fatal signal \d+ \(' + re.escape(expected_signal) + r'\)', log)
    failure = re.search(r'uncaught exception of type ([\w:]+)(?:: (.*))?$', log, re.M)
    if code in CPP_FAILURES:
        exception, message = CPP_FAILURES[code]
        mechanism = bool(failure and failure.group(1) == exception
                         and (message is None or message in (failure.group(2) or '')))
    else:
        mechanism = failure is None
    return bool(marker and expected_thread in marker and entered and signal and mechanism)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    args = parser.parse_args()
    fixture = json.loads((ROOT / 'build/r8-verification/result.json').read_text(encoding='utf-8'))
    if fixture.get('status') != 'passed' or fixture.get('variant') != 'verification':
        raise RuntimeError('First run verify_r8.py --device-apk')
    package = fixture['applicationId']
    if not re.fullmatch(r'verification\.crash\.r[0-9a-f]{12}', package):
        raise RuntimeError('Refusing to use a non-fixture package')
    apk = ROOT / fixture['apk']
    output = ROOT / 'build/native-device'
    output.mkdir(parents=True, exist_ok=True)

    def adb(*command, check=True):
        result = subprocess.run(['adb', '-s', args.serial, *command], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', timeout=30)
        if check and result.returncode:
            raise RuntimeError(f'adb {command}: {result.stdout}')
        return result.stdout.strip()

    if 'package:' in adb('shell', 'pm', 'path', package, check=False):
        raise RuntimeError('Fixture package already installed; refusing to overwrite it')
    result = {
        'status': 'running', 'applicationId': package,
        'apkSha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
        'api': adb('shell', 'getprop', 'ro.build.version.sdk'),
        'abi': adb('shell', 'getprop', 'ro.product.cpu.abi'),
        'pageSize': adb('shell', 'getconf', 'PAGE_SIZE'), 'cases': [],
        'scope': 'Native trigger/process exit only; no collection SDK configured'
    }
    installed = False
    result_path = output / 'result.json'

    def save():
        result_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')

    save()
    # 常量固定验收预期，不能从运行结果反推信号。
    cases = [
        ('RUNTIME_EXCEPTION', 1, 'SIGABRT'), ('NULL_POINTER', 2, 'SIGSEGV'),
        ('ARRAY_INDEX_OUT_OF_BOUNDS', 3, 'SIGSEGV'), ('LIST_INDEX_OUT_OF_BOUNDS', 4, 'SIGABRT'),
        ('STRING_INDEX_OUT_OF_BOUNDS', 5, 'SIGABRT'), ('CLASS_CAST', 6, 'SIGABRT'),
        ('INTEGER_DIVISION_BY_ZERO', 7, 'SIGFPE'), ('NUMBER_FORMAT', 8, 'SIGABRT'),
        ('ILLEGAL_ARGUMENT', 9, 'SIGABRT'), ('ILLEGAL_STATE', 10, 'SIGABRT'),
        ('UNINITIALIZED_PROPERTY', 11, 'SIGABRT'), ('ABORT', 12, 'SIGABRT'),
        ('SEGMENTATION_FAULT', 13, 'SIGSEGV')
    ]
    try:
        install_output = adb('install', str(apk))
        if 'Success' not in install_output:
            raise RuntimeError(install_output)
        installed = True
        for scenario, code, expected_signal in cases:
            for thread in ('MAIN', 'BACKGROUND'):
                run_id = 'native-' + uuid.uuid4().hex
                case_id = scenario.lower() + '-' + thread.lower()
                record = {'id': case_id, 'runId': run_id, 'expectedSignal': expected_signal,
                          'status': 'running', 'evidence': f'{case_id}.log'}
                record['expectedCppFailure'] = CPP_FAILURES.get(code)
                result['cases'].append(record)
                # 先落盘，再触发故障，外部执行中断后仍能关联本次运行。
                save()
                adb('shell', 'am', 'force-stop', package)
                started = time.monotonic()
                launch = adb('shell', 'am', 'start', '-n', package + '/verification.crash.VerificationActivity',
                             '--es', 'scenario', scenario, '--ez', 'native', 'true', '--es', 'thread', thread,
                             '--es', 'runId', run_id, check=False)
                pid = None
                log = ''
                passed = False
                while time.monotonic() - started < 18:
                    if pid is None:
                        markers = adb('logcat', '-d', '-v', 'threadtime', '-s', 'lib_crash:E', '*:S')
                        for line in markers.splitlines():
                            if run_id in line:
                                match = re.match(r'\S+\s+\S+\s+(\d+)\s+(\d+)\s+', line)
                                if match:
                                    pid = match.group(1)
                                    break
                    if pid is not None:
                        log = adb('logcat', '-d', '-v', 'threadtime', '--pid', pid)
                        exited = not adb('shell', 'pidof', package, check=False)
                        if matches_failure(log, code, expected_signal, thread, run_id) and exited:
                            passed = True
                            break
                    time.sleep(0.3)
                (output / f'{case_id}.log').write_text(log or launch, encoding='utf-8')
                record.update({'status': 'passed' if passed else 'failed',
                               'durationSeconds': round(time.monotonic() - started, 2)})
                save()
                print(f'{case_id}: {"PASS" if passed else "FAIL"} {expected_signal}', flush=True)
                if not passed:
                    raise AssertionError(f'Failed {case_id}; see {output / (case_id + ".log")}')
        result['status'] = 'passed'
    except Exception as error:
        result['status'] = 'failed'
        result['error'] = str(error)
        raise
    finally:
        if installed:
            # 仅清理本次创建且安装前确认不存在的随机测试包。
            cleanup = adb('uninstall', package, check=False)
            result['fixtureRemoved'] = 'Success' in cleanup
        save()
    print(f'Native device verification passed: {len(result["cases"])} cases; {result_path}')


if __name__ == '__main__':
    main()
