"""Клиент Codeforces API (с опциональным rate-limiter).

В тестах метод call_api подменяется — сетевые вызовы не выполняются.
"""
import json
import urllib.parse
import urllib.request

from app.core.config import settings


class CodeforcesError(Exception):
    pass


class CodeforcesClient:
    def __init__(self, limiter=None, base: str | None = None):
        self.limiter = limiter
        self.base = base or settings.cf_api_base

    def call_api(self, method: str, **params) -> object:
        if self.limiter is not None:
            self.limiter.acquire()
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{self.base}/{method}?{query}"
        request = urllib.request.Request(url, headers={"User-Agent": "online-programmer/1.0"})
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("status") != "OK":
            raise CodeforcesError(payload.get("comment", "Codeforces API error"))
        return payload["result"]

    def problemset_problems(self, tags: list[str] | None = None) -> dict:
        params = {}
        if tags:
            params["tags"] = ";".join(tags)
        return self.call_api("problemset.problems", **params)

    def user_status(self, handle: str, count: int = 10000, frm: int = 1) -> list:
        return self.call_api("user.status", handle=handle, count=count, **{"from": frm})

    def contest_standings(
        self, contest_id: int, handles: list[str] | None = None, count: int = 100
    ) -> dict:
        params: dict = {"contestId": contest_id, "from": 1, "count": count, "showUnofficial": "true"}
        if handles:
            params["handles"] = ";".join(handles)
        return self.call_api("contest.standings", **params)
