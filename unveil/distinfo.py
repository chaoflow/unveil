import ConfigParser
import functools
import itertools
import json
import os


SCRIPT_TEMPLATE = """
#!%%(python)s

# -*- coding: utf-8 -*-
import re
import sys

from %(module)s import %(func)s

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(%(func)s())
""".lstrip()


def cached_property(function):
    cache_name = '__' + function.__name__

    @functools.wraps(function)
    def caching(self):
        try:
            return getattr(self, cache_name)
        except AttributeError:
            rv = function(self)
            setattr(self, cache_name, rv)
            return rv

    return property(caching)


class Distribution(object):
    def __init__(self, distinfopath):
        self.distinfopath = os.path.abspath(distinfopath)

    @cached_property
    def datadir(self):
        return self.distinfopath.replace('.dist-info', '.data')

    @cached_property
    def epfile(self):
        return os.path.join(self.distinfopath, 'entry_points.txt')

    @cached_property
    def metadata(self):
        return json.load(
            open(os.path.join(self.distinfopath, 'metadata.json'), 'rb'))

    @cached_property
    def name(self):
        return self.metadata['name']

    @cached_property
    def scriptsdir(self):
        return os.path.join(self.datadir, 'scripts')

    @cached_property
    def scripts(self):
        return itertools.chain(self._scripts(), self._ep_scripts())

    def _scripts(self):
        try:
            listing = os.listdir(self.scriptsdir)
        except OSError:
            raise StopIteration
        for name in listing:
            with open(os.path.join(self.scriptsdir, name), 'rb') as f:
                content = f.read()
            template = '#!%(python)s\n' + content.split('\n', 1)[1]
            yield name, template

    def _ep_scripts(self):
        cfgparser = ConfigParser.SafeConfigParser()
        try:
            cfgparser.read(self.epfile)
            items = cfgparser.items('console_scripts')
        except (ConfigParser.NoSectionError, OSError):
            raise StopIteration

        for name, callpath in items:
            module, func = callpath.split(':')
            # %(python)s still needs to be filled in
            template = SCRIPT_TEMPLATE % dict(func=func, module=module)
            yield name, template
