import logging
import subprocess

from hotness.cache import cache

log = logging.getLogger('fedmsg')

def get_version(package_name, repoid):
    nvr_dict = build_nvr_dict(repoid)
    return nvr_dict[package_name]


@cache.cache_on_arguments()
def build_nvr_dict(repoid):
    cmdline = ["/usr/bin/repoquery",
               "--quiet",
               "--archlist=src",
               "--all",
               "--qf",
               "%{name}\t%{version}\t%{release}"]

    if repoid:
        cmdline.append('--repoid=%s' % repoid)

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
