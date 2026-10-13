"""Regression checks for artifact and crash-evidence false positives."""
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from verify_native_artifacts import verify_apk
from verify_native_device import matches_failure


class NativeArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='crash-verifier-test-')
        self.addCleanup(self.temp.cleanup)
        self.apk = Path(self.temp.name) / 'fixture.apk'
        self.libraries = {f'jni/{abi}/libcrash_native.so': abi.encode()
                          for abi in ('arm64-v8a', 'armeabi-v7a', 'x86_64')}

    def write_apk(self, entries, aligned=True, compressed=False):
        with zipfile.ZipFile(self.apk, 'w') as archive:
            for name, data in entries:
                info = zipfile.ZipInfo(name)
                if aligned:
                    padding = (-(archive.fp.tell() + 30 + len(name.encode()))) % 16384
                    if padding < 4:
                        padding += 16384
                    info.extra = struct.pack('<HH', 0xffff, padding - 4) + bytes(padding - 4)
                info.compress_type = zipfile.ZIP_DEFLATED if compressed else zipfile.ZIP_STORED
                archive.writestr(info, data)

    def entries(self):
        return [(name.replace('jni/', 'lib/', 1), data) for name, data in self.libraries.items()]

    def test_valid_apk(self):
        self.write_apk(self.entries())
        verify_apk(self.apk, self.libraries)

    def test_missing_libraries(self):
        for entries in ([], self.entries()[:-1]):
            with self.subTest(count=len(entries)):
                self.write_apk(entries)
                with self.assertRaisesRegex(AssertionError, 'Unexpected APK'):
                    verify_apk(self.apk, self.libraries)

    def test_changed_library(self):
        entries = self.entries()
        entries[0] = (entries[0][0], b'wrong library')
        self.write_apk(entries)
        with self.assertRaisesRegex(AssertionError, 'mismatch'):
            verify_apk(self.apk, self.libraries)

    def test_duplicate_library(self):
        with self.assertWarns(UserWarning):
            self.write_apk(self.entries() + [self.entries()[0]])
        with self.assertRaisesRegex(AssertionError, 'Unexpected APK'):
            verify_apk(self.apk, self.libraries)

    def test_alignment_and_compression(self):
        for aligned, compressed in ((False, False), (True, True)):
            with self.subTest(aligned=aligned, compressed=compressed):
                self.write_apk(self.entries(), aligned, compressed)
                with self.assertRaises(AssertionError):
                    verify_apk(self.apk, self.libraries)


class NativeEvidenceTests(unittest.TestCase):
    def log(self, exception='std::out_of_range: vector', code=4, thread='main', run_id='test-run'):
        failure = f'uncaught exception of type {exception}\n' if exception else ''
        return (f'scenario=native-list-index-out-of-bounds runId={run_id} thread={thread}\n'
                f'native-entry code={code}\n' + failure + 'Fatal signal 6 (SIGABRT)\n')

    def matches(self, log):
        return matches_failure(log, 4, 'SIGABRT', 'MAIN', 'test-run')

    def test_expected_failure(self):
        self.assertTrue(self.matches(self.log()))

    def test_generic_abort_and_wrong_exception_rejected(self):
        for exception in (None, 'std::runtime_error: vector', 'std::out_of_range: basic_string'):
            with self.subTest(exception=exception):
                self.assertFalse(self.matches(self.log(exception)))

    def test_wrong_run_thread_and_code_rejected(self):
        for log in (self.log(run_id='other'), self.log(thread='lib_crash-native-list'), self.log(code=40)):
            self.assertFalse(self.matches(log))

    def test_signal_case_rejects_cpp_failure(self):
        self.assertTrue(matches_failure(self.log(None, 12), 12, 'SIGABRT', 'MAIN', 'test-run'))
        self.assertFalse(matches_failure(self.log(code=12), 12, 'SIGABRT', 'MAIN', 'test-run'))


if __name__ == '__main__':
    unittest.main()
