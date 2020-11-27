# -*- coding:utf-8 -*-
#    author    :   丁雪峰
#    time      :   2015-08-06 19:08:33
#    email     :   fengidri@yeah.net
#    version   :   1.0.1

import os
import pyvim
from frainui import Search
import vim
from . import libtag
import popup

def ctag(filename):
    tags = libtag.parse(filename)
    name = []
    linenu = []
    for t in tags:
        name.append(t.show)

        linenu.append(t.line_nu)
    return name, linenu

class tag_filter(object):
    def __init__(self):
        vim.command('update')

        tags_name, tags_lineno = ctag(vim.current.buffer.name)

        self.tags_lineno = tags_lineno
        self.tags_name = tags_name

        popup.PopupSearch(self.filter_cb, self.finish_cb)

    def filter_cb(self, words, bwords):
        self.active_index = None
        if not words:
            return self.tags_name

        self.active_index = []
        o = []

        for i,line in enumerate(self.tags_name):
            for w in words:
                if line.find(w) == -1:
                    break
            else:
                o.append(line)
                self.active_index.append(i)

        return o

    def finish_cb(self, ret):
        if ret < 0:
            return

        if self.active_index:
            ret = self.active_index[ret]

        linenu = self.tags_lineno[ret]
        if linenu:
            vim.current.window.cursor = (linenu + 1, 0)
            try:
                vim.command('normal zz')
            except vim.error as e:
                logging.error(e)


def TagFilter():
    if not vim.current.buffer.name:
        return

    tag_filter()


if __name__ == "__main__":
    pass

