import logging

from fedora.client import AuthError
from fedora.client import OpenIdBaseClient


ANITYA_URL = "https://release-monitoring.org/"


_log = logging.getLogger(__name__)


backends = {
    "ftp.debian.org": "Debian project",
    "drupal.org": "Drupal7",
    "freecode.com": "Freshmeat",
    "github.com": "GitHub",
    "download.gnome.org": "GNOME",
    "ftp.gnu.org": "GNU project",
    "code.google.com": "Google code",
    "hackage.haskell.org": "Hackage",
    "launchpad.net": "launchpad",
    "npmjs.org": "npmjs",
    "npmjs.com": "npmjs",
    "packagist.org": "Packagist",
    "pear.php.net": "PEAR",
    "pecl.php.net": "PECL",
    "pypi.python.org": "PyPI",
    "pypi.org": "PyPI",
    "rubygems.org": "Rubygems",
    "sourceforge.net": "Sourceforge",
}

prefixes = {
    "drupal7-": None,
    "drupal6-": None,
    "ghc-": None,
    "nodejs-": None,
    "php-pear-": None,
    "php-pecl-": None,
    "php-": None,
    "python-": None,
    "rubygem-": "Rubygems",
}

easy_guesses = [
    "Debian project",
    "Drupal7",
    "Freshmeat",
    "GitHub",
    "GNOME",
    "GNU project",
    "Google code",
    "Hackage",
    "launchpad",
    "npmjs",
    "PEAR",
    "PECL",
    "PyPI",
    "Rubygems",
]


class AnityaException(Exception):
    pass


class AnityaAuthException(AnityaException, AuthError):
    pass


def determine_backend(project_name, project_homepage):
    """
    Determine the Anitya backend to use for a given project name and homepage.

    This is not a 100% accurate process. If the ``project_name`` has a prefix with
    a backend associated with it in :data:`prefixes`, that is preferred. Otherwise,
    the homepage is checked to see if the host is mapped to known backend.

    Args:
        project_name (str): The project's name, possibly containing the RPM prefix
            (e.g. ``python-`` for Python packages).
        project_homepage (str): The project's homepage URL.

    Returns:
        str: The backend name to use with Anitya.

    Raises:
        AnityaException: When the backend could not be determined.
    """
    for prefix, backend in prefixes.items():
        if project_name.startswith(prefix) and backend is not None:
            return backend

    for target, backend in backends.items():
        if target in project_homepage:
            return backend

    err = (
        "the-new-hotness was unable to automatically determine the Anitya backend "
        "to use with the {name} ({homepage}) project. Please search {anitya_url} "
        "for this project. If it already exists, ensure there is a distribution "
        "mapping for Fedora. If it does not already exist, please create the "
        "project manually. Doing so enables us to automatically notify package "
        "maintainers when new versions are released."
    ).format(name=project_name, homepage=project_homepage, anitya_url=ANITYA_URL)
    raise AnityaException(err)


class Anitya(OpenIdBaseClient):
    def __init__(self, url=ANITYA_URL, insecure=False):
        super(Anitya, self).__init__(
            base_url=url,
            login_url=url + "/login/fedora",
            useragent="The New Hotness",
            debug=False,
            insecure=insecure,
            openid_insecure=insecure,
            username=None,  # We supply this later
            cache_session=True,
            retries=7,
            timeout=120,
            retry_backoff_factor=0.3,
        )

    @property
    def is_logged_in(self):
        response = self._session.get(self.base_url)
        return "logout" in response.text

    def force_check(self, project):
        """ Force anitya to check for a new upstream release. """
        idx = project["id"]
        url = "%s/api/version/get" % self.base_url
        data = self.send_request(url, verb="POST", data=dict(id=idx))

        if "error" in data:
            _log.warning("Anitya error: %r" % data["error"])
        else:
            _log.info(
                "Check yielded upstream version %s for %s"
                % (data["version"], data["name"])
            )
