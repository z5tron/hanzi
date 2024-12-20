import subprocess
import re
import sys
import os
from jinja2 import Template

def print_3col(inpname):
    tmpl = Template(open('qiangzhi/app/templates/print_words_3col.tex', 'r').read())
    words=open(inpname, 'r').read()
    words = re.sub(r'\s', '', words)
    root, ext = os.path.splitext(inpname)
    ftex = '{}-col.tex'.format(root)
    with open(ftex, 'w') as f:
        f.write(tmpl.render(title=root, words=words))
    return ftex

def print_row(inpname):
    tmpl = Template(open('qiangzhi/app/templates/print_words_row.tex', 'r').read())
    words=open(inpname, 'r').read()
    words = re.sub(r'\s+', ' ', words)
    # print(words)
    nrow, ncol = 16, 12
    sz = nrow * ncol
    while len(words) > sz: sz += nrow * ncol 
    sz = max(sz, 6*nrow*ncol)
    words = words + " " * (sz - len(words))
    lines = []
    for i in range(0, len(words), ncol):
        lines.append(words[i:i+ncol])

    root, ext = os.path.splitext(inpname)
    ftex = '{}-row.tex'.format(root)
    with open(ftex, 'w') as f:
        f.write(tmpl.render(title=root, lines=lines))
    return ftex

def main():
    mod, inpname = sys.argv[1:3]
    if not os.path.exists(inpname):
        raise RuntimeError("can not find file: {}".format(inpname))
    ftex = None
    if '-col' == mod:
        ftex = print_3col(inpname)
    elif '-row' == mod:
        ftex = print_row(inpname)
    else:
        raise RuntimeError("invalid format {}".format(sys.argv[1]))

    root, ext = os.path.splitext(ftex)
    for i in range(2):
        subprocess.check_call('xelatex {}'.format(root), shell=True)

    for ext in ['out', 'aux', 'log']:
        os.remove('{}.{}'.format(root, ext))


if __name__ == "__main__":
    main()
