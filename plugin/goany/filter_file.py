# -*- coding:utf-8 -*-
#    author    :   丁雪峰
#    time      :   2015-08-05 09:32:14
#    email     :   fengidri@yeah.net
#    version   :   1.0.1

import os
import pyvim
import vim
import time
import popup

class g:
    recent = []


def check_file(f):
    if f[0] == '.':
        return False

    suffix = f.split('.')
    if len(suffix) > 1:
        suffix = suffix[-1]
        if suffix in ['o', 'so', 'pyc', 'lo', 'd']:
            return False

    return True

def getfiles(path, cur_path):
    lines = []
    lenght = len(path)
    if path[-1] != '/':
        lenght += 1

    for root, ds, fs in os.walk(cur_path):
        for f in fs:
            if not check_file(f):
                continue

            f = os.path.join(root, f)
            lines.append(f[lenght:])

    for root, ds, fs in os.walk(path):
        if root.startswith(cur_path):
            continue

        for f in fs:
            if not check_file(f):
                continue

            f = os.path.join(root, f)
            lines.append(f[lenght:])

    for name in g.recent:
        if name.startswith(path):
            name = name[lenght:]
            if name in lines:
                lines.remove(name)
                lines.insert(0, name + ' *')

    return lines




class file_filter(object):
    def __init__(self, path):
        self.path = path
        self.fs = getfiles(path, os.path.dirname(vim.current.buffer.name))

        s = time.time()
        pyvim.log.debug("getfiles use time: %s" % (time.time() - s))

        popup.PopupSearch(self.filter_cb, finish_cb = self.finish_cb, center = True)

    def filter_cb(self, words, bwords):
        self.active_index = None
        if not words:
            return self.fs

        self.active_index = []
        o = []

        for i,line in enumerate(self.fs):
            for w in words:
                if line.find(w) == -1:
                    break
            else:
                o.append(line)
                self.active_index.append(i)

        return o

    def finish_cb(self, ret):
        if ret <= -1:
            return

        if self.active_index:
            index = self.active_index[ret]
        else:
            index = ret

        f = self.fs[index]
        if f.endswith(' *'):
            f = f[0:-2]

        path = os.path.join(self.path, f)
        pyvim.log.info("i got : %s", path)

        vim.command("update")
        vim.command("edit %s" % path)

        if path not in g.recent:
            g.recent.append(path)
            g.recent.sort()


def FileFilter():
    name = vim.current.buffer.name
    root = None
    for r in pyvim.Roots:
        if not name or name.startswith(r):
            root = r
            break

    if root:
        file_filter(root)
    else:
        pyvim.echo("Not Found root in pyvim.Roots for current file.", hl=True)

def cfile_goto():
    if not pyvim.Roots:
        return

    root = pyvim.Roots[0]
    l = vim.current.line.split(':')
    if len(l) <= 4:
        return

    cfile = l[0]
    linenu = l[1]
    col = l[2]

    if not linenu.isdigit():
        return

    if not col.isdigit():
        return

    f = os.path.basename(cfile)

    for root, ds, fs in os.walk(root):
        if f in fs:
            path = os.path.join(root, f)
            break
    else:
        return

    vim.command('wincmd p')
    w = vim.current.window
    if not w.buffer.name:
        for w in vim.windows:
            name = w.buffer.name
            if name.startswith(root):
                vim.current.window = w
                vim.command("update")
                vim.command("edit %s" % path)
                break
        else:
            vim.command('split %s' % path)
    else:
        vim.command("update")
        vim.command("edit %s" % path)

    vim.current.window.cursor = (int(linenu), int(col) - 1)


