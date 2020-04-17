'''
Created on 2020-02-27

@author: noflame.lin
'''
import os
from avalon import Session
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


def work_root():    
    work_dir = Session["AVALON_WORKDIR"]
    scene_dir = Session.get("AVALON_SCENEDIR")
    if scene_dir:
        return os.path.join(work_dir, scene_dir)
    else:
        return work_dir