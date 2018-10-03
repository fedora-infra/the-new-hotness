import copy
import logging

import bs4

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


def _parse_service_form(response):
    parsed = bs4.BeautifulSoup(response.text, "lxml")
    inputs = {}
    for child in parsed.form.find_all(name="input"):
        if child.attrs["type"] == "submit":
            continue
        inputs[child.attrs["name"]] = child.attrs["value"]
    return (parsed.form.attrs["action"], inputs)


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

    def search_by_homepage(self, name, homepage):
        url = "{0}/api/projects/?homepage={1}".format(self.base_url, homepage)
        _log.info("Looking for %r via %r" % (name, url))
        return self.send_request(url, verb="GET")

    def get_project_by_package(self, name):
        url = "{0}/api/project/Fedora/{1}".format(self.base_url, name)
        _log.info("Looking for %r via %r" % (name, url))
        data = self.send_request(url, verb="GET")
        if "error" in data:
            _log.warn(data.error)
            return None
        else:
            return data

    def update_url(self, project, homepage):
        if not self.is_logged_in:
            raise AnityaException("Could not add anitya project.  " "Not logged in.")
        idx = project["id"]
        url = self.base_url + "/project/%i/edit" % idx
        response = self._session.get(url)
        if not response.status_code == 200:
            code = response.status_code
            raise AnityaException("Couldn't get form to get " "csrf token %r" % code)
        soup = bs4.BeautifulSoup(response.text, "lxml")

        data = copy.copy(project)
        data["homepage"] = homepage
        data["csrf_token"] = soup.find(id="csrf_token").attrs["value"]
        response = self._session.post(url, data=data)

        if not response.status_code == 200:
            del data["csrf_token"]
            raise AnityaException(
                "Bad status code from anitya when "
                "updating project: %r.  Sent %r" % (response.status_code, data)
            )
        elif "Could not" in response.text:
            soup = bs4.BeautifulSoup(response.text, "lxml")
            err = "Unknown error updating project in anitya"
            # This is the css class on the error flash messages from anitya
            tags = soup.find_all(attrs={"class": "list-group-item-danger"})
            if tags:
                err = " ".join(tags[0].stripped_strings)
            raise AnityaException(err)

        _log.info("Successfully updated anitya url for %r" % data["name"])

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

    def map_new_package(self, name, project):
        if not self.is_logged_in:
            raise AnityaException("Could not add anitya project.  " "Not logged in.")

        idx = project["id"]
        url = self.base_url + "/project/%i/map" % idx
        response = self._session.get(url)
        if not response.status_code == 200:
            code = response.status_code
            raise AnityaException("Couldn't get form to get " "csrf token %r" % code)

        soup = bs4.BeautifulSoup(response.text, "lxml")
        csrf_token = soup.find(id="csrf_token").attrs["value"]
        data = dict(distro="Fedora", package_name=name, csrf_token=csrf_token)
        response = self._session.post(url, data=data)

        if not response.status_code == 200:
            # Hide this from stuff we republish to the bus
            del data["csrf_token"]
            raise AnityaException(
                "Bad status code from anitya when "
                "mapping package: %r.  Sent %r" % (response.status_code, data)
            )
        elif "Could not" in response.text:
            soup = bs4.BeautifulSoup(response.text, "lxml")
            err = "Unknown error mapping package in anitya"
            # This is the css class on the error flash messages from anitya
            tags = soup.find_all(attrs={"class": "list-group-item-danger"})
            if tags:
                err = " ".join(tags[0].stripped_strings)
            raise AnityaException(err)

        _log.info("Successfully mapped %r in anitya" % name)

    def add_new_project(self, name, homepage):
        if not self.is_logged_in:
            raise AnityaException("Could not add anitya project.  " "Not logged in.")

        data = dict(
            name=name,
            homepage=homepage,
            distro="Fedora",
            package_name=name,
            backend=determine_backend(name, homepage),
        )

        # It's not always the case that these need removed, but often
        # enough...
        for prefix in prefixes:
            if data["name"].startswith(prefix):
                data["name"] = data["name"][len(prefix) :]

        # For these, we can get a pretty good guess at the upstream name
        for guess in easy_guesses:
            if data["backend"] == guess:
                data["name"] = data["homepage"].strip("/").split("/")[-1]
                break

        if data["backend"] == "github" and "github.com" in data["homepage"]:
            data["version_url"] = data["homepage"]

        url = self.base_url + "/project/new"
        response = self._session.get(url)

        if not response.status_code == 200:
            code = response.status_code
            raise AnityaException("Couldn't get form to get csrf " "token %r" % code)

        soup = bs4.BeautifulSoup(response.text, "lxml")
        data["csrf_token"] = soup.find(id="csrf_token").attrs["value"]

        response = self._session.post(url, data=data)

        if not response.status_code == 200:
            # Hide this from stuff we republish to the bus
            del data["csrf_token"]
            raise AnityaException(
                "Bad status code from anitya when "
                "adding project: %r.  Sent %r" % (response.status_code, data)
            )
        elif "Could not" in response.text:
            soup = bs4.BeautifulSoup(response.text, "lxml")
            err = "Unknown error adding project to anitya"
            # This is the css class on the error flash messages from anitya
            tags = soup.find_all(attrs={"class": "list-group-item-danger"})
            if tags:
                err = " ".join(tags[0].stripped_strings)
            raise AnityaException(err)

        _log.info("Successfully added %r to anitya" % data["name"])
