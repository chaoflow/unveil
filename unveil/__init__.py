from __future__ import print_function

"""CLI to unveil wheels.
"""

__author__ = 'Florian Friesdorf <flo@chaoflow.net>'
__version__ = '0'


import click
import logging
import os

from .distinfo import Distribution


UMASK=os.umask(0)
os.umask(UMASK)
UMASKED_EXE=(0o111 - (0o111 & UMASK))


@click.group()
@click.option('--debug/--no-debug', help='Enable debug output')
@click.pass_context
def cli(ctx, debug):
    log = ctx.log = logging.getLogger(__name__)
    if debug:
        logging.basicConfig(level=logging.DEBUG)


@cli.command(name="create-scripts")
@click.option(
    '-f', '--force',
    is_flag=True,
    help="Force overwrite of existing scripts."
)
@click.option(
    '--python',
    type=click.Path(exists=True),
    help="Python interpreter used for scripts.",
)
@click.option(
    '--target',
    type=click.Path(exists=True),
    help="Target directory to place scripts in",
)
@click.option(
    '--dist', 'dists',
    callback=lambda ctx, dists: tuple(Distribution(distinfopath=x) for x in dists),
    multiple=True,
    type=click.Path(exists=True),
    help="Paths to .dist-info directories",
)
@click.pass_context
def create_scripts(ctx, dists, force, python, target):
    log = ctx.log = ctx.parent.log.getChild('create-scripts')

    for dist in dists:
        for name, content in dist.scripts:
            abspath = os.path.join(target, name)
            assert not os.path.exists(abspath) or force
            with open(abspath, 'wb') as f:
                f.write(content % dict(python=python))
            os.chmod(abspath, os.stat(abspath).st_mode | UMASKED_EXE)
