"""Staging API client. Credentials come from the environment, never from this file."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class ApiClient:
    base_url: str
    token: str = ""

    def request(self, method: str, path: str, body: dict | None = None, timeout: int = 120) -> tuple[int, Any]:
        url = self.base_url.rstrip("/") + path
        data = None if body is None else json.dumps(body).encode()
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read()
                payload = json.loads(raw.decode() or "null") if raw else None
                return response.status, payload
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            try:
                payload = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                payload = raw[:500]
            return exc.code, payload

    def login(self, email: str, password: str) -> None:
        status, payload = self.request("POST", "/auth/login", {"email": email, "password": password})
        if status != 200 or not isinstance(payload, dict) or not payload.get("access_token"):
            raise RuntimeError(f"login failed with status {status}")
        self.token = payload["access_token"]


def client_from_env() -> tuple[ApiClient, dict[str, str]]:
    web = os.environ.get("HF_QA_WEB_URL", "https://hfleanstg-web.whiteplant-64737337.eastus2.azurecontainerapps.io").rstrip("/")
    dv = os.environ.get("HF_QA_DV_URL", "https://hfleanstg-web-datavoyager.whiteplant-64737337.eastus2.azurecontainerapps.io").rstrip("/")
    api = os.environ.get("HF_QA_API_URL", "https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io/api/v1").rstrip("/")
    email = os.environ.get("HF_QA_EMAIL", "")
    password = os.environ.get("HF_QA_PASSWORD", "")
    if not email or not password:
        raise RuntimeError("Set HF_QA_EMAIL and HF_QA_PASSWORD. Do not commit them.")
    if "hfleanstg" not in web or "healthforesight-web.azurewebsites.net" in web:
        raise RuntimeError("HF_QA_WEB_URL is not the lean staging web app")
    if "dec4" in web or "healthforesight-rg" in web:
        raise RuntimeError("Refusing to test the December 4 demo")
    client = ApiClient(api)
    client.login(email, password)
    return client, {"web": web, "dv": dv, "api": api}
