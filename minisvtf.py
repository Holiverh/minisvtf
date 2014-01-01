# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import datetime

import flask

from valve import source
from valve.steam import api as steamapi
from valve.steam.api.util import appid_to_name
from valve.steam.id import SteamID, SteamIDError
from valve.source.server import ServerQuerier, NoResponseError

app = flask.Flask(__name__)
api = steamapi.SteamAPI("5493480160076D1E988C8C20A50085AA")


@app.template_filter("yesno")
def yesno_filter(s, yes="Yes", no="No"):
    return yes if s else no


@app.template_filter("timedelta")
def timedelta_dilter(s):
    return unicode(datetime.timedelta(seconds=s))


@app.template_filter("visibility")
def visibility_filter(s):
    return {
        s.PRIVATE: "Private",
        s.FRIENDS_ONLY: "Friends only",
        s.FRIENDS_OF_FRIENDS: "Friends of friends",
        s.USERS: "Steam users",
        s.PUBLIC: "Public",
    }.get(s.visibility, "Unknown ({})".format(s.visibility))


@app.template_filter("status")
def status_filter(s):
    return {
        s.OFFLINE: "Offline",
        s.ONLINE: "Online",
        s.BUSY: "Busy",
        s.AWAY: "Away",
        s.SNOOZE: "Snooze",
        s.LOOKING_TO_TRADE : "Looking to trade",
        s.LOOKING_TO_PLAY: "Looking to play",
    }.get(s.status, "Unknown ({})".format(s.status))


@app.template_filter("appid")
def appid_filter(s):
    return appid_to_name.get(int(s), s)


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
                "waiting for response".format(server.timeout))
    return flask.render_template("stat.html", **context)


def steamidify(steamid):
    try:
        return SteamID.from_text(steamid)
    except SteamIDError:
        return steamid


@app.route("/user/<steamid>")
def stat_user(steamid):
    try:
        user = api.user(steamidify(steamid))
    except steamapi.SteamAPIError as exc:
        return unicode(exc)
    return flask.render_template("user.html", steamid=steamid, user=user)


@app.route("/user/<steamid>/inventory/<inv>")
def inventory(steamid, inv):
    try:
        user = api.user(steamidify(steamid))
        inv = user.inventories[inv]
    except steamapi.SteamAPIError as exc:
        return unicode(exc)
    columns = []
    for item in inv:
        if inv.appid != steamapi.TRADING_CARDS:
            cols = dir(item) + dir(item._schema_item)
        else:
            cols = dir(item)
        for col in cols:
            if col in ["schema", "index"]:
                continue
            if col.startswith("_"):
                continue
            if col not in columns:
                columns.append(col)
    return flask.render_template("inventory.html",
                                 steamid=steamid, user=user, inv=inv, columns=columns)


if __name__ == "__main__":
    app.run(debug=True)
