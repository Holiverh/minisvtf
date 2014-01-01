# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import datetime

import flask

from valve import source
from valve.source.server import ServerQuerier, NoResponseError

app = flask.Flask(__name__)


@app.template_filter("yesno")
def yesno_filter(s, yes="Yes", no="No"):
    return yes if s else no


@app.template_filter("timedelta")
def timedelta_dilter(s):
    return unicode(datetime.timedelta(seconds=s))


@app.route("/<host>:<int:port>")
def stat_server(host, port):
    server = ServerQuerier((host, port))
    try:
        context = {
            "host": host,
            "port": port,
            "info": server.get_info(),
            "players": server.get_players(),
            "rules": server.get_rules(),
        }
        context["type_name"] = {
            ord("d"): "Dedicated",
            ord("l"): "Listen",
            ord("o"): "SourceTV",
        }[context["info"]["server_type"]]
        context["plat_name"] = {
            ord("l"): "Linux",
            ord("w"): "Windows",
            ord("m"): "Mac",
            ord("o"): "Mac",
            }[context["info"]["platform"]]
    except NoResponseError:
        return ("Timeout after {} seconds whilst "
                "waiting for response:".format(server.timeout))
    return flask.render_template("stat.html", **context)


if __name__ == "__main__":
    app.run(debug=True)
