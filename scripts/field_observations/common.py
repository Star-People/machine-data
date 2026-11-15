"""Small shared primitives; no station credentials or media enter public records."""
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path, PurePosixPath

SCHEMA = 'ufo-files-field-observation/v1'
FEED_SCHEMA = 'ufo-files-field-observation-feed/v1'
STATION = re.compile(r'[a-z0-9][a-z0-9-]{0,63}\Z')
EVENT = re.compile(r'[a-f0-9]{32}\Z')
SESSION = re.compile(r'[0-9TZ]+-[a-f0-9]{6}\Z')
HASH = re.compile(r'[a-f0-9]{64}\Z')
IDENTIFIER = re.compile(r'[A-Za-z0-9_.-]{1,200}\Z')
MAX_RECORD_BYTES = 1024 * 1024


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def safe_file(root, relative):
    root = Path(root)
    rel = PurePosixPath(relative)
    if not relative or rel.is_absolute() or '..' in rel.parts or '\\' in relative:
        raise ValueError('Unsafe relative path')
    path = root
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Symlink in evidence path')
    return path


def read_json(root, relative, optional=False, limit=8*1024*1024):
    p = safe_file(root, relative)
    try:
        if p.stat().st_size > limit:
            raise ValueError('Metadata exceeds size limit')
        raw = p.read_bytes()
    except FileNotFoundError:
        if optional:
            return None
        raise
    return json.loads(raw)


def atomic(path, value):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Refusing symlink output')
    raw = value if isinstance(value, bytes) else encode(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == raw:
        return False
    fd, name = tempfile.mkstemp(prefix='.observation-', suffix='.copying', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(raw); out.flush(); os.fsync(out.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return True


def number(value, minimum=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        return None
    return value if minimum is None or value >= minimum else None


def identifier(value, pattern):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError('Invalid identifier')
    return value
