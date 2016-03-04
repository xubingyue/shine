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
    gateway = Gateway(Box)
    if config.endswith('.py'):
        gateway.config.from_pyfile(config)
    else:
        gateway.config.from_object(config)

    gateway.run()


@cli.command()
@click.option('-c', '--config', help='config file or module', default=None)
def forwarder(config):
    """
    启动forwarder
    :return:
    """
    forwarder = Forwarder()

    if config.endswith('.py'):
        forwarder.config.from_pyfile(config)
    else:
        forwarder.config.from_object(config)

    forwarder.run()


if __name__ == '__main__':
    cli()
