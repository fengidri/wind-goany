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

def ctag(filename):
    tags = libtag.parse(filename)
    name = []
    linenu = []
    for t in tags:
        name.append(t.show)

        linenu.append(t.line_nu)
    return name, linenu

class tag_filter(object):
    INSTANCE = None
    def __init__(self):
        tag_filter.INSTANCE = self

        vim.command('update')
        tags_name, tags_lineno = ctag(vim.current.buffer.name)
        #tags.sort()
        self.win = Search(tags_name)
        self.tags_lineno = tags_lineno

        self.win.FREventBind("Search-Quit", self.quit)


    def quit(self, win, index):
        tag_filter.INSTANCE = None
        if None == index:
            return

        if index > -1:
            linenu = self.tags_lineno[index]
            if linenu:
                vim.current.window.cursor = (linenu + 1, 0)
                try:
    #                vim.command('%foldopen!')
                    vim.command('normal zz')
                except vim.error as e:
                    logging.error(e)

    def show(self):
        pyvim.log.error('call show')
        self.win.BFToggle()


def TagFilter():
    if not vim.current.buffer.name:
        return

    if tag_filter.INSTANCE:
        tag_filter.INSTANCE.show()
        return

    tag_filter()


if __name__ == "__main__":
    pass

