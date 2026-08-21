"""net.py — Κοινό SSL-aware urlopen wrapper, χρησιμοποιείται από όλα τα scripts
του scanner/ (aggregate.py, radar.py, universe.py)."""
from urllib.request import urlopen

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}
TIMEOUT = 15

# Σε κάποια τοπικά Python (π.χ. python.org στο macOS) το urllib δεν βρίσκει CA
# certificates — αν υπάρχει το certifi, χρησιμοποίησε το bundle του.
_SSL_CTX = None
try:
    import ssl
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    pass


def urlopen_safe(req, timeout=TIMEOUT):
    if _SSL_CTX is not None:
        return urlopen(req, timeout=timeout, context=_SSL_CTX)
    return urlopen(req, timeout=timeout)
