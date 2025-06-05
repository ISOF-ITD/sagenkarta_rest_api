import logging
from base64 import b64encode
import requests
from revproxy.views import ProxyView
from django.http import HttpResponse
from requests import RequestException
from django.views.decorators.clickjacking import xframe_options_exempt

from sagenkarta_rest_api import config

logger = logging.getLogger(__name__)

"""
All pass-through proxy endpoints live here.
These  wrappers isolate the rest of the code-base from
up-stream details (hostnames, auth schemes, content-types).
Every proxy must
• forward the caller’s query‐string verbatim (`request.GET`)
• preserve the upstream status-code
• preserve the upstream `Content-Type`
If you change any of the above, leave a comment
"""

# ---------- plain function proxies ----------
@xframe_options_exempt
def isofGeoProxy(request):
    """
    Example:
    https://oden-test.isof.se/geoserver/gwc/service/wmts?REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&LAYER=SockenStad_ExtGranskning-clipped:SockenStad_ExtGranskn_v1.0_clipped&STYLE=&TILEMATRIX=EPSG:900913:4&TILEMATRIXSET=EPSG:900913&FORMAT=application/x-protobuf;type=mapbox-vector&TILECOL=9&TILEROW=4
    http://localhost:8000/api/isofGeoProxy?REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&LAYER=SockenStad_ExtGranskning-clipped:SockenStad_ExtGranskn_v1.0_clipped&STYLE=&TILEMATRIX=EPSG:900913:4&TILEMATRIXSET=EPSG:900913&FORMAT=application/x-protobuf;type=mapbox-vector&TILECOL=9&TILEROW=4
    We forward all query-params to the ISOF WMTS endpoint.
    """
    upstream = "https://oden-test.isof.se/geoserver/gwc/service/wmts"
    # drop Host (and possibly Cookie) to be safe
    fwd_headers = {k: v for k, v in request.headers.items()
                   if k.lower() not in {"host", "cookie"}}
    try:
        resp = requests.get(
            upstream,
            params = request.GET,  # forward caller’s query-string verbatim
            headers = fwd_headers,
            timeout = 20,  # avoid hanging workers
        )
    except RequestException as exc:
        # Upstream unreachable → fail fast with 502
        logger.warning("isofGeoProxy: %s", exc, exc_info=True)
        return HttpResponse("Bad gateway", status=502)

    return HttpResponse(
        resp.content,
        status=resp.status_code,
        content_type=resp.headers.get("content-type", "application/octet-stream"),
    )


def SimpleLantmaterietProxy(request):
    # 401 responses usually mean the Authorization header is missing
    # or incorrectly base64-encoded.
    """
        Pass-through to Lantmäteriet WMTS that requires Basic auth.

        Client URL example:
            /api/simple_lm_proxy/9/151/277.png
        We lop off the prefix                 ^^^^^^^^^^^^^^^^^^^^^
        and append the remainder to           config.LantmaterietProxy.
        """
    auth = b64encode(config.LantmaterietProxy_access.encode()).decode()
    tail = request.path.partition("simple_lm_proxy")[2].lstrip("/")
    upstream = f"{config.LantmaterietProxy.rstrip('/')}/{tail}"
    headers = {**request.headers, "Authorization": f"Basic {auth}"}
    resp = requests.get(upstream, params=request.GET, headers=headers, timeout=20)
    return HttpResponse(
        resp.content,
        status=resp.status_code,
        content_type=resp.headers.get("content-type", "application/octet-stream"),
    )

# ---------- class-based reverse proxies ----------
class _AuthProxy(ProxyView):
    """
    Reverse-proxy base that injects HTTP Basic auth taken from
    `config.LantmaterietProxy_access` (“user:pass”).
    Subclasses must override the class attribute `upstream`.
    """
    upstream: str = "" # will be overridden in subclasses

    def get_request_headers(self):
        hdrs = super().get_request_headers().copy()
        hdrs.pop("Host", None)
        hdrs["Authorization"] = (
            f"Basic {b64encode(config.LantmaterietProxy_access.encode()).decode()}"
        )
        return hdrs


class LantmaterietProxyView(_AuthProxy): upstream = config.LantmaterietProxy
class LantmaterietEpsg3857ProxyView(_AuthProxy): upstream = config.LantmaterietEpsg3857Proxy
class LantmaterietNedtonadEpsg3857ProxyView(_AuthProxy): upstream = config.LantmaterietNedtonadEpsg3857Proxy
class LantmaterietOrtoProxyView(_AuthProxy): upstream = config.LantmaterietOrtoProxy

class LantmaterietHistOrtoProxyView(ProxyView):

    # Orthophoto layer uses API-key in clear text
    upstream = config.LantmaterietHistOrtoProxy

    def get_request_headers(self):
        hdrs = super().get_request_headers()
        hdrs["Authorization"] = (
            f"Basic {b64encode(config.LantmaterietProxy_access_opendata.encode()).decode()}"
        )
        return hdrs


# Everything below is pass-through, no custom headers needed
class IsofGeoProxyView(ProxyView): upstream = config.IsofGeoProxy
class IsofHomepageView(ProxyView): upstream = config.IsofHomepage
class FriggStaticView(ProxyView): upstream = config.FriggStatic
class FilemakerProxyView(ProxyView):
    """
        Legacy FileMaker pass-through.

        NB: FileMaker sets its own <frame> policy.  If the embed breaks,
        add CSP `frame-ancestors` on the *response* headers, **not** here –
        see https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/frame-ancestors
    """
    upstream = config.FilemakerProxy
