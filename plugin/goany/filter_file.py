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

    for suffix in [
            '.o',
            '.so',
            '.pyc',
            '.lo',
            '.d',
            '.ko',
            '.mod',
            '.order',
            '.mod.c',
            '.a']:

        if f.endswith(suffix):
            return False

    return True

def getfiles(path, cur_path = None):
    lines = []
    lenght = len(path)
    if path[-1] != '/':
        lenght += 1

    if cur_path:
        for root, ds, fs in os.walk(cur_path):
            for f in fs:
                if not check_file(f):
                    continue

                f = os.path.join(root, f)
                lines.append(f[lenght:])

    for root, ds, fs in os.walk(path):
        if cur_path and root.startswith(cur_path):
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
    def __init__(self, path, cur):
        self.path = path
        self.cur = cur
        self.cur_fs = None
        self.fs = getfiles(path, os.path.dirname(vim.current.buffer.name))

        s = time.time()
        pyvim.log.debug("getfiles use time: %s" % (time.time() - s))

        popup.PopupSearch(self.filter_cb, finish_cb = self.finish_cb, center = True)

    def check_bwords(self, f, bwords):
        for b in bwords:
            if f.find(b) > -1:
                return False

        return True

    def check_words(self, f, words):
        for w in words:
            if f.find(w) == -1:
                return False

        return True

    def filter_cb(self, words, line):
        self.active_index = None
        hi_words = ['*']
        if not words:
            return self.fs, hi_words

        self.active_index = []
        o = []

        if words[0] == '@help':
            o.append('first @: search inside current directory')
            o.append('prefix -: means black list word')
            return o

        if words[0] == '@':
            words = words[1:]

            if self.cur_fs == None:
                self.cur_fs = getfiles(self.cur)

            fs = self.cur_fs

        else:
            fs = self.fs

        ws = words
        words = []
        bwords = []

        for w in ws:
            if w[0] == '-':
                if w[1:]:
                    bwords.append(w[1:])
            else:
                words.append(w)

        for i,line in enumerate(fs):
            if not self.check_bwords(line, bwords):
                continue

            if not self.check_words(line, words):
                continue

            o.append(line)
            self.active_index.append(i)

        words.append('*')
        return o, words

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
        file_filter(root, os.path.dirname(name))
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
    vim.command("normal zz")


