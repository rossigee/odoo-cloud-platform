# Copyright 2016-2021 Camptocamp SA
# Copyright 2025 Ross Golder
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
from prometheus_client import generate_latest

from odoo.http import Controller, route, request


class PrometheusController(Controller):
    @route("/metrics", auth="none")
    def metrics(self, **kw):
        # Check for PROMETHEUS_TOKEN env var
        expected_token = os.environ.get("PROMETHEUS_TOKEN", "").strip()
        if expected_token:
            auth_header = request.httprequest.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                provided_token = auth_header[7:].strip()
                if provided_token == expected_token:
                    headers = {"Content-Type": "text/plain"}
                    return request.make_response(generate_latest(), headers=headers)

        # No valid token - return 401
        return request.make_response('Unauthorized', status=401, headers={'Content-Type': 'text/plain'})