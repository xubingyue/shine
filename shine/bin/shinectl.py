# -*- coding: utf-8 -*-

# gateway和forwarder都必须用gevent全部patch
from gevent import monkey; monkey.patch_all()

import click
from shine import Gateway, Forwarder
from netkit.box import Box


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
    server = Gateway(Box)
    server.config.from_pyfile(config)

    server.run()


@cli.command()
@click.option('-c', '--config', help='config file', required=True)
def forwarder(config):
    """
    启动forwarder
    :return:
    """
    server = Forwarder()
    server.config.from_pyfile(config)

    server.run()


if __name__ == '__main__':
    cli()
