#!/usr/bin/env python3
# Index helper: _idx.py add <path> <page_url> <media_url> <date> <subject> <view> <notes>
# Computes resolution via `identify`, dedups by path, writes index.json atomically.
import json, os, sys, subprocess, hashlib
D = os.path.expanduser('~/koch_work/web/photos')
IDX = os.path.join(D, 'index.json')
def load():
    try: return json.load(open(IDX))
    except Exception: return []
def save(a):
    tmp = IDX + '.tmp'; json.dump(a, open(tmp, 'w'), ensure_ascii=False, indent=1); os.replace(tmp, IDX)
def res(p):
    try:
        o = subprocess.run(['identify', '-format', '%wx%h\n', p], capture_output=True, text=True, timeout=30).stdout.split('\n')[0]
        return o.strip()
    except Exception: return ''
if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'add':
        p, page, media, date, subj, view, notes = sys.argv[2:9]
        p = os.path.abspath(os.path.expanduser(p))
        a = [e for e in load() if e['path'] != p]
        md5 = hashlib.md5(open(p, 'rb').read()).hexdigest()
        a.append(dict(path=p, source_page=page, media_url=media, date=date, subject=subj, view=view,
                      resolution=res(p), bytes=os.path.getsize(p), md5=md5, notes=notes))
        save(a); print('ok', p, a[-1]['resolution'], len(a))
    elif cmd == 'count':
        print(len(load()))
