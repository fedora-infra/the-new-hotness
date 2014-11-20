import logging
import subprocess

from hotness.cache import cache

log = logging.getLogger('fedmsg')

def get_version(package_name, yumconfig):
    nvr_dict = build_nvr_dict(yumconfig)
    return nvr_dict[package_name]


@cache.cache_on_arguments()
def build_nvr_dict(yumconfig):
    cmdline = ["/usr/bin/repoquery",
               "--config", yumconfig,
               "--quiet",
               "--archlist=src",
               "--all",
               "--qf",
               "%{name}\t%{version}\t%{release}"]

    log.info("Running %r" % ' '.join(cmdline))
    repoquery = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
    (stdout, stderr) = repoquery.communicate()
    log.debug("Done with repoquery.")

    if stderr:
        log.warn(stderr)

    new_nvr_dict = {}
    for line in stdout.split("\n"):
        line = line.strip()
        if line:
            name, version, release = line.split("\t")
            new_nvr_dict[name] = (version, release)

    return new_nvr_dict
