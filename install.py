#!/usr/bin/env python3
"""Install the SDA skill locally without executing project code or using the network."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def verify_package(source):
    required = ('SKILL.md', 'references/ARCHITECTURE_STANDARDS.md',
                'references/report-template.md', 'references/provenance.json')
    for name in required:
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Missing or unsafe package file: {name}')
    for path in source.rglob('*'):
        if path.is_symlink():
            raise ValueError('Package must not contain symbolic links')
    metadata = json.loads((source / 'references/provenance.json').read_text())
    digest = hashlib.sha256((source / 'references/ARCHITECTURE_STANDARDS.md').read_bytes()).hexdigest()
    if digest != metadata['standard_sha256']:
        raise ValueError('Architecture standard checksum mismatch')


def install(agent, destination=None, home=None):
    source = Path(__file__).resolve().parent / agent / 'sda'
    verify_package(source)
    if destination is None:
        base = Path.home() if home is None else Path(home)
        parent = base / ('.agents' if agent == 'codex' else '.claude') / 'skills'
        destination = parent / 'sda'
    else:
        destination = Path(destination).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f'Skill destination already exists: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # copytree refuses an existing destination, including a concurrent creation.
    shutil.copytree(source, destination)
    verify_package(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', required=True, choices=('codex', 'claude'))
    parser.add_argument('--destination', type=Path, help='Explicit new skill directory')
    args = parser.parse_args()
    try:
        destination = install(args.agent, args.destination)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'Installation not completed: {exc}\n')
    print(f'SDA copied and verified: {destination}\nVerify that your agent loads it; start a new session if needed.')


if __name__ == '__main__':
    main()
