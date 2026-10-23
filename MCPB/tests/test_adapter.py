#!/usr/bin/env python3
"""Exercise the packed production adapter, never the owner's awake settings.

Signed fixture backends have no preferences, power assertions or network access.
Only get_status/initialize/tools-list are sent to the real installed app.
"""
import json
import os
from pathlib import Path
import plistlib
import select
import shutil
import signal
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
IDENTITY = 'Developer ID Application: Chester Wong Consulting Ltd (3GPMM2KM4R)'

FIXTURE = r'''
import Foundation
import Darwin
if CommandLine.arguments.contains("--mcp") {
    let info = Bundle.main.infoDictionary ?? [:]
    while let line = readLine() {
        guard let data = line.data(using: .utf8),
              let request = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let id = request["id"] else { continue }
        let disabled = info["FixtureDisabled"] as? Bool ?? false
        let result: [String: Any] = ["content": [["type": "text", "text": disabled ? "AI assistants disabled" : "fixture"]],
            "structuredContent": ["fixture": true, "active": false, "edition": info["CFBundleIdentifier"] ?? ""],
            "isError": disabled]
        let response: [String: Any] = ["jsonrpc": "2.0", "id": id, "result": result]
        print(String(data: try! JSONSerialization.data(withJSONObject: response), encoding: .utf8)!)
        fflush(stdout)
    }
    exit(0)
}
fputs("Fixture only supports --mcp\n", stderr)
exit(2)
'''


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='extra-caffeine-adapter-tests-')
        cls.base = Path(cls.tmp.name)
        cls.clients = []
        archive = ROOT / 'dist/mcpb/extra-caffeine-0.1.0.mcpb'
        with zipfile.ZipFile(archive) as z:
            member = z.getinfo('server/extra-caffeine-adapter')
            assert member.external_attr >> 16 & 0o111, 'Archive lost executable permissions'
            z.extractall(cls.base / 'unpacked')
        cls.adapter = cls.base / 'unpacked/server/extra-caffeine-adapter'
        cls.adapter.chmod(0o755)
        subprocess.run(['codesign', '--verify', '--strict', str(cls.adapter)], check=True)
        source = cls.base / 'fixture.swift'
        source.write_text(FIXTURE)
        cls.fixture_bin = cls.base / 'fixture'
        subprocess.run(['xcrun', 'swiftc', str(source), '-o', str(cls.fixture_bin)], check=True)

    @classmethod
    def tearDownClass(cls):
        for proc in cls.clients:
            if proc.poll() is None:
                proc.terminate()
            proc.wait(timeout=10)
            for stream in [proc.stdin, proc.stdout, proc.stderr]:
                if stream:
                    stream.close()
        cls.tmp.cleanup()

    def bundle(self, label, identifier='com.chesterwong.ExtraCaffeine.Direct', version='1.2', signed=True, disabled=False):
        path = self.base / (label + '.app')
        contents = path / 'Contents'
        (contents / 'MacOS').mkdir(parents=True)
        shutil.copy2(self.fixture_bin, contents / 'MacOS/Fixture With Spaces')
        (contents / 'Info.plist').write_bytes(plistlib.dumps({
            'CFBundleIdentifier': identifier, 'CFBundleExecutable': 'Fixture With Spaces',
            'CFBundleShortVersionString': version, 'CFBundleName': label,
            'CFBundlePackageType': 'APPL', 'LSUIElement': True, 'FixtureDisabled': disabled,
        }))
        if signed:
            subprocess.run(['codesign', '--force', '--timestamp=none', '--sign', IDENTITY, str(path)],
                           check=True, capture_output=True)
        return path

    def rejected(self, app, message):
        response = subprocess.run([str(self.adapter), '--app', str(app)], capture_output=True, text=True, timeout=15)
        self.assertNotEqual(response.returncode, 0)
        self.assertEqual(response.stdout, '', 'Diagnostics must not corrupt MCP stdout')
        self.assertIn(message, response.stderr)

    def client(self, app):
        proc = subprocess.Popen([str(self.adapter), '--app', str(app)], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self.clients.append(proc)
        return proc

    def request(self, proc, request):
        proc.stdin.write(json.dumps(request) + '\n')
        proc.stdin.flush()
        self.assertTrue(select.select([proc.stdout], [], [], 12)[0], 'No protocol response')
        line = proc.stdout.readline()
        if not line:
            self.fail('Adapter exited: ' + proc.stderr.read())
        return json.loads(line)

    def test_missing_or_relative_app(self):
        self.rejected(self.base / 'Absent.app', 'Select an installed')
        self.rejected(Path('relative.app'), 'Usage:')

    def test_wrong_product(self):
        app = self.bundle('Other Product', identifier='com.example.NotExtraCaffeine')
        self.rejected(app, 'Select an installed')

    def test_old_version(self):
        app = self.bundle('Old Edition', version='1.1.9')
        self.rejected(app, '1.2 or later')

    def test_unsigned_or_modified_vendor_app(self):
        app = self.bundle('Unsigned', signed=False)
        self.rejected(app, 'signature verification failed')
        app = self.bundle('Tampered')
        with (app / 'Contents/MacOS/Fixture With Spaces').open('ab') as file:
            file.write(b'tampered')
        self.rejected(app, 'signature verification failed')

    def test_executable_outside_bundle(self):
        app = self.bundle('External executable', signed=False)
        executable = app / 'Contents/MacOS/Fixture With Spaces'
        executable.unlink()
        executable.symlink_to(self.fixture_bin)
        self.rejected(app, 'outside the app bundle')

    def test_old_installed_app_is_rejected(self):
        app = Path.home() / 'Applications/Extra Caffeine.app'
        if not app.exists():
            self.skipTest('Old installed app not present')
        info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
        if info.get('CFBundleShortVersionString') != '1.1':
            self.skipTest('Installed app has changed; fixture covers minimum version')
        self.rejected(app, '1.2 or later')

    def test_both_editions_stdio_spaces_and_exit(self):
        for index, identifier in enumerate(['com.chesterwong.ExtraCaffeine', 'com.chesterwong.ExtraCaffeine.Direct']):
            with self.subTest(identifier=identifier):
                app = self.bundle('Path with spaces ; literal ' + str(index), identifier=identifier)
                proc = self.client(app)
                result = self.request(proc, {'jsonrpc': '2.0', 'id': 42, 'method': 'tools/call',
                                             'params': {'name': 'get_status', 'arguments': {}}})
                self.assertEqual(result['id'], 42)
                self.assertEqual(result['result']['structuredContent']['edition'], identifier)
                self.assertFalse(result['result']['isError'])
                proc.stdin.close()
                self.assertEqual(proc.wait(timeout=10), 0)
                self.assertEqual(proc.stderr.read(), '')

    def test_disabled_access_error_passes_through(self):
        app = self.bundle('Disabled fixture', disabled=True)
        proc = self.client(app)
        result = self.request(proc, {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                                     'params': {'name': 'get_status', 'arguments': {}}})
        self.assertTrue(result['result']['isError'])
        self.assertEqual(result['result']['content'][0]['text'], 'AI assistants disabled')
        proc.terminate()
        self.assertEqual(proc.wait(timeout=10), -signal.SIGTERM)

    def test_installed_real_app_read_only(self):
        app = Path('/Applications/Extra Caffeine Direct.app')
        if not app.exists():
            self.skipTest('Real direct edition is not installed here')
        proc = self.client(app)
        initialize = self.request(proc, {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                                        'params': {'protocolVersion': '2025-11-25', 'capabilities': {},
                                                   'clientInfo': {'name': 'adapter-validation', 'version': '0.1.0'}}})
        self.assertIn('tools', initialize['result']['capabilities'])
        tools = self.request(proc, {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})
        self.assertEqual({x['name'] for x in tools['result']['tools']},
                         {'get_status', 'turn_on', 'turn_off', 'schedule', 'list_schedules', 'cancel_schedule'})
        status = self.request(proc, {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call',
                                    'params': {'name': 'get_status', 'arguments': {}}})
        # This edition may be closed. Read-only discovery still works and status
        # must either provide real state or an explicit app-side availability error.
        if status['result']['isError']:
            self.assertIn('text', status['result']['content'][0])
            self.assertTrue(status['result']['content'][0]['text'])
            print('Real app status:', status['result']['content'][0]['text'])
        else:
            self.assertFalse(status['result']['structuredContent']['wakes_sleeping_mac'])
            self.assertTrue(status['result']['structuredContent']['app_must_remain_open'])
        proc.stdin.close()
        self.assertEqual(proc.wait(timeout=10), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
