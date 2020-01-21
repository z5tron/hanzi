import subprocess
import re
import sys
import os
from jinja2 import Template

inpname = sys.argv[1]
if not os.path.exists(inpname):
    raise RuntimeError("can not find file: {}".format(inpname))

tmpl = Template(open('qiangzhi/app/templates/print_words_3col.tex', 'r').read())
words=open(inpname, 'r').read()
words = re.sub(r'\s', '', words)
root, ext = os.path.splitext(inpname)

with open('{}.tex'.format(root), 'w') as f:
    f.write(tmpl.render(title="title", words=words))

for i in range(2):
    subprocess.check_call('xelatex {}'.format(root), shell=True)

print(words)
for ext in ['out', 'aux', 'log']:
    os.remove('{}.{}'.format(root, ext))

