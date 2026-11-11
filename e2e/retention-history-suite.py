# @spec docs/BACKLOG.md#sls-078 | docs/RETENTION_HISTORY_REPLAY.md
# @verifies docs/BACKLOG.md#sls-078 | docs/RETENTION_HISTORY_REPLAY.md#lecture-publique-restitution-et-preuves-propres
"""Run one real DEV replay case and bind its report to deployed sources/images."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import time
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['source', 'terminal'])
    parser.add_argument('mode', choices=['invalid', 'not-eligible', 'preflight', 'age', 'seed-loss', 'observer-loss', 'foreign-namespace'])
    args = parser.parse_args()
    if args.mode == 'foreign-namespace' and args.kind != 'source':
        parser.error('foreign-namespace requires the live source capture')
    root = Path(__file__).resolve().parent.parent
    suite = runpy.run_path(str(root / 'e2e/execution-suite.py'))
    out = root / '.local/e2e'
    out.mkdir(mode=0o700, parents=True, exist_ok=True)
    name = 'retention-history-' + args.kind + '-' + args.mode + '-' + uuid4().hex
    checkpoint = out / (name + '-checkpoint.json')
    pattern = 'retention-history-replay-' + args.kind + '-' + args.mode + '-*.json'
    previous = set(out.glob(pattern))
    before = suite['snapshot'](str(checkpoint.relative_to(root)), False, include_adapter=True)
    state = {'completed': False, 'kind': args.kind, 'mode': args.mode,
             'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
             'started_at_ns': time.time_ns(), 'before': before}

    def save():
        checkpoint.write_text(json.dumps(state, indent=2) + '\n')
        checkpoint.chmod(0o600)

    save()
    credentials = suite['private_credentials']() if args.mode in ('preflight', 'age', 'foreign-namespace') else None
    try:
        with (out / (name + '.stdout')).open('xb') as stdout, (out / (name + '.stderr')).open('xb') as stderr:
            os.fchmod(stdout.fileno(), 0o600)
            os.fchmod(stderr.fileno(), 0o600)
            process = subprocess.run(['node', str(root / 'e2e/retention-history-replay.mjs'), args.kind, args.mode],
                                     cwd=root, input=credentials, stdout=stdout, stderr=stderr, timeout=660)
        state['exit_code'] = process.returncode
        paths = set(out.glob(pattern)) - previous
        assert len(paths) == 1, 'exactly_one_original_report_required'
        report_path = paths.pop()
        raw = report_path.read_bytes()
        report = json.loads(raw)
        state.update(report_path=str(report_path.relative_to(root)), report_sha256=hashlib.sha256(raw).hexdigest(), report=report)
        after = suite['snapshot'](str(report_path.relative_to(root)), False, include_adapter=True)
        state['after'] = after
        assert all(before[key] == after[key] for key in ('source_sha256', 'image', 'adapter_images')), 'sources_or_images_changed'
        assert process.returncode == 0 and report['completed'] and report['cleanup'] and not report['failure'] and report['skipped'] == 0
        expected = 1 if args.mode in ('invalid', 'not-eligible') else 2 if args.mode in ('seed-loss', 'observer-loss') else 4 if args.mode == 'foreign-namespace' else 3
        assert len(report['checks']) == expected and all(row['status'] == 'passed' for row in report['checks'])
        state['completed'] = True
    except BaseException as error:
        state['failure_type'] = type(error).__name__
        raise
    finally:
        credentials = None
        state['finished_at_ns'] = time.time_ns()
        save()
        print(json.dumps({'completed': state['completed'], 'kind': args.kind, 'mode': args.mode,
                          'groups': len(state.get('report', {}).get('checks', [])),
                          'checkpoint': str(checkpoint.relative_to(root))}), flush=True)


if __name__ == '__main__':
    main()
