# Copyright 2016-2021 Camptocamp SA
# Copyright 2025 Ross Golder
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from werkzeug.exceptions import BadRequest, Unauthorized

from odoo import models
from odoo.http import request

# Reuse the metrics defined by monitoring_prometheus. Defining the same
# Prometheus metric names again raises DuplicateTimeseries at load time.
from odoo.addons.monitoring_prometheus.models.ir_http import (  # noqa: E402
    LONGPOLLING_COUNT,
    REQUEST_TIME,
)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls, endpoint):
        path_info = request.httprequest.environ.get("PATH_INFO")

        if path_info.startswith("/longpolling/"):
            LONGPOLLING_COUNT.inc()
            return super()._dispatch(endpoint)

        if path_info.startswith("/metrics"):
            return super()._dispatch(endpoint)

        if path_info.startswith("/web/static"):
            label = "assets"
        elif path_info.startswith("/web/content"):
            label = "filestore"
        else:
            label = "client"

        res = None
        with REQUEST_TIME.labels(label).time():
            res = super()._dispatch(endpoint)

        return res

    @classmethod
    def _auth_method_token(cls):
        access_token = request.httprequest.headers.get("Authorization")
        if not access_token:
            raise BadRequest("Access token missing")

        if access_token.startswith("Bearer "):
            access_token = access_token[7:]

        user_id = request.env["res.users.apikeys"]._check_credentials(
            scope="metrics", key=access_token
        )
        if not user_id:
            raise Unauthorized("Access token invalid")

        # take the identity of the API key user
        request.update_env(user=user_id)
