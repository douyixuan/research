#!/usr/bin/env python3
import hashlib
import json
import subprocess
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path

BASE_PREFIX = '#include <stdio.h>\nint main(void){\n  int x=0;\n'
BASE_SUFFIX = '  printf("%d\\n", x);\n  return 0;\n}\n'
N = 32
REQUIRED = {3, 11, 19}
LINES = [f'  x += {1 if i in REQUIRED else 0}; /* token-{i:02d} */\n' for i in range(N)]
EXPECTED = str(len(REQUIRED))


def render(config):
    return BASE_PREFIX + ''.join(LINES[i] for i in config) + BASE_SUFFIX


def intervals(config, base):
    pos = {v: i for i, v in enumerate(base)}
    idx = [pos[x] for x in config if x in pos]
    if len(idx) != len(config):
        return None
    out = []
    if not idx:
        return out
    start = previous = idx[0]
    for current in idx[1:]:
        if current == previous + 1:
            previous = current
        else:
            out += [start, previous + 1]
            start = previous = current
    out += [start, previous + 1]
    return out


def varint_size(value):
    value = max(0, value)
    size = 1
    while value >= 128:
        value >>= 7
        size += 1
    return size


@dataclass
class Cache:
    kind: str
    base: list
    store: dict
    hits: int = 0
    peak_bytes: int = 0

    def __init__(self, kind, base):
        self.kind = kind
        self.base = list(base)
        self.store = {}
        self.hits = 0
        self.peak_bytes = 0

    def key(self, config):
        source = render(config).encode()
        if self.kind == 'none':
            return None
        if self.kind == 'str':
            return source
        if self.kind == 'sha':
            return hashlib.sha512(source).digest()
        if self.kind == 'zip':
            return zlib.compress(source, 9)
        if self.kind == 'rcc':
            encoded = intervals(config, self.base)
            return None if encoded is None else tuple(encoded)
        raise ValueError(self.kind)

    def key_bytes(self, key):
        if key is None:
            return 0
        if isinstance(key, bytes):
            return len(key)
        return sum(varint_size(value) for value in key)

    def lookup(self, config):
        key = self.key(config)
        if key is not None and key in self.store:
            self.hits += 1
            return True, self.store[key]
        return False, None

    def add(self, config, value):
        key = self.key(config)
        if key is not None:
            self.store[key] = value
            live_bytes = sum(self.key_bytes(item) for item in self.store)
            self.peak_bytes = max(self.peak_bytes, live_bytes)

    def refresh(self, new_best):
        if self.kind != 'rcc':
            return
        old_base = list(self.base)
        survivors = []
        for key, value in list(self.store.items()):
            config = []
            for index in range(0, len(key), 2):
                begin, end = key[index], key[index + 1]
                config.extend(old_base[begin:end])
            survivors.append((config, value))
        self.base = list(new_best)
        self.store = {}
        new_base_set = set(self.base)
        for config, value in survivors:
            if set(config).issubset(new_base_set):
                self.add(config, value)


def compile_oracle(config, tmpdir):
    source = Path(tmpdir) / 'candidate.c'
    executable = Path(tmpdir) / 'candidate'
    source.write_text(render(config))
    compile_result = subprocess.run(
        ['gcc', '-O0', str(source), '-o', str(executable)],
        capture_output=True,
        text=True,
    )
    if compile_result.returncode != 0:
        return False
    run_result = subprocess.run([str(executable)], capture_output=True, text=True)
    return run_result.returncode == 0 and run_result.stdout.strip() == EXPECTED


def reduce(kind):
    best = list(range(N))
    cache = Cache(kind, best)
    oracle_calls = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        def test(config):
            nonlocal oracle_calls
            hit, value = cache.lookup(config)
            if hit:
                return value
            oracle_calls += 1
            value = compile_oracle(config, tmpdir)
            cache.add(config, value)
            return value

        assert test(best)
        changed = True
        while changed:
            changed = False
            for chunk in [8, 4, 2, 1]:
                index = 0
                while index < len(best):
                    candidate = best[:index] + best[index + chunk:]
                    if candidate != best and test(candidate):
                        best = candidate
                        cache.refresh(best)
                        changed = True
                        index = 0
                    else:
                        index += chunk
            for element in list(best):
                candidate = [item for item in best if item != element]
                if candidate != best and test(candidate):
                    best = candidate
                    cache.refresh(best)
                    changed = True

    return {
        'scheme': kind,
        'final_config': best,
        'final_tokens': len(best),
        'oracle_calls': oracle_calls,
        'cache_hits': cache.hits,
        'cache_entries': len(cache.store),
        'peak_key_bytes': cache.peak_bytes,
    }


def main():
    results = [reduce(kind) for kind in ['none', 'str', 'sha', 'zip', 'rcc']]
    baseline = results[0]
    assert all(result['final_config'] == baseline['final_config'] for result in results)
    assert baseline['final_config'] == sorted(REQUIRED)
    assert results[1]['oracle_calls'] < baseline['oracle_calls']
    assert results[-1]['peak_key_bytes'] < results[2]['peak_key_bytes']

    report = {
        'probe': 'fresh gcc compile+execute reduction',
        'gcc': subprocess.run(['gcc', '--version'], capture_output=True, text=True).stdout.splitlines()[0],
        'expected': EXPECTED,
        'results': results,
    }
    print(json.dumps(report, indent=2))
    Path('results').mkdir(exist_ok=True)
    Path('results/reproduction.json').write_text(json.dumps(report, indent=2) + '\n')

    cached = next(item for item in results if item['scheme'] == 'str')
    rcc = next(item for item in results if item['scheme'] == 'rcc')
    sha = next(item for item in results if item['scheme'] == 'sha')
    saved = 100.0 * (baseline['oracle_calls'] - cached['oracle_calls']) / baseline['oracle_calls']
    rcc_vs_sha = 100.0 * (sha['peak_key_bytes'] - rcc['peak_key_bytes']) / sha['peak_key_bytes']
    rows = [
        '# Reproduction summary',
        '',
        f"GCC: `{report['gcc']}`",
        '',
        '| Scheme | Oracle calls | Cache hits | Peak key-byte proxy | Final config |',
        '|---|---:|---:|---:|---|',
    ]
    for item in results:
        rows.append(
            f"| {item['scheme']} | {item['oracle_calls']} | {item['cache_hits']} | "
            f"{item['peak_key_bytes']} | `{item['final_config']}` |"
        )
    rows += [
        '',
        f'- Any cache avoided **{saved:.2f}%** of compile+execute oracle calls versus no cache in this scoped probe.',
        f'- RCC interval-key proxy used **{rcc_vs_sha:.2f}%** fewer peak key bytes than SHA-512. This is a key-size proxy, not JVM heap usage.',
        '- All schemes converged to the same three required fragments.',
    ]
    Path('results/summary.md').write_text('\n'.join(rows) + '\n')


if __name__ == '__main__':
    main()
