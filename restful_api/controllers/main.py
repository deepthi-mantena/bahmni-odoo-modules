"""Part of odoo. See LICENSE file for full copyright and licensing details."""

import functools
import logging
import werkzeug.wrappers
import json
import datetime

from odoo import http
from odoo.addons.restful_api.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
from odoo.http import request

_logger = logging.getLogger(__name__)

def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()

def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("Authorization")
        if not access_token:
            return invalid_response(
                401, "missing http request (or) access token",)
        
        access_token_data = (
                                request.env["api.access_token"]
                                .sudo()
                                .search([("token", "=", access_token)], order="id DESC", limit=1)
                            )

        if (
                access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id)
                != access_token
            ):
            return invalid_response("401", "token seems to have expired or invalid")

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap

_routes = ["/api/<model>", "/api/<model>/<id>", "/api/<model>/<id>/<action>"]
            
#-------------------------------- example of api methods ----------------------------------------#

class APIController(http.Controller):
    """."""

    def __init__(self):
        self._model = "ir.model"

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["GET","OPTIONS"], csrf=True, cors='*')
    
    def get(self, model=None, id=None, **payload):
        ioc_name = model
        model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        if model:
            domain, fields, offset, limit, order = extract_arguments(payload)
            data = (
                request.env[model.model]
                .sudo()
                .search_read(
                    domain=domain,
                    fields=fields,
                    offset=offset,
                    limit=limit,
                    order=order,
                )
            )
            if id:
                domain = [("id", "=", int(id))]
                data = (
                    request.env[model.model]
                    .sudo()
                    .search_read(
                        domain=domain,
                        fields=fields,
                        offset=offset,
                        limit=limit,
                        order=order,
                    )
                )
            if data:
                return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),('Access-Control-Allow-Headers', 'Origin, Content-Type, X-Auth-Token, charset'),('Access-Control-Allow-Methods','POST, GET, OPTIONS, DELETE, PUT'), ('Access-Control-Allow-Origin'), ("Pragma", "no-cache")],
                response=json.dumps(data, default=default),
   
            )                
                #return response
            else:
                return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"),('Access-Control-Allow-Headers', 'Origin, Content-Type, X-Auth-Token, charset'),('Access-Control-Allow-Methods','POST, GET, OPTIONS, DELETE, PUT'), ('Access-Control-Allow-Origin'), ("Pragma", "no-cache")],
                response=json.dumps(data, default=default),
   
            )  
        return werkzeug.wrappers.Response(
        status=401,
        content_type="application/json; charset=utf-8",
        headers=[("Cache-Control", "no-store"),('Access-Control-Allow-Headers', 'Origin, Content-Type, X-Auth-Token, charset'),('Access-Control-Allow-Methods','POST, GET, OPTIONS, DELETE, PUT'), ('Access-Control-Allow-Origin'), ("Pragma", "no-cache")],
        response=json.dumps(
            {
                "status": 401,
                "message":  "The %s is not available in the registry." % ioc_name
            },
            default=datetime.datetime.isoformat,
        ),
    )  

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["POST"], csrf=True, cors='*')
    def post(self, model=None, id=None, **payload):
        """Create a new record.
        Basic sage:
        import requests

        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'charset': 'utf-8',
            'access-token': 'access_token'
        }
        data = {
            'name': 'Babatope Ajepe',
            'country_id': 105,
            'child_ids': [
                {
                    'name': 'Contact',
                    'type': 'contact'
                },
                {
                    'name': 'Invoice',
                   'type': 'invoice'
                }
            ],
            'category_id': [{'id': 9}, {'id': 10}]
        }
        req = requests.post('%s/api/res.partner/' %
                            base_url, headers=headers, data=data)

        """
        ioc_name = model
        model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        if model:
            try:
                resource = request.env[model.model].sudo().create(payload)
            except Exception as e:
                return invalid_response("params", e)
            else:
                data = {"id": resource.id}
                if resource:
                    return valid_response(data)
                else:
                    return valid_response(data)
        return invalid_response(
            # "invalid object model",
            401,
            "The model %s is not available in the registry." % ioc_name,
        )

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["PUT"], csrf=True, cors='*')
    def put(self, model=None, id=None, **payload):
        """."""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response(
                "invalid object id", "invalid literal %s for id with base " % id
            )
        _model = (
            request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        )
        if not _model:
            return invalid_response(
                404,
                "The model %s is not available in the registry." % model,
            )
        try:
            if "data" in payload:
                temp=json.loads(payload['data'].replace("\'", '"'))
                request.env[_model.model].sudo().browse(_id).write(temp)
            else:
                request.env[_model.model].sudo().browse(_id).write(payload)
                
        except Exception as e:
            return invalid_response(payload, e)
        else:
            return valid_response(
                payload
            )

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["DELETE"], csrf=True, cors='*')
    def delete(self, model=None, id=None, **payload):
        """."""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response(
                "invalid object id", "invalid literal %s for id with base " % id
            )
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            if record:
                record.unlink()
            else:
                return invalid_response(
                    "missing_record",
                    "record object with id %s could not be found" % _id,
                    404,
                )
        except Exception as e:
            return invalid_response("exception", e.name, 503)
        else:
            return valid_response("record %s has been successfully deleted" % record.id)

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["PATCH"], csrf=True, cors='*')
    def patch(self, model=None, id=None, action=None, **payload):
        """."""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response(
                "invalid object id", "invalid literal %s for id with base " % id
            )
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            _callable = action in [
                method for method in dir(record) if callable(getattr(record, method))
            ]
            if record and _callable:
                # action is a dynamic variable.
                getattr(record, action)()
            else:
                return invalid_response(
                    "missing_record",
                    "record object with id %s could not be found or %s object has no method %s"
                    % (_id, model, action),
                    404,
                )
        except Exception as e:
            return invalid_response("exception", e, 503)
        else:
            return valid_response("record %s has been successfully patched" % record.id)


##############################################################################################
