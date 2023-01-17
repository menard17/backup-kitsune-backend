from __future__ import division, print_function, unicode_literals

__copyright__ = """\
Copyright (C) m-click.aero GmbH

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

import datetime
import os
import ssl
import tempfile

import cryptography.hazmat.backends
import cryptography.hazmat.primitives.asymmetric.rsa
import cryptography.hazmat.primitives.hashes
import cryptography.hazmat.primitives.serialization.pkcs12
import cryptography.x509.oid
import requests.adapters

try:
    from ssl import PROTOCOL_TLS as default_ssl_protocol
except ImportError:
    from ssl import PROTOCOL_SSLv23 as default_ssl_protocol


def check_cert_not_expired(cert):
    cert_not_after = cert.not_valid_after
    if cert_not_after < datetime.datetime.utcnow():
        raise ValueError("Client certificate expired: You can not use this cert")


def create_ssl_sslcontext(
    pkcs12_data, pkcs12_password_bytes, ssl_protocol=default_ssl_protocol
):
    (
        private_key,
        cert,
        ca_certs,
    ) = cryptography.hazmat.primitives.serialization.pkcs12.load_key_and_certificates(
        pkcs12_data, pkcs12_password_bytes
    )
    check_cert_not_expired(cert)
    ssl_context = ssl.SSLContext(ssl_protocol)
    with tempfile.NamedTemporaryFile(delete=False) as c:
        try:
            pk_buf = private_key.private_bytes(
                cryptography.hazmat.primitives.serialization.Encoding.PEM,
                cryptography.hazmat.primitives.serialization.PrivateFormat.TraditionalOpenSSL,
                cryptography.hazmat.primitives.serialization.BestAvailableEncryption(
                    password=pkcs12_password_bytes
                ),
            )
            c.write(pk_buf)
            buf = cert.public_bytes(
                cryptography.hazmat.primitives.serialization.Encoding.PEM
            )
            c.write(buf)
            if ca_certs:
                for ca_cert in ca_certs:
                    check_cert_not_expired(ca_cert)
                    buf = ca_cert.public_bytes(
                        cryptography.hazmat.primitives.serialization.Encoding.PEM
                    )
                    c.write(buf)
            c.flush()
            c.close()
            ssl_context.load_cert_chain(c.name, password=pkcs12_password_bytes)
        finally:
            os.remove(c.name)
    return ssl_context


class Pkcs12Adapter(requests.adapters.HTTPAdapter):
    def __init__(self, *args, **kwargs):
        pkcs12_data = kwargs.pop("pkcs12_data", None)
        pkcs12_filename = kwargs.pop("pkcs12_filename", None)
        pkcs12_password = kwargs.pop("pkcs12_password", None)
        ssl_protocol = kwargs.pop("ssl_protocol", default_ssl_protocol)
        if pkcs12_data is None and pkcs12_filename is None:
            raise ValueError(
                'Both arguments "pkcs12_data" and "pkcs12_filename" are missing'
            )
        if pkcs12_data is not None and pkcs12_filename is not None:
            raise ValueError('Argument "pkcs12_data" conflicts with "pkcs12_filename"')
        if pkcs12_password is None:
            raise ValueError('Argument "pkcs12_password" is missing')
        if pkcs12_filename is not None:
            with open(pkcs12_filename, "rb") as pkcs12_file:
                pkcs12_data = pkcs12_file.read()
        if isinstance(pkcs12_password, bytes):
            pkcs12_password_bytes = pkcs12_password
        else:
            pkcs12_password_bytes = pkcs12_password.encode("utf8")
        self.ssl_context = create_ssl_sslcontext(
            pkcs12_data, pkcs12_password_bytes, ssl_protocol
        )
        super(Pkcs12Adapter, self).__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        if self.ssl_context:
            kwargs["ssl_context"] = self.ssl_context
        return super(Pkcs12Adapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        if self.ssl_context:
            kwargs["ssl_context"] = self.ssl_context
        return super(Pkcs12Adapter, self).proxy_manager_for(*args, **kwargs)
