from gi.repository import Gtk


@Gtk.Template(resource_path='/io/github/amit9838/mousam/shortcuts_dialog.ui')
class ShortcutsDialog(Gtk.ShortcutsWindow):
    __gtype_name__ = 'MousamShortcutsDialog'

    def __init__(self, parent):
        super().__init__()
        self.set_transient_for(parent)
