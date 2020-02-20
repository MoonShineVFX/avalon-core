import os
import sys
import errno
import importlib
import contextlib
#print("prepare Avalon Max Pipeline")

# sys.path.append(r'C:\Users\noflame\.p2\pool\plugins\org.python.pydev.core_6.4.3.201807050139\pysrc')
# import pydevd
# pydevd.settrace("192.168.1.35", suspend=True)
import MaxPlus as MP
from MaxPlus import NotificationCodes as NC
from MaxPlus import NotificationManager as NM
from MaxPlus import PathManager as PM
from MaxPlus import ActionFactory as AF

from pyblish import api as pyblish

from . import lib
from ..lib import logger
from .. import api, io, schema
from ..tools import workfiles
from ..vendor import six
from ..vendor.Qt import QtCore, QtWidgets

self = sys.modules[__name__]
self._menu_name = "avalonmax"  # Unique name of menu
self._events = dict()  # Registered callbacks
self._parent = None  # Main Window, it means 3dsMAX itself
self._ignore_lock = False

AVALON_CONTAINERS = ":AVALON_CONTAINERS"
logger.info("prepare Avalon Max Pipeline")


def install():
    '''config: module, get from AVALON_CONFIG'''

    self._menu_name = api.Session["AVALON_LABEL"]

    # print(type(config))
    # print(dir(config))
    # print("module name: %s" % (config.__name__))
    # print("module : %s" % (config.__file__))

    _register_callbacks()
    _register_events()
    _set_project()

    _install_menu()

    # register host
    pyblish.register_host("max")

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


def _system_starup(*args):
    api.emit('init', args)

    # run in command mode?

    # reference to 3dsMAX itself
    self._parent = MP.GetQMaxWindow()  # max2016 sp2
    _uninstall_menu()


def _file_post_open(*args):
    api.emit('open', args)


def _system_post_new(*args):
    api.emit('new', args)


def _file_pre_save(*args):
    api.emit('before_save', args)


def _file_post_save(*args):
    api.emit('save', args)


def _register_events():
    api.on("taskChanged", _on_task_changed)
    logger.info("Installed event callback for 'taskChanged'..")


def _set_project():
    pass


def _install_menu():
    from ..tools import (
        creator,
        loader,
        publish,
        cbloader,
        cbsceneinventory,
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

        act_set_Context = AF.Create(category_name, 'Set Context', lambda *args: contextmanager.show(parent=MP.GetQMaxMainWindow()))
        act_create = AF.Create(category_name, 'Create...', lambda *args: creator.show(parent=MP.GetQMaxMainWindow()))
        act_load = AF.Create(category_name, 'Load...', lambda *args: loader.show(parent=MP.GetQMaxMainWindow()))
        act_publish = AF.Create(category_name, 'Publish...', lambda *args: publish.show())
        act_manage = AF.Create(category_name, 'Manage...', lambda *args: cbsceneinventory.show(parent=MP.GetQMaxMainWindow()))
        
        
        context_mb.AddItem(act_set_Context)
        ava_mb.AddItem(act_create)
        ava_mb.AddItem(act_load)
        ava_mb.AddItem(act_publish)
        ava_mb.AddItem(act_manage)
        
        ava_menu = ava_mb.Create(MP.MenuManager.GetMainMenu())
        context_menu = context_mb.Create(ava_menu)

    QtCore.QTimer.singleShot(100, deferred)


def _uninstall_menu():
    if MP.MenuManager.MenuExists(self._menu_name):
        MP.MenuManager.UnregisterMenu(self._menu_name)

    context_menu_name = "{}, {}".format(api.Session["AVALON_ASSET"], api.Session["AVALON_TASK"])
    if MP.MenuManager.MenuExists(context_menu_name):
            MP.MenuManager.UnregisterMenu(context_menu_name)


def launch_workfiles_app(*args):
    workfiles.show(MP.Core.EvalMAXScript('maxfilepath').Get())


def find_host_config(config):
    try:
        config = importlib.import_module(config.__name__ + ".max")
    except ImportError as exc:
        if str(exc) != "No module name {}".format(config.__name__ + ".max"):
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

    pyblish.deregister_host("max")
    print("uninstall end")


def create(name, asset, family, options=None, data=None):
    """Create a new instance

    Associate nodes with a subset and family. These nodes are later
    validated, according to their `family`, and integrated into the
    shared environment, relative their `subset`.

    Data relative each family, along with default data, are imprinted
    into the resulting objectSet. This data is later used by extractors
    and finally asset browsers to help identify the origin of the asset.

    Arguments:
        name (str): Name of subset
        asset (str): Name of asset
        family (str): Name of family
        options (dict, optional): Additional options from GUI
        data (dict, optional): Additional data from GUI

    Raises:
        NameError on `subset` already exists
        KeyError on invalid dynamic property
        RuntimeError on host error

    Returns:
        Name of instance

    """

    print("create")


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
    pass


def load(Loader,
         representation,
         name=None,
         namespace=None,
         data=None):
    """Load asset via database

    Arguments:
        Loader (api.Loader): The loader to process in host Max.
        representation (dict, io.ObjectId or str): Address to representation
        name (str, optional): Use pre-defined name
        namespace (str, optional): Use pre-defined namespace
        data (dict, optional): Additional settings dictionary

    """
    print("load")

    assert representation is not None, "This is a bug"

    if isinstance(representation, (six.string_types, io.ObjectId)):
        representation = io.find_one({"_id": io.ObjectId(str(representation))})

    version, subset, asset, project = io.parenthood(representation)

    assert all([representation, version, subset, asset, project]), (
        "This is a bug"
    )

    context = {
        "project": project,
        "asset": asset,
        "subset": subset,
        "version": version,
        "representation": representation,
    }

    # Ensure data is a dictionary when no explicit data provided
    if data is None:
        data = dict()
    assert isinstance(data, dict), "Data must be a dictionary"

    name = name or subset["name"]
    namespace = namespace or lib.unique_namespace(
        asset["name"] + "_",
        prefix="_" if asset["name"][0].isdigit() else "",
        suffix="_",
    )

    # TODO(roy): add compatibility check, see `tools.cbloader.lib`

    Loader.log.info(
        "Running '%s' on '%s'" % (Loader.__name__, asset["name"])
    )


class Creator():
    pass


class Loader():
    pass


print("install Avalon Max Done")
