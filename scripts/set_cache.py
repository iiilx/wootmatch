import memcache

cache = memcache.Client(['127.0.0.1:11211'])
cache.set('updates_allowed','1')


