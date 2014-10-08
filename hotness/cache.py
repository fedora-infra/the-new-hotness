import threading
import dogpile.cache

# At import time, this can be used to markup cached functions, but it cannot be
# used to actually cache until it has been configured with a call to
# .configure()
cache = dogpile.cache.make_region()

# We just use this so two threads don't try to initialize the cache at the same
# time.  That would be embarrassing.
cache_lock = threading.Lock()
