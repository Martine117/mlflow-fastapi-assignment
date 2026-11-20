r"""Read-only checks. Run: .venv\Scripts\python verify.py --version 2"""
import argparse
import csv
import json
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def verify(version):
    expected = [{'id': '1', 'score': '80'}, {'id': '2', 'score': '90'}]
    if version == 2:
        expected.append({'id': '3', 'score': '95'})
    with Path('data/dvc_demo.csv').open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == ['id', 'score'], 'Unexpected columns'
        assert list(reader) == expected, 'Dataset content differs'
    tracked = git('ls-files').splitlines()
    assert 'data/dvc_demo.csv.dvc' in tracked
    assert 'data/dvc_demo.csv' not in tracked
    assert not any(p.startswith(('.venv/', '.dvc/cache/')) or p.endswith('config.local') for p in tracked)
    for path in ['data/dvc_demo.csv', '.dvc/config.local', '.venv/probe', '.env']:
        subprocess.run(['git', 'check-ignore', '-q', path], check=True)
    assert '[\'remote "myazure"\']' in Path('.dvc/config').read_text()
    for tag in ['dvc-demo-v1', 'dvc-demo-v2']:
        pointer = git('show', f'{tag}:data/dvc_demo.csv.dvc')
        assert 'md5:' in pointer
    assert git('show', 'dvc-demo-v1:data/dvc_demo.csv.dvc') != git('show', 'dvc-demo-v2:data/dvc_demo.csv.dvc')
    print(json.dumps({'version': version, 'records': len(expected), 'checks': 'passed'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', type=int, choices=[1, 2], required=True)
    verify(parser.parse_args().version)
