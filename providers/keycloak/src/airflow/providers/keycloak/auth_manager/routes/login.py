# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from starlette.responses import HTMLResponse, RedirectResponse

from airflow.api_fastapi.app import get_auth_manager
from airflow.api_fastapi.auth.managers.base_auth_manager import COOKIE_NAME_JWT_TOKEN
from airflow.api_fastapi.common.router import AirflowRouter
from airflow.api_fastapi.core_api.security import get_user
from airflow.configuration import conf
from airflow.providers.keycloak.auth_manager.keycloak_auth_manager import KeycloakAuthManager
from airflow.providers.keycloak.auth_manager.user import KeycloakAuthManagerUser

log = logging.getLogger(__name__)
login_router = AirflowRouter(tags=["KeycloakAuthManagerLogin"])


@login_router.get("/login")
def login(request: Request) -> RedirectResponse:
    """Initiate the authentication."""
    client = KeycloakAuthManager.get_keycloak_client()
    redirect_uri = request.url_for("login_callback")
    auth_url = client.auth_url(redirect_uri=str(redirect_uri), scope="openid")
    return RedirectResponse(auth_url)


@login_router.get("/login_callback")
def login_callback(request: Request):
    """Authenticate the user."""
    code = request.query_params.get("code")
    if not code:
        return HTMLResponse("Missing code", status_code=400)

    client = KeycloakAuthManager.get_keycloak_client()
    redirect_uri = request.url_for("login_callback")

    tokens = client.token(
        grant_type="authorization_code",
        code=code,
        redirect_uri=str(redirect_uri),
    )
    userinfo = client.userinfo(tokens["access_token"])
    user = KeycloakAuthManagerUser(
        user_id=userinfo["sub"],
        name=userinfo["preferred_username"],
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )
    token = get_auth_manager().generate_jwt(user)

    response = RedirectResponse(url=conf.get("api", "base_url", fallback="/"), status_code=303)
    secure = bool(conf.get("api", "ssl_cert", fallback=""))
    response.set_cookie(COOKIE_NAME_JWT_TOKEN, token, secure=secure)
    return response


@login_router.get("/refresh")
def refresh(
    request: Request, user: Annotated[KeycloakAuthManagerUser, Depends(get_user)]
) -> RedirectResponse:
    """Refresh the token."""
    client = KeycloakAuthManager.get_keycloak_client()

    if not user or not user.refresh_token:
        raise HTTPException(status_code=400, detail="User is empty or has no refresh token")

    tokens = client.refresh_token(user.refresh_token)
    user.refresh_token = tokens["refresh_token"]
    user.access_token = tokens["access_token"]
    token = get_auth_manager().generate_jwt(user)

    redirect_url = request.query_params.get("next", conf.get("api", "base_url", fallback="/"))
    response = RedirectResponse(url=redirect_url, status_code=303)
    secure = bool(conf.get("api", "ssl_cert", fallback=""))

    response.set_cookie(COOKIE_NAME_JWT_TOKEN, token, secure=secure)
    return response
