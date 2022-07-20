#encoding:utf8

import vim
import os
import pyvim
import sys
from pyvim import log as logging
from . import libtag
import popup
import history

class g:
    last_path = None
    last_pos  = None
    last_tag  = None
    msg = ''

    taglist_cur = None

def encode(cmd):
    # 把 tags 文件的里 命令式 tag 进行转码
    show_enco=vim.eval('&encoding')
    file_enco=vim.eval('&fileencoding')
    if file_enco != show_enco:
        if file_enco:
            cmd = cmd.decode(file_enco).encode(show_enco)
    return cmd



def goto_file(path):
    if path == vim.current.buffer.name:
        return

    vim.command('update')

    for b in vim.buffers:
        if path == b.name:
            vim.current.buffer = b
            break
    else:
        vim.command('silent edit %s'  % path)

def goto_pos(pos):
    vim.current.window.cursor = pos

    try:
        vim.command('normal zz')
    except vim.error as e:
        logging.error(e)


class TagStack(object):
    stacks = {}
    stack = None
    def __new__(cls, *args, **kwargs):
        w = vim.current.window
        stack = cls.stacks.get(w)
        if not stack:
            org = super(TagStack, cls)
            stack = org.__new__(cls, *args, **kwargs)
            cls.stacks[w] = stack
        return stack

    def __init__(self):
        if None == self.stack:
            self.stack = []

    def push(self, frame):
        self.stack.append(frame)

    def pop(self):
        if not self.stack:
            return
        return self.stack.pop()

    def refresh(self):
        if self.stack:
            tag = self.stack[-1]
            g.last_pos = tag.pos
            g.last_path = tag.pos
            g.last_tag = tag.tag

        else:
            g.last_pos = None
            g.last_path = None
            g.last_tag = None



class TagOne(libtag.Line):
    def back(self):
        goto_file(self.last_file)
        goto_pos(self.last_cursor)

    def goto(self):
        self.last_file = vim.current.buffer.name
        self.last_cursor = vim.current.window.cursor

        g.last_tag = self.tag
        g.last_pos = None
        g.last_path = None

        self._goto()

    def _goto(self):
        tag = self.tag

        root = pyvim.get_cur_root()
        path = os.path.join(root, self.file_path)

        goto_file(path)

        n = self.get_pos_real_time()
        if not n:
            return

        line = vim.current.buffer[n - 1]
        col = line.find(tag)
        if col >= 0:
            pos = (n, col)
        else:
            pos = (n, 0)

        goto_pos(pos)

        self.pos = pos
        self.path = path

        g.last_pos = pos
        g.last_path = path


    def get_pos_real_time(self):
        taglist = []

        for t in g.taglist_cur:
            if t.file_path == self.file_path:
                taglist.append(t)

        taglist.sort(key = lambda x: x.line_nu)

        index = taglist.index(self)

        tags = libtag.parse(vim.current.buffer.name)
        for t in tags:
            if t.tag != self.tag:
                continue

            index -= 1
            if index >= 0:
                continue

            break
        else:
            return

        return t.line_nu + 1

    def get_pos(self):
        if self.line_nu:
            return self.line_nu + 1

        pattern_nu = None
        pattern_nu_b = None

        for i, l in enumerate(vim.current.buffer):
            if l == self.pattern:
                pattern_nu = i
                break

            if l.find(tag) > -1 and None == pattern_nu_b:
                pattern_nu_b  = i

        else:
            g.msg = "linue num is guessed"
            pattern_nu  = pattern_nu_b


        if pattern_nu == None:
            g.msg = 'error patten: %s' % self.pattern
            return

        return pattern_nu + 1


class TagFrame(object):
    def __init__(self, lines):
        self.kinds = {}
        taglist   = []

        for line in lines:
            tag = TagOne(line)

            if isinstance(tag.pattern, str):
                " skip EXPORT_SYMBOL inside kernel source"
                if tag.pattern.startswith('EXPORT_SYMBOL'):
                    continue

            if self.kinds.get(tag.kind):
                self.kinds[tag.kind] += 1
            else:
                self.kinds[tag.kind] = 1

            taglist.append(tag)

        taglist = self.sort(taglist)

        self.taglist   = taglist
        self.tagname   = taglist[0].tag
        self.num       = len(self.taglist)

    def sort(self, taglist):
        "同一个 tag 的多个纪录, 把 f, v kind 的放前面."

        _taglist = []

        #kinds = 'fstudvm'
        kinds = ['function', 'struct', 'marco', 'variable', 'member']
        for k in kinds:
            for tag in taglist:
                if tag.kind == k:
                    _taglist.append(tag)

        for tag in taglist:
            if tag.kind in kinds:
                continue
            _taglist.append(tag)

        return _taglist

    def _goto(self, index):
        tag  = self.taglist[index]

        g.taglist_cur = self.taglist

        tag.goto()
        TagStack().push(tag)

        g.taglist_cur = None

        pyvim.echoline('Tag(%s) goto %s/%s kind: %s. [%s]' %
                (tag.tag, index + 1, self.num, tag.kind, g.msg))

    def ui_select(self):
        '使用 popup 展示, 用户进行选择'

        lines = []
        maxlen = 0
        for t in self.taglist:
            l = len(t.file_path)
            if l > maxlen:
                maxlen = l

        for t in self.taglist:
            f = t.file_path

            if t.show:
                l = t.show
            else:
                l = t.pattern

            if isinstance(l, str):
                l = l.strip()

            tt = r"%s  %s|%s" % (f.ljust(maxlen), t.kind, l)
            line = encode(tt)
            lines.append(line)

        self.lines = lines

        popup.PopupSearch(self.popup_filter_cb, finish_cb = self.popup_finish_cb,
                filetype=vim.eval('&ft'))

    def popup_filter_cb(self, words, line):
        self.active_index = None
        if not words:
            return self.lines

        self.active_index = []
        o = []

        for i,line in enumerate(self.lines):
            for w in words:
                if line.find(w) == -1:
                    break
            else:
                o.append(line)
                self.active_index.append(i)

        return o

    def popup_finish_cb(self, ret):
        if ret < 0:
            return

        if self.active_index:
            index = self.active_index[ret]
        else:
            index = ret

        logging.error("tags search window get: %s", index)

        self._goto(index)



    def goto_p(self):
        if self.tagname != g.last_tag:
            return

        kind = 'prototype'

        if self.kinds.get(kind, 0) == 0:
            return

        if g.last_path != vim.current.buffer.name:
            return

        if not g.last_pos:
            return

        if g.last_pos[0] != vim.current.window.cursor[0]:
            return

        if 1 < self.kinds.get(kind):
            self.ui_select()
            return True

        for i, tag in enumerate(self.taglist):
            if tag.kind == kind:
                self._goto(i)
                return True

    def goto_local_file(self):
        if self.tagname == g.last_tag:
            return

        for i, tag in enumerate(self.taglist):
            root = pyvim.get_cur_root()
            path = os.path.join(root, tag.file_path)
            if path == vim.current.buffer.name:
                self._goto(i)
                return True

    def goto(self, index = None):
        '不指定的情况下, 并且只一个纪录直接跳转'
        if self.num < 2:
            index = 0

        if None != index:
            self._goto(index)
            return

        '如果有对应的申明 p, 并且当前还在上一次跳转之后的地方. 尝试去申明'
        if self.goto_p():
            return

        if self.goto_local_file():
            return

        '如果不算 p(申明) 只有一个, 直接跳转到另一个'
        if self.num - self.kinds.get('prototype', 0) == 1:
            for i, tag in enumerate(self.taglist):
                if tag.kind == 'prototype':
                    continue
                self._goto(i)
                return

        self.ui_select()


@pyvim.cmd()
def Tag(tag = None):
    if not tag:
        tag = pyvim.current_word()

    root = pyvim.get_cur_root()
    if not root:
        pyvim.echoline('not in project path')
        return

    taglist, err = libtag.find_tag(root, tag)
    if not taglist:
        pyvim.echoline(err)
        return

    h = 'Tag %s' % tag
    history.history(h, cmd = h)

    frame = TagFrame(taglist)

    frame.goto()

@pyvim.cmd()
def TagBack():
    stack = TagStack()

    tag = stack.pop()

    if not tag:
        vim.command(" echo 'there is no tag in stack'")
        return 0

    tag.back()
    stack.refresh()


def refresh(iskernel = False):
    root = pyvim.get_cur_root()

    libtag.refresh(root, iskernel)

    vim.command("echo 'the ctags is ok'")

@pyvim.cmd()
def TagRefresh():
    refresh()


@pyvim.cmd()
def TagKernel():
    refresh(iskernel = True)
