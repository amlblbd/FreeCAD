"""Run an isolated, read-only stage-4 audit with the local FreeCAD build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
TEST = HERE.parent
ROOT = TEST.parents[2]
TASKS = ['document', 'body', 'paired', 'ears', 'distance', 'zone_0_40',
         'zone_40_55', 'zone_55_75', 'zone_75_595', 'zone_595_top', 'surface_body']


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--freecad', type=Path, default=ROOT / 'build/debug/bin/FreeCADCmd.exe')
    parser.add_argument('--timeout', type=int, default=180, help='Seconds per isolated check')
    parser.add_argument('--tasks', nargs='+', choices=TASKS, default=TASKS,
                        help='Run selected checks; omitted means the entire baseline')
    args = parser.parse_args()
    exe = args.freecad.resolve()
    if not exe.is_file() or args.timeout <= 0:
        parser.error('FreeCAD executable must exist and timeout must be positive')
    run = HERE / 'runs' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    snapshot = run / 'inputs'
    snapshot.mkdir(parents=True)
    sources = [TEST / 'B_pillar_stage4_working.FCStd', TEST / 'BPillarSurface.py']
    sources += [TEST / 'stage4_work' / name for name in (
        'paired_solid.brep', 'complete_outer.brep', 'paired_inner.brep',
        'full_profiles.json', 'inner_profiles.json', 'reference_inner_complete.brep',
        'paired_result.json', 'paired_wall_test.json', 'zone_checks.json', 'resume_checkpoint.json')]
    sources += [HERE / 'run.py', HERE / 'worker.py', TEST / 'large_files/manifest.json']
    records = []
    for source in sources:
        target = snapshot / source.relative_to(TEST)
        target.parent.mkdir(parents=True, exist_ok=True)
        before = digest(source)
        shutil.copyfile(source, target)
        if digest(target) != before:
            raise RuntimeError('Input changed while copying: ' + str(source))
        records.append(dict(path=source.relative_to(TEST).as_posix(), size=source.stat().st_size, sha256=before))
    manifest = json.loads((snapshot / 'large_files/manifest.json').read_text(encoding='utf-8'))
    expected = next(x for x in manifest['files'] if x['path'] == 'B_pillar_stage4_working.FCStd')
    env = os.environ.copy()
    pixi = ROOT / '.pixi/envs/default'
    env['PATH'] = os.pathsep.join([str(exe.parent), str(pixi), str(pixi / 'Library/bin'), env.get('PATH', '')])
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['BPILLAR_BASELINE_RUN'] = str(run)
    report = dict(schema=1, created_utc=datetime.now(timezone.utc).isoformat(),
                  git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  executable=str(exe), executable_sha256=digest(exe), timeout_seconds=args.timeout,
                  inputs=records, archive_matches=records[0]['sha256'] == expected['sha256'], tasks=[])
    write(run / 'manifest.json', report)
    tasks = args.tasks
    report['requested_tasks'] = tasks
    report['full_suite_requested'] = set(tasks) == set(TASKS)
    for task in tasks:
        print('Checking ' + task, flush=True)
        env['BPILLAR_BASELINE_TASK'] = task
        command = [str(exe), '-u', str(run / (task + '_user.cfg')),
                   '-s', str(run / (task + '_system.cfg')), str(snapshot / 'baseline/worker.py')]
        start = datetime.now(timezone.utc)
        item = dict(task=task)
        with (run / (task + '.log')).open('wb') as log:
            try:
                result = subprocess.run(command, cwd=run, env=env, stdin=subprocess.DEVNULL,
                                        stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
                item['exit_code'] = result.returncode
                output = run / (task + '.json')
                item['execution'] = 'completed' if result.returncode == 0 and output.exists() else 'error'
                if output.exists():
                    item['result'] = json.loads(output.read_text(encoding='utf-8'))
                    if 'error' in item['result']:
                        item['execution'] = 'error'
            except subprocess.TimeoutExpired:
                item['execution'] = 'timeout'
        item['seconds'] = (datetime.now(timezone.utc) - start).total_seconds()
        report['tasks'].append(item)
        write(run / 'manifest.json', report)
        print(task + ': ' + item['execution'], flush=True)
    report['originals_unchanged'] = all(digest(TEST / x['path']) == x['sha256'] for x in records)
    report['execution_complete'] = all(x['execution'] == 'completed' for x in report['tasks'])
    write(run / 'manifest.json', report)
    print('Report: ' + str(run / 'manifest.json'), flush=True)
    return 0 if report['execution_complete'] and report['originals_unchanged'] else 1


if __name__ == '__main__':
    sys.exit(main())
