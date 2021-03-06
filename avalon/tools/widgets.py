import logging
import re

from . import lib

from .models import AssetModel, TasksModel, RecursiveSortFilterProxyModel
from .views import DeselectableTreeView
from ..vendor import qtawesome, qargparse
from ..vendor.Qt import QtWidgets, QtCore, QtGui

from .. import style
from .. import io

log = logging.getLogger(__name__)


class AssetWidget(QtWidgets.QWidget):
    """A Widget to display a tree of assets with filter

    To list the assets of the active project:
        >>> # widget = AssetWidget()
        >>> # widget.refresh()
        >>> # widget.show()

    """

    assets_refreshed = QtCore.Signal()   # on model refresh
    selection_changed = QtCore.Signal()  # on view selection change
    current_changed = QtCore.Signal()    # on view current index change

    def __init__(self, parent=None):
        super(AssetWidget, self).__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Tree View
        model = AssetModel()
        proxy = RecursiveSortFilterProxyModel()
        proxy.setSourceModel(model)
        proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        view = DeselectableTreeView()
        view.setIndentation(15)
        view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        view.setHeaderHidden(True)
        view.setModel(proxy)

        # Header
        header = QtWidgets.QHBoxLayout()

        icon = qtawesome.icon("fa.refresh", color=style.colors.light)
        refresh = QtWidgets.QPushButton(icon, "")
        refresh.setToolTip("Refresh items")

        filter = QtWidgets.QLineEdit()
        filter.textChanged.connect(proxy.setFilterFixedString)
        filter.setPlaceholderText("Filter assets..")

        header.addWidget(filter)
        header.addWidget(refresh)

        # Layout
        layout.addLayout(header)
        layout.addWidget(view)

        # Signals/Slots
        selection = view.selectionModel()
        selection.selectionChanged.connect(self.selection_changed)
        selection.currentChanged.connect(self.current_changed)
        refresh.clicked.connect(self.refresh)

        self.refreshButton = refresh
        self.model = model
        self.proxy = proxy
        self.view = view

    def _refresh_model(self):
        with lib.preserve_states(
            self.view, column=0, role=self.model.ObjectIdRole
        ):
            self.model.refresh()

        self.assets_refreshed.emit()

    def refresh(self):
        self._refresh_model()

    def get_active_asset(self):
        """Return the asset item of the current selection."""
        current = self.view.currentIndex()
        return current.data(self.model.ItemRole)

    def get_active_asset_document(self):
        """Return the asset document of the current selection."""
        current = self.view.currentIndex()
        return current.data(self.model.DocumentRole)

    def get_active_index(self):
        return self.view.currentIndex()

    def get_selected_assets(self):
        """Return the documents of selected assets."""
        selection = self.view.selectionModel()
        rows = selection.selectedRows()
        assets = [row.data(self.model.DocumentRole) for row in rows]

        # NOTE: skip None object assumed they are silo (backwards comp.)
        return [asset for asset in assets if asset]

    def update_selected_assets(self):
        """Update selected assets' document from database

        Fetch documents that have been written into database by user, and
        update model.
        Documents that have changed should be those being selected.

        """
        selection = self.view.selectionModel()
        rows = selection.selectedRows()
        indexes = [row.model().mapToSource(row) for row in rows]
        self.model.update_documents(indexes)

    def select_assets(self, assets, expand=True, key="name"):
        """Select assets by item key.

        Args:
            assets (list): List of asset values that can be found under
                specified `key`
            expand (bool): Whether to also expand to the asset in the view
            key (string): Key that specifies where to look for `assets` values

        Returns:
            None

        Default `key` is "name" in that case `assets` should contain single
        asset name or list of asset names. It is recommended to use "_id" key
        instead of name. In that case `assets` must contain `ObjectId` objects.
        It is assumed that each value in `assets` is found only once.
        On multiple matches only the first found will be selected.
        """

        if not isinstance(assets, (tuple, list)):
            assets = [assets]

        # convert to list - tuple cant be modified
        assets = set(assets)

        # Clear selection
        selection_model = self.view.selectionModel()
        selection_model.clearSelection()

        # Select
        mode = selection_model.Select | selection_model.Rows
        for index in lib.iter_model_rows(
            self.proxy, column=0, include_root=False
        ):
            # stop iteration if there are no assets to process
            if not assets:
                break

            value = index.data(self.model.ItemRole).get(key)
            if value not in assets:
                continue

            # Remove processed asset
            assets.discard(value)

            selection_model.select(index, mode)
            if expand:
                # Expand parent index
                self.view.expand(self.proxy.parent(index))

            # Set the currently active index
            self.view.setCurrentIndex(index)


class TaskWidget(QtWidgets.QWidget):
    # (TODO) Merge `workfiles.app.TasksWidget`

    selection_changed = QtCore.Signal()  # on view selection change

    def __init__(self, parent=None):
        super(TaskWidget, self).__init__(parent=parent)

        model = TasksModel()

        view = QtWidgets.QTreeView()
        view.setIndentation(0)
        view.setModel(model)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(view)

        # Signals/Slots
        selection = view.selectionModel()
        selection.selectionChanged.connect(self.selection_changed)

        self.setContentsMargins(0, 0, 0, 0)

        self.model = model
        self.view = view

    def set_assets(self, asset_docs):
        """Update task model with view state preserved"""
        with lib.preserve_states(self.view, column=0):
            self.model.set_assets(asset_docs)

    def get_selected_tasks(self):
        """Returns a list of selected tasks' names"""
        selection = self.view.selectionModel()
        tasks = [row.data() for row in selection.selectedRows()]
        return tasks


class OptionalMenu(QtWidgets.QMenu):
    """A subclass of `QtWidgets.QMenu` to work with `OptionalAction`

    This menu has reimplemented `mouseReleaseEvent`, `mouseMoveEvent` and
    `leaveEvent` to provide better action hightlighting and triggering for
    actions that were instances of `QtWidgets.QWidgetAction`.

    """

    def mouseReleaseEvent(self, event):
        """Emit option clicked signal if mouse released on it"""
        active = self.actionAt(event.pos())
        if active and active.use_option:
            option = active.widget.option
            if option.is_hovered(event.globalPos()):
                option.clicked.emit()
        super(OptionalMenu, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """Add highlight to active action"""
        active = self.actionAt(event.pos())
        for action in self.actions():
            action.set_highlight(action is active, event.globalPos())
        super(OptionalMenu, self).mouseMoveEvent(event)

    def leaveEvent(self, event):
        """Remove highlight from all actions"""
        for action in self.actions():
            action.set_highlight(False)
        super(OptionalMenu, self).leaveEvent(event)


class OptionalAction(QtWidgets.QWidgetAction):
    """Menu action with option box

    A menu action like Maya's menu item with option box, implemented by
    subclassing `QtWidgets.QWidgetAction`.

    """

    def __init__(self, label, icon, use_option, parent):
        super(OptionalAction, self).__init__(parent)
        self.label = label
        self.icon = icon
        self.use_option = use_option
        self.option_tip = ""
        self.optioned = False

    def createWidget(self, parent):
        widget = OptionalActionWidget(self.label, parent)
        self.widget = widget

        if self.icon:
            widget.setIcon(self.icon)

        if self.use_option:
            widget.option.clicked.connect(self.on_option)
            widget.option.setToolTip(self.option_tip)
        else:
            widget.option.setVisible(False)

        return widget

    def set_option_tip(self, options):
        sep = "\n\n"
        mak = (lambda opt: opt["name"] + " :\n    " + opt["help"])
        self.option_tip = sep.join(mak(opt) for opt in options)

    def on_option(self):
        self.optioned = True

    def set_highlight(self, state, global_pos=None):
        body = self.widget.body
        option = self.widget.option

        role = QtGui.QPalette.Highlight if state else QtGui.QPalette.Window
        body.setBackgroundRole(role)
        body.setAutoFillBackground(state)

        if not self.use_option:
            return

        state = option.is_hovered(global_pos)
        role = QtGui.QPalette.Highlight if state else QtGui.QPalette.Window
        option.setBackgroundRole(role)
        option.setAutoFillBackground(state)


class OptionalActionWidget(QtWidgets.QWidget):
    """Main widget class for `OptionalAction`"""

    def __init__(self, label, parent=None):
        super(OptionalActionWidget, self).__init__(parent)

        body = QtWidgets.QWidget()
        body.setStyleSheet("background: transparent;")

        icon = QtWidgets.QLabel()
        label = QtWidgets.QLabel(label)
        option = OptionBox(body)

        icon.setFixedSize(24, 16)
        option.setFixedSize(30, 30)

        layout = QtWidgets.QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(icon)
        layout.addWidget(label)
        layout.addSpacing(6)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 1, 2, 1)
        layout.setSpacing(0)
        layout.addWidget(body)
        layout.addWidget(option)

        body.setMouseTracking(True)
        label.setMouseTracking(True)
        option.setMouseTracking(True)
        self.setMouseTracking(True)
        self.setFixedHeight(32)

        self.icon = icon
        self.label = label
        self.option = option
        self.body = body

        # (NOTE) For removing ugly QLable shadow FX when highlighted in Nuke.
        #   See https://stackoverflow.com/q/52838690/4145300
        label.setStyle(QtWidgets.QStyleFactory.create("Plastique"))

    def setIcon(self, icon):
        pixmap = icon.pixmap(16, 16)
        self.icon.setPixmap(pixmap)


class OptionBox(QtWidgets.QLabel):
    """Option box widget class for `OptionalActionWidget`"""

    clicked = QtCore.Signal()

    def __init__(self, parent):
        super(OptionBox, self).__init__(parent)

        self.setAlignment(QtCore.Qt.AlignCenter)

        icon = qtawesome.icon("fa.sticky-note-o", color="#c6c6c6")
        pixmap = icon.pixmap(18, 18)
        self.setPixmap(pixmap)

        self.setStyleSheet("background: transparent;")

    def is_hovered(self, global_pos):
        if global_pos is None:
            return False
        pos = self.mapFromGlobal(global_pos)
        return self.rect().contains(pos)


class OptionDialog(QtWidgets.QDialog):
    """Option dialog shown by option box"""

    def __init__(self, parent=None):
        super(OptionDialog, self).__init__(parent)
        self.setModal(True)
        self._options = dict()

    def create(self, options):
        parser = qargparse.QArgumentParser(arguments=options)

        decision = QtWidgets.QWidget()
        accept = QtWidgets.QPushButton("Accept")
        cancel = QtWidgets.QPushButton("Cancel")

        layout = QtWidgets.QHBoxLayout(decision)
        layout.addWidget(accept)
        layout.addWidget(cancel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(parser)
        layout.addWidget(decision)

        accept.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        parser.changed.connect(self.on_changed)

    def on_changed(self, argument):
        self._options[argument["name"]] = argument.read()

    def parse(self):
        return self._options.copy()


class NameValidator(QtGui.QRegExpValidator):

    invalid = QtCore.Signal(set, str)
    pattern = "^[a-zA-Z0-9_.]*$"

    def __init__(self):
        reg = QtCore.QRegExp(self.pattern)
        super(NameValidator, self).__init__(reg)

    def validate(self, input, pos):
        results = super(NameValidator, self).validate(input, pos)
        if results[0] == self.Invalid:
            self.invalid.emit(*self.invalid_chars(input))
        return results

    def invalid_chars(self, input):
        invalid = set()
        re_valid = re.compile(self.pattern)
        for char in str(input):
            if char in [" ", "\n", "\t"]:
                invalid.add(char)
                continue
            if not re_valid.match(char):
                invalid.add(char)
        return invalid, input


class NameValidEdit(QtWidgets.QLineEdit):

    report = QtCore.Signal(str)
    colors = {
        "empty": (QtGui.QColor("#78879b"), ""),
        "exists": (QtGui.QColor("#4E76BB"), "border-color: #4E76BB;"),
        "new": (QtGui.QColor("#7AAB8F"), "border-color: #7AAB8F;"),
    }

    def __init__(self, *args, **kwargs):
        super(NameValidEdit, self).__init__(*args, **kwargs)

        validator = NameValidator()
        self.setValidator(validator)
        self.setToolTip("Only alphanumeric characters (A-Z a-z 0-9), "
                        "'_' and '.' are allowed.")

        self._status_color = self.colors["empty"][0]

        anim = QtCore.QPropertyAnimation()
        anim.setTargetObject(self)
        anim.setPropertyName(b"status_color")
        anim.setEasingCurve(QtCore.QEasingCurve.InCubic)
        anim.setDuration(500)
        anim.setStartValue(QtGui.QColor("#C84747"))  # `Invalid` status color
        anim.setEndValue(QtGui.QColor("#78879b"))  # Default color
        self.animation = anim

        validator.invalid.connect(self.on_invalid)

    def on_invalid(self, invalid, input):
        message = "Invalid character: %s" % ", ".join(repr(c) for c in invalid)
        self.report.emit(message)
        self.animation.stop()
        self.animation.start()
        # For improving UX in case like pasting invalid string, set cleaned
        # text back to widget, instead of nothing happens by default.
        text = self.text()
        for c in invalid:
            text = text.replace(c, "")
        self.setText(text)

    def indicate(self, status):
        """Indicate the status of current input via animation

        `NameValidEdit` has three states:

            "empty": Empty input
            "exists": Input value already exists
            "new": Input value is new

        And each state has a corresponding border color.

        Args:
            status (str): Status name

        """
        qcolor, style = self.colors[status]
        self.animation.setEndValue(qcolor)
        self.setStyleSheet(style)

    def _get_status_color(self):
        return self._status_color

    def _set_status_color(self, color):
        self._status_color = color
        self.setStyleSheet("border-color: %s;" % color.name())

    status_color = QtCore.Property(QtGui.QColor,
                                   _get_status_color,
                                   _set_status_color)
