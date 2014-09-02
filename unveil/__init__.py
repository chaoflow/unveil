from __future__ import print_function

"""CLI to unveil wheels.
"""

__author__ = 'Florian Friesdorf <flo@chaoflow.net>'
__version__ = '0.20140726'


import click
import itertools
import logging
import os
from glob import glob

from .distinfo import Distribution


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


def find_dists(path):
    if path.endswith('.dist-info'):
        dists = (path,)
    elif path.endswith('site-packages'):
        dists = glob(os.path.join(path, '*.dist-info'))
    else:
        dists = glob(os.path.join(path, 'lib', '*', 'site-packages', '*.dist-info'))
    return tuple(Distribution(distinfopath=x) for x in dists)


@cli.command(help="""
Unveil metadata of distributions found in space-separated list of
PATHS.

A PATH may point at a '*.dist-info' directory of one distribution, a
'site-packages' directory containing multiple distributions or a
directory being globbed with 'lib/*/site-packages/*.dist-info'.""")
@click.option(
    '--print-names',
    is_flag=True,
    help='Print names of distributions found')
@click.option(
    '--print-nix-wheels-meta',
    is_flag=True,
    help='Print content for wheels-meta file for nixpkgs.')
@click.option(
    '--sort/--no-sort',
    help='Sort distributions by name')
@click.argument(
    'paths',
    nargs=-1,
    required=True,
    type=click.Path(exists=True))
def meta(paths, print_names, print_nix_wheels_meta, sort):
    dists = tuple(itertools.chain(*(find_dists(x) for x in paths)))
    if sort:
        dists = sorted(dists, key=lambda x: x.name)

    if print_names:
        print('\n'.join(x.name for x in dists))

    if print_nix_wheels_meta:
        print_nix_meta(dists)


def print_nix_meta(dists):
    """XXX: This is nixpkgs-specific and might be moved out
    """
    dists_meta = [dist.metadata for dist in dists]
    dists_names = [meta['name'] for meta in dists_meta]

    print('python: self:')
    print('{')
    print('')
    for meta in dists_meta:
        requires = []
        if 'run_requires' in meta:
            for item in meta['run_requires']:
                if 'requires' in item:
                    for req_item in item['requires']:
                        dist_name = req_item.split(' ')[0]
                        if dist_name in dists_names:
                            requires.append(dist_name)
        if 'summary' in meta:
            print('  "{}".meta.description = "{}";'.format(
                meta['name'], meta['summary']))
        if 'extensions' in meta and \
           'python.details' in meta['extensions'] and \
           'project_urls' in meta['extensions']['python.details'] and \
           'Home' in meta['extensions']['python.details']['project_urls']:
            print('  "{}".meta.homepage = "{}";'.format(
                meta['name'],
                meta['extensions']['python.details']['project_urls']['Home'],
                ))
        if 'license' in meta:
            print('  "{}".meta.license = "{}";'.format(
                meta['name'], meta['license']))
        print('  "{}".requires = [{}];'.format(
            meta['name'],
            ' '.join(['self.' + i for i in requires]),
            ))
        print('')
    print('}')
