'''
Created on 2020-02-27

@author: noflame.lin
'''
import os
import MaxPlus as MP
import pymxs
rt = pymxs.runtime


def open_file(filename):
    rt.loadMaxFile(filename, allowPrompts=True)
    return True


def save_file(filename):
    rt.saveMaxFile(filename, clearNeedSaveFlag=True)


def current_file():
    maxfile = rt.maxfilepath + rt.maxfilename
    return maxfile or None


def has_unsaved_changes():
    return rt.getSaveRequired()


def file_extensions():
    return ['.max']


def work_root(session):
    work_dir = session["AVALON_WORKDIR"]
    scene_dir = session.get("AVALON_SCENEDIR")
    if scene_dir:
        return os.path.join(work_dir, scene_dir)
    else:
        return work_dir
        