"""BH adapter runner: import a detector from PYTHONPATH-injected source and emit
{relpath: {'enc': raw_label, 'conf': confidence}} for every corpus file. Raw
(un-normalised) labels are kept so naming quirks (a provenance fingerprint)
survive. Invoked in a subprocess with PYTHONPATH set to the extracted package's
parent dir, so the right chardet/csn version is imported in isolation."""
import sys, os, json

kind, corpus = sys.argv[1], sys.argv[2]
SKIP = ('.md', '.tsv', '.py', '.gitignore')
files = []
for root, _, fs in os.walk(corpus):
    for f in fs:
        if f.endswith(SKIP):
            continue
        files.append(os.path.join(root, f))
files.sort()

if kind == 'chardet':
    import chardet
    def detect(d):
        r = chardet.detect(d) or {}
        return {'enc': r.get('encoding'), 'conf': r.get('confidence')}
    ver = getattr(chardet, '__version__', '?')
elif kind == 'csn':
    from charset_normalizer import from_bytes
    import charset_normalizer
    def detect(d):
        r = from_bytes(d).best()
        return {'enc': (r.encoding if r else None), 'conf': None}
    ver = getattr(charset_normalizer, '__version__', '?')
else:
    raise SystemExit('unknown kind')

out = {}
for p in files:
    key = os.path.relpath(p, corpus)
    try:
        with open(p, 'rb') as fh:
            out[key] = detect(fh.read())
    except Exception as e:
        out[key] = {'enc': f'ERR:{type(e).__name__}', 'conf': None}

print(json.dumps({'impl_version': ver, 'results': out}))
