"""Restore the original large files: python large_files/restore.py."""
import hashlib
import json
import os
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def restore(base=None):
    archive = Path(__file__).resolve().parent
    base = Path(base).resolve() if base else archive.parent
    manifest = json.loads((archive / 'manifest.json').read_text(encoding='utf-8'))
    for item in manifest['files']:
        target = (base / item['path']).resolve()
        if not target.is_relative_to(base):
            raise ValueError('Target outside restore directory')
        if target.exists():
            if target.stat().st_size == item['size'] and sha256(target) == item['sha256']:
                print('Verified:', item['path'])
                continue
            raise FileExistsError(f'Refusing to overwrite changed file: {target}')
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.restoring')
        digest = hashlib.sha256()
        size = 0
        created = False
        try:
            with temporary.open('xb') as output:
                created = True
                for part in item['parts']:
                    source = (archive / part['path']).resolve()
                    if not source.is_relative_to(archive):
                        raise ValueError('Part outside archive directory')
                    if source.stat().st_size != part['size'] or sha256(source) != part['sha256']:
                        raise ValueError(f'Corrupt part: {source}')
                    with source.open('rb') as stream:
                        for block in iter(lambda: stream.read(1024 * 1024), b''):
                            output.write(block)
                            digest.update(block)
                            size += len(block)
            if size != item['size'] or digest.hexdigest() != item['sha256']:
                raise ValueError(f'Combined checksum mismatch: {target}')
            if target.exists():
                raise FileExistsError(f'Target appeared during restore: {target}')
            os.rename(temporary, target)
        except Exception:
            if created and temporary.exists():
                temporary.unlink()
            raise
        print('Restored:', item['path'])


if __name__ == '__main__':
    restore()
