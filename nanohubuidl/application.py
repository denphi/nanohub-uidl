import os
from .handlers import *
from notebook.base.handlers import IPythonHandler, FilesRedirectHandler, path_regex
from notebook.utils import url_path_join


DEFAULT_STATIC_FILES_PATH = os.path.join(os.path.dirname(__file__), "static")
DEFAULT_TEMPLATE_FILES_PATH = os.path.join(os.path.dirname(__file__), "templates")

    

class UIDLmode(object):
    """Notebook handler registration helper."""

    # The name of the extension.
    name = "nanohubuidl"

    # Te url that your extension will serve its homepage.
    extension_url = "/uidl"

    # Should your extension expose other server extensions when launched directly?
    load_other_extensions = True

    # Local path to static files directory.
    static_paths = [DEFAULT_STATIC_FILES_PATH]

    # Local path to templates directory.
    template_paths = [DEFAULT_TEMPLATE_FILES_PATH]

    @staticmethod
    def handlers(baseurl):
        return [
                (url_path_join(baseurl, r"/uidl/([A-Z]*.HTML)/local/(.*)"), UIDLLocalHandler),
                (url_path_join(baseurl, r"/uidl/([A-Z]*.HTML)/redirect/(.*)"), UIDLRedirectHandler),
                (url_path_join(baseurl, r"/uidl/([A-Z]*.HTML)/direct/(.*)"), UIDLHandler),
            ]
        
    def initialize_handlers(self):
        """Initialize handlers."""
        self.handlers.extend(UIDLmode.handlers(""))

    def initialize_settings(self):
        """Initialize settings."""
        self.log.info(f"Config {self.config}")

main = launch_new_instance = None
