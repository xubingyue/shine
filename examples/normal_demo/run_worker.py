# -*- coding: utf-8 -*-


import sys
sys.path.insert(0, '../../')

from netkit.box import Box
from shine import Worker, logger
import constants


app = Worker(Box)
app.config.from_object(constants)


@app.create_client
def create_client(request):
    logger.debug(request)


@app.close_client
def close_client(request):
    logger.debug(request)


@app.route(2)
def login(request):
    request.login_client(1, 2)
    # request.logout_client()
    request.write_to_client(dict(
        ret=100,
        body='ok'
    ))


@app.route(3)
def write_to_users(request):
    request.write_to_users([
        ((1, 2), dict(
            ret=0,
            body='from app'
        )),
    ])
    request.write_to_client(dict(
        ret=100,
        body='ok'
    ))


@app.route(4)
def close_users(request):
    request.close_users([1, 2])
    request.write_to_client(dict(
        ret=100,
        body='ok'
    ))

if __name__ == '__main__':
    app.run()
