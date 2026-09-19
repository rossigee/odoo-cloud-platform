# Copyright 2016-2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import functools
import logging
import os
import re
from typing import Optional

from odoo import http
from odoo.tools import config

from .session import RedisSessionStore
from .strtobool import strtobool

_logger = logging.getLogger(__name__)

try:
    import redis
    from redis.sentinel import Sentinel
except ImportError:
    redis = None  # noqa
    _logger.debug("Cannot 'import redis'.")


def _redact_url(url: Optional[str]) -> str:
    """Redact password from Redis URL for safe logging."""
    if not url:
        return "<not set>"
    return re.sub(r"(:[^:@]+@)", ":****@", url)


def _redact_host(host: Optional[str], port: Optional[int]) -> str:
    """Return sanitized host:port for logging."""
    if not host:
        return "<not set>"
    return f"{host}:{port}" if port else host


def is_true(strval):
    return bool(strtobool(strval or "0".lower()))


sentinel_host = os.getenv("ODOO_SESSION_REDIS_SENTINEL_HOST")
sentinel_master_name = os.getenv("ODOO_SESSION_REDIS_SENTINEL_MASTER_NAME")
if sentinel_host and not sentinel_master_name:
    raise Exception(
        "ODOO_SESSION_REDIS_SENTINEL_MASTER_NAME must be defined "
        "when using session_redis"
    )
sentinel_port = int(os.getenv("ODOO_SESSION_REDIS_SENTINEL_PORT", 26379))
host = os.getenv("ODOO_SESSION_REDIS_HOST", "localhost")
port = int(os.getenv("ODOO_SESSION_REDIS_PORT", 6379))
prefix = os.getenv("ODOO_SESSION_REDIS_PREFIX")
url = os.getenv("ODOO_SESSION_REDIS_URL")
password = os.getenv("ODOO_SESSION_REDIS_PASSWORD")
expiration = os.getenv("ODOO_SESSION_REDIS_EXPIRATION")
anon_expiration = os.getenv("ODOO_SESSION_REDIS_EXPIRATION_ANONYMOUS")
ssl = os.getenv("ODOO_SESSION_REDIS_SSL", "1")
ssl_cert_reqs = os.getenv("ODOO_SESSION_REDIS_SSL_CERT_REQS", "1")
redis_cluster = os.getenv("ODOO_SESSION_REDIS_CLUSTER", "0")

_logger.debug(
    "session_redis env vars: sentinel_host=%s, url=%s, host=%s, port=%s, "
    "prefix=%s, redis_cluster=%s",
    sentinel_host,
    _redact_url(url),
    host,
    port,
    prefix,
    redis_cluster,
)


@functools.cached_property
def session_store(self):
    _logger.debug(
        "session_store property accessed: sentinel_host=%s, url=%s, redis_cluster=%s",
        sentinel_host,
        _redact_url(url),
        redis_cluster,
    )
    if sentinel_host:
        _logger.debug("Using Sentinel: %s:%s", sentinel_host, sentinel_port)
        sentinel = Sentinel([(sentinel_host, sentinel_port)], password=password)
        redis_client = sentinel.master_for(sentinel_master_name)
    elif url:
        _logger.debug("Using Redis URL: %s", _redact_url(url))
        redis_client = redis.from_url(url)
    elif is_true(redis_cluster):
        _logger.debug("Using Redis Cluster: %s:%s", host, port)
        redis_client = redis.RedisCluster(
            host=host,
            port=port,
            password=password,
            ssl=is_true(ssl),
            ssl_cert_reqs=is_true(ssl_cert_reqs),
        )
    else:
        _logger.debug("Using standard Redis: %s:%s", host, port)
        redis_client = redis.Redis(
            host=host,
            port=port,
            password=password,
            ssl=is_true(ssl),
            ssl_cert_reqs=is_true(ssl_cert_reqs),
        )
    try:
        return RedisSessionStore(
            redis=redis_client,
            prefix=prefix,
            expiration=expiration,
            anon_expiration=anon_expiration,
            session_class=http.Session,
        )
    except Exception as e:
        _logger.error(
            "Failed to initialize Redis session store: %s: %s",
            type(e).__name__,
            e,
        )
        raise


def purge_fs_sessions(session_dir):
    if not os.path.isdir(session_dir):
        _logger.warning("Session directory '%s' does not exist.", session_dir)
        return

    for fname in os.listdir(session_dir):
        fpath = os.path.join(session_dir, fname)
        try:
            os.unlink(fpath)
        except OSError:
            _logger.warning("OS Error during purge of redis sessions.")


_odoo_session_redis_env = os.getenv("ODOO_SESSION_REDIS")
_logger.debug(
    "Checking ODOO_SESSION_REDIS: value=%s, is_true=%s",
    _odoo_session_redis_env,
    is_true(_odoo_session_redis_env),
)

if is_true(os.getenv("ODOO_SESSION_REDIS")):
    _logger.info("session_redis: Initializing Redis session store!")
    if sentinel_host:
        _logger.info(
            "HTTP sessions stored in Redis with prefix '%s'. Using Sentinel on %s:%s",
            prefix or "",
            sentinel_host,
            sentinel_port,
        )
    else:
        _logger.info(
            "HTTP sessions stored in Redis with prefix '%s' on %s:%s",
            prefix or "",
            _redact_host(host, port),
            port,
        )
    http.Application.session_store = session_store
    http.Application.session_store.__set_name__(
        http.Application,
        "session_store",
    )
    _logger.info("session_store property has been assigned to http.Application")
    purge_fs_sessions(config.session_dir)
else:
    _logger.debug("session_redis: ODOO_SESSION_REDIS is not enabled, skipping Redis session store setup")
