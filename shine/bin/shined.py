# -*- coding: utf-8 -*-

import click
import importlib


@click.group()
def cli():
    pass


@cli.command()
@click.option('-c', '--config', help='config file', required=True)
def gateway(config):
    """
    启动gateway
    :return:
    """
    # gateway和forwarder都必须用gevent全部patch
    from gevent import monkey; monkey.patch_all()

    from shine import Gateway
    app = Gateway()
    if config.endswith('.py'):
        app.config.from_pyfile(config)
    else:
        app.config.from_object(importlib.import_module())

    app.run()


@cli.command()
@click.option('-c', '--config', help='config file/module', required=True)
def forwarder(config):
    """
    启动forwarder
    :return:
    """
    # gateway和forwarder都必须用gevent全部patch
    from gevent import monkey; monkey.patch_all()
    from shine import Forwarder

    app = Forwarder()
    if config.endswith('.py'):
        app.config.from_pyfile(config)
    else:
        app.config.from_object(importlib.import_module(config))

    app.run()


@cli.command()
@click.option('-a', '--app', help='app. worker:app/worker.app/worker', required=True)
@click.option('-c', '--config', help='config file', required=False)
def worker(app, config):
    """
    启动worker
    :return:
    """
    import os
    import sys
    # 必须要将当前所在路径放进来，否则找不到
    sys.path.append(os.getcwd())
    from shine import Worker
    from shine.share.utils import import_module_or_string

    app = import_module_or_string(app)

    if not isinstance(app, Worker):
        app = getattr(app, 'app')

    if config is not None:
        if config.endswith('.py'):
            app.config.from_pyfile(config)
        else:
            app.config.from_object(importlib.import_module(config))

    app.run()


if __name__ == '__main__':
    cli()
