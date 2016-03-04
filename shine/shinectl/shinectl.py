# -*- coding: utf-8 -*-

import click
from shine import Gateway, Forwarder
from netkit.box import Box


@click.group()
def cli():
    pass


@cli.command()
@click.option('-c', '--config', help='config file or module', default=None)
def gateway(config):
    """
    启动gateway
    :return:
    """
    server = Gateway(Box)
    if config.endswith('.py'):
        server.config.from_pyfile(config)
    else:
        server.config.from_object(config)

    server.run()


@cli.command()
@click.option('-c', '--config', help='config file or module', default=None)
def forwarder(config):
    """
    启动forwarder
    :return:
    """
    server = Forwarder()

    if config.endswith('.py'):
        server.config.from_pyfile(config)
    else:
        server.config.from_object(config)

    server.run()


if __name__ == '__main__':
    cli()
