"""Run the exact release archive on a fresh Mac without the paid application."""
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import zipfile

archive = Path('dist/mcpb/extra-caffeine-0.1.0.mcpb')
with tempfile.TemporaryDirectory(prefix='extra-caffeine-release-') as tmp:
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist()) == {'manifest.json', 'README.md', 'server/extra-caffeine-adapter'}
        manifest = json.loads(z.read('manifest.json'))
        assert manifest['compatibility']['platforms'] == ['darwin']
        z.extractall(tmp)
    helper = Path(tmp) / 'server/extra-caffeine-adapter'
    helper.chmod(0o755)
    subprocess.run(['codesign', '--verify', '--strict', str(helper)], check=True)
    arches = subprocess.check_output(['lipo', '-archs', str(helper)], text=True).split()
    assert set(arches) == {'arm64', 'x86_64'}, arches
    for args, expected in [([], 'Usage:'), (['--app', '/nonexistent/Extra Caffeine.app'], 'Select an installed')]:
        run = subprocess.run([str(helper), *args], capture_output=True, text=True, timeout=15)
        assert run.returncode == 1, run
        assert not run.stdout, run
        assert expected in run.stderr, run
    gatekeeper = subprocess.run(['spctl', '--assess', '--type', 'execute', '--verbose=4', str(helper)], capture_output=True, text=True)
    print(json.dumps({'architecture': platform.machine(), 'native_execution': 'passed', 'signature': 'passed', 'gatekeeper_exit': gatekeeper.returncode, 'gatekeeper_output': gatekeeper.stderr}, indent=2))
    if os.environ.get('REQUIRE_NOTARIZED') == 'true':
        subprocess.run(['codesign', '--verify', '--strict', '--all-architectures', '-R=notarized', '--check-notarization', '--verbose=4', str(helper)], check=True)
        print('PASS: Apple notarized requirement satisfied for all architectures')
