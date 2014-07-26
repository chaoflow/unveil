import ConfigParser
import itertools
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


class Distribution(object):
    def __init__(self, distinfopath):
        self.distinfopath = os.path.abspath(distinfopath)

    @property
    def epfile(self):
        return os.path.join(self.distinfopath, 'entry_points.txt')

    @property
    def metafile(self):
        return os.path.join(self.distinfopath, 'metadata.json')

    @property
    def datadir(self):
        return self.distinfopath.replace('.dist-info', '.data')

    @property
    def scriptsdir(self):
        return os.path.join(self.datadir, 'scripts')

    @property
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
        except ConfigParser.NoSectionError:
            raise StopIteration
        except OSError:
            raise StopIteration

        for name, callpath in items:
            module, func = callpath.split(':')
            # %(python)s still needs to be filled in
            template = SCRIPT_TEMPLATE % dict(func=func, module=module)
            yield name, template
