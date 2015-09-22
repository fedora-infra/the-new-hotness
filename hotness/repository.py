import logging
import subprocess

from hotness.cache import cache

log = logging.getLogger('fedmsg')

def get_version(package_name, yumconfig):
    nvr_dict = build_nvr_dict(yumconfig)
    try:
        version = nvr_dict[package_name]
    except KeyError:
        log.warn("Did not find %r in nvr_dict, forcing refresh" % package_name)
        force_cache_refresh(yumconfig)
        nvr_dict = build_nvr_dict(yumconfig)
        # This might still fail.. but we did the best we could.
        version = nvr_dict[package_name]
    return version


def force_cache_refresh(yumconfig):
    # First, invalidate our in-memory cache of the results
    cache.invalidate(hard=True)

    # But also ask yum/dnf to kill its on-disk cache
    cmdline = ["/usr/bin/yum",
               "--config", yumconfig,
               "clean",
               "all"]
    log.info("Running %r" % ' '.join(cmdline))
    cleanall = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
    (stdout, stderr) = cleanall.communicate()
    if stderr:
        log.warn(stderr)
    log.debug("Done with cache cleaning.")


@cache.cache_on_arguments()
def build_nvr_dict(yumconfig):
    cmdline = ["/usr/bin/repoquery",
               "--config", yumconfig,
               "--quiet",
               #"--archlist=src",
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

    log.info("Rebuilt nvr_dict with %r entries" % len(new_nvr_dict))

    return new_nvr_dict
