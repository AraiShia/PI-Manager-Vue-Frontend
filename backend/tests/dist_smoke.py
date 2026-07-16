import os, glob, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
candidates = []
for d in [os.path.join(root, '.worktrees', 'frontend-repo', 'frontend', 'dist'),
          os.path.join(os.path.dirname(root), '.worktrees', 'frontend-repo', 'frontend', 'dist')]:
    if os.path.isdir(d):
        candidates.append(d)

for d in candidates:
    print('DIST?', d, os.listdir(d))
    for js in glob.glob(os.path.join(d, 'assets', '*.js')):
        with open(js, encoding='utf-8', errors='ignore') as f:
            txt = f.read()
        if '/api/pi/items' in txt:
            print('hit 8000/8001 etc:', '8000' in txt, '8001' in txt)
        if 'localhost:800' in txt:
            print('has localhost 800x reference:', re.findall(r'localhost:\d+', txt)[:5])

import re
