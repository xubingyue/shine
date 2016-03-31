# -*- coding: utf-8 -*-


import sys
sys.path.insert(0, '../../')

from shine import Worker, logger


app = Worker()


@app.create_client
def create_client(request):
    logger.debug(request)


@app.close_client
def close_client(request):
    logger.debug(request)


@app.route(1)
def reg(request):
    request.write_to_client(dict(
        ret=0,
    ))


@app.route(2)
def login(request):

    request.login_client(request.box.get_json()['uid'], 2)
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


@app.route(5)
def handle_trigger(request):
    logger.error('from trigger.write_to_worker')
