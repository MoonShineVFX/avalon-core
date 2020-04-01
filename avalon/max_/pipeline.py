import os
import sys
import errno
import importlib
import contextlib

# print("prepare Avalon Max Pipeline")

from pyblish import api as pyblish

from . import lib, workio
from ..lib import logger
from .. import api, io, schema
from ..vendor import six
from ..vendor.Qt import QtCore, QtWidgets
from ..pipeline import AVALON_CONTAINER_ID
from ..pipeline import create
from ..pipeline import load
# from ..pipeline import update
# from ..pipeline import remove
from ..tools import workfiles
import MaxPlus as MP
from MaxPlus import NotificationCodes as NC
from MaxPlus import NotificationManager as NM
from MaxPlus import PathManager as PM
from MaxPlus import ActionFactory as AF
import pymxs

Ev_Mxs = MP.Core.EvalMAXScript
Ex_Mxs = MP.Core.ExecuteMAXScript
rt = pymxs.runtime

self = sys.modules[__name__]
self._menu_name = "avalonmax"  # Unique name of menu
self._events = dict()  # Registered callbacks
self._ignore_lock = False
try:
    self._parent = MP.GetQMaxMainWindow()  # Main Window, it means 3dsMAX itself
except:
    self._parent = MP.GetQMaxWindow()
AVALON_CONTAINERS = "AVALON_CONTAINERS"
AVALON_CONTAINERS_NODE = None
logger.info("prepare Avalon Max Pipeline")


def install():
    '''config: module, get from AVALON_CONFIG'''

    self._menu_name = api.Session["AVALON_LABEL"]
    
    _register_callbacks()
    _register_events()
    _set_project()

    _install_menu()

    # register host
    pyblish.register_host("max_")


def _register_callbacks():
    '''
    # reg dcc change call_back make avalon can reactorto those signal
        # maya                    max
        # _on_max_initialized -> SystemStartup
        # _on_scene_open      -> FilePostOpen
        # _on_scene_new       -> SystemPostNew
        # _before_scene_save  -> FilePreSave
        # _on_scene_save      -> FilePostSave
    '''
    # remove pre-install call_back
    for _, handle in self._events.items():
        try:
            NM.Unregister(handle)
        except Exception:
            pass
    self._events.clear()

    # install callback
    self._events[_system_starup] = NM.Register(NC.SystemStartup, _system_starup)
    self._events[_file_post_open] = NM.Register(NC.FilePostOpen, _file_post_open)
    self._events[_system_post_new] = NM.Register(NC.SystemPostNew, _system_post_new)
    self._events[_file_pre_save] = NM.Register(NC.FilePreSave, _file_pre_save)
    self._events[_file_post_save] = NM.Register(NC.FilePostSave, _file_post_save)

    logger.info("Installed event handler SystemPostNew..")
    logger.info("Installed event handler FilePreSave..")
    logger.info("Installed event handler SystemPostNew..")
    logger.info("Installed event handler SystemStartup..")
    logger.info("Installed event handler FilePostOpen..")


def _register_events():
    api.on("taskChanged", _on_task_changed)
    logger.info("Installed event callback for 'taskChanged'..")


def _set_project():
    '''setting current work folder to max project'''
    pass


def _system_starup(*args):
    api.emit('init', args)

    # run in command mode?

    # reference to 3dsMAX itself
    try:
        self._parent = MP.GetQMaxWindow()  # max2016 sp2
    except:
        self._parent = MP.GetQMaxMainWindow()  # max2018.4
    _uninstall_menu()


def _file_post_open(*args):
    api.emit('open', args)


def _system_post_new(*args):
    api.emit('new', args)


def _file_pre_save(*args):
    api.emit('before_save', args)


def _file_post_save(*args):
    api.emit('save', args)


def _install_menu():
    from ..tools import (
        projectmanager,
        creator,
        loader,
        publish,
        sceneinventory,
        contextmanager
    )
    
    _uninstall_menu()

    def deferred():
        print("building menu")
        ava_menu_name = self._menu_name
        category_name = api.Session["AVALON_LABEL"]
        context_menu_name = "{}, {}".format(api.Session["AVALON_ASSET"], api.Session["AVALON_TASK"])
        ava_mb = MP.MenuBuilder(ava_menu_name)
        context_mb = MP.MenuBuilder(context_menu_name)

        act_projectmanager = AF.Create(category_name, 'Project Manager', lambda *args: projectmanager.show(parent=self._parent))
        act_set_Context = AF.Create(category_name, 'Set Context', lambda *args: contextmanager.show(parent=self._parent))
        act_create = AF.Create(category_name, 'Create...', lambda *args: creator.show(parent=self._parent))
        act_load = AF.Create(category_name, 'Load...', lambda *args: loader.show(parent=self._parent))
        act_publish = AF.Create(category_name, 'Publish...', lambda *args: publish.show())
        act_manage = AF.Create(category_name, 'Manage...', lambda *args: sceneinventory.show(parent=self._parent))
        act_workfiles = AF.Create(category_name, 'Work file...', lambda *args: launch_workfiles_app(self._parent))
        
        context_mb.AddItem(act_set_Context)
        ava_mb.AddItem(act_projectmanager)
        ava_mb.AddItem(act_create)
        ava_mb.AddItem(act_load)
        ava_mb.AddItem(act_publish)
        ava_mb.AddItem(act_manage)
        ava_mb.AddItem(act_workfiles)
        
        ava_menu = ava_mb.Create(MP.MenuManager.GetMainMenu())
        context_menu = context_mb.Create(ava_menu)
        
        # run script plugin
        avalon_core_folder = os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)))
        base_ms = avalon_core_folder + '\\setup\max\\avalon_base.ms'
        rt.executeScriptFile(base_ms)

    QtCore.QTimer.singleShot(100, deferred)


def _uninstall_menu():
    if MP.MenuManager.MenuExists(self._menu_name):
        MP.MenuManager.UnregisterMenu(self._menu_name)

    context_menu_name = "{}, {}".format(api.Session["AVALON_ASSET"], api.Session["AVALON_TASK"])
    if MP.MenuManager.MenuExists(context_menu_name):
            MP.MenuManager.UnregisterMenu(context_menu_name)


def launch_workfiles_app(*args):
    workfiles.show(workio.work_root(api.Session), parent=args[0])


def find_host_config(config):
    try:
        config = importlib.import_module(config.__name__ + ".max_")
    except ImportError as exc:
        if str(exc) != "No module name {}".format(config.__name__ + ".max_"):
            raise
        config = None

    return config


def _on_task_changed(*args):
    # update menu task label
    for arg in args:
        print('{}:{}'.format(type(arg), arg))
    _update_menu_task_label()


def _update_menu_task_label():
    """Update the task label in Avalon menu to current session"""

    object_name = "{}|currentContext".format(self._menu_name)
    print('self._menu_name:{}'.format(self._menu_name))
    # to be continue


def uninstall(config):
    print("uninstall start")
    config = find_host_config(config)
    if hasattr(config, "uninstall"):
        config.uninstall()

    _uninstall_menu()

    pyblish.deregister_host("max_")
    print("uninstall end")


def containerise(name,
                 namespace,
                 nodes,
                 context,
                 loader=None,
                 suffix="CON"):
    """Bundle `nodes` into an assembly and imprint it with metadata

    Containerisation enables a tracking of version, author and origin
    for loaded assets.

    Arguments:
        name (str): Name of resulting assembly
        namespace (str): Namespace under which to host container
        nodes (list): Long names of nodes to containerise
        context (dict): Asset information
        loader (str, optional): Name of loader used to produce this container.
        suffix (str, optional): Suffix of container, defaults to `_CON`.

    Returns:
        container (AvalonContainer): container assembly

    """

    ava_con.ava_name = name
    ava_con.id = AVALON_CONTAINER_ID
    ava_con.loader = str(loader)
    ava_con.representation = context["representation"]["_id"]
    ava_con.avalon_nodes = nodes

    return ava_con


def update(container, version=-1):
    """Update `container` to `version`

    This function relies on a container being referenced. At the time of this
    writing, all assets - models, rigs, animations, shaders - are referenced
    and should pose no problem. But should there be an asset that isn't
    referenced then this function will need to see an update.

    Arguments:
        container (avalon-core:container-1.0): Container to update,
            from `host.ls()`.
        version (int, optional): Update the container to this version.
            If no version is passed, the latest is assumed.

    """
    print("update")


def remove(container):
    """Remove an existing `container` from Maya scene

    Arguments:
        container (avalon-core:container-1.0): Which container
            to remove from scene.

    """
    print("remove")
    print(container)
    print(dir(container))


def publish():
    """Shorthand to publish from within host"""
    import pyblish.util
    return pyblish.util.publish()


def ls():
    """List containers from active Max scene

    This is the host-equivalent of api.ls(), but instead of listing
    assets on disk, it lists assets already loaded in Max; once loaded
    they are called 'containers'
    """
    containers = [obj for obj in rt.helpers]
    condi = lambda o:rt.classOf(o) == rt.AvalonContainer
    containers = filter(condi, containers)
    return containers


class Creator(api.Creator):
    
    def _create_ava_set_object(self):
        org_lay = rt.LayerManager.current
        ava_lay = rt.LayerManager.getLayerFromName('avalon')
        if not ava_lay:
            ava_lay = rt.LayerManager.newLayerFromName('avalon')
        ava_lay.current = True
        # create layer for avalon
        
        inst = rt.AvalonSet()
        attrs = ['cross', 'box', 'centermarker', 'axistripod']
        for attr in attrs:
            rt.execute('$' + inst.name + '[4][1].' + attr + '=off')
        org_lay.current = True
        return inst

    def process(self):
        inst = self._create_ava_set_object()

        if (self.options or {}).get("useSelection"):
            inst_node = MP.INode.GetINodeByName(inst.name)
            avalon_nodes = inst_node.BaseObject.ParameterBlock.GetParamByName('avalon_nodes')
            
            sel_objs = [obj for obj in rt.selection]
            for obj in sel_objs:
                class_ = rt.classOf(obj) 
                if  class_ == rt.AvalonSet or class_ == rt.AvalonContainer:
                    rt.deselect(obj)
            # Exclude AvalonSet and AvalonContainer object

            new_list = MP.INodeList()
            for node in MP.SelectionManager.Nodes:
                new_list.Append(node)

            avalon_nodes.Value = new_list
        # inst = rt.newTrackViewNode(AVALON_CONTAINERS_NODE, self.name)

        inst.ava_id = self.data["id"] = "pyblish.avalon.instance"
        inst.family = self.data["family"]
        inst.asset = self.data["asset"]
        inst.subset = self.data["subset"]
        inst.active = self.data["active"]
        
        inst.name = rt.uniqueName(inst.subset)

        return inst


class Loader(api.Loader):
    hosts = ["max_"]

    def __init__(self, context):
        super(Loader, self).__init__(context)
        self.fname = self.fname.replace(
            api.registered_root(), "$AVALON_PROJECTS"
        )


print("install Avalon Max Done")
