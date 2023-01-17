from requests import Session
from requests.adapters import Retry

from utils.requests_pkcs12 import Pkcs12Adapter


class OrcaSingleton:
    """Returns singleton object for orca connection.
    This is just meant to be called once to complete the setup for orca.
    """

    session: Session = None
    uri: str = None

    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = super(OrcaSingleton, cls).__new__(cls)
        return cls._instance

    @classmethod
    def client(cls, orca_base_path: str = "/secrets"):
        if cls.session is None and cls.uri is None:
            user = ""
            cls.orca_client_cert_path = (
                f"{orca_base_path}/orca_client_cert/orca_client_cert.p12"
            )
            cls.fs_orca_apikey = open(f"{orca_base_path}/orca_apikey/orca_apikey", "r")
            cls.apikey = cls.fs_orca_apikey.readlines()[0].strip()
            cls.fs_orca_cert_pass = open(
                f"{orca_base_path}/orca_cert_pass/orca_cert_pass", "r"
            )
            cls.cert_pass = cls.fs_orca_cert_pass.readline().strip()
            cls.fs_orca_fqdn = open(f"{orca_base_path}/orca_fqdn/orca_fqdn", "r")
            cls.fqdn = cls.fs_orca_fqdn.readline().strip()
            cls.uri = f"https://{user}:{cls.apikey}@{cls.fqdn}"
            cls.open_session(cls)
        else:
            return Exception("Orca client is already initialized")

    def open_session(cls):
        # Since There is case that orca service as backend is not stable
        # so we implement retry logic with exponetial backoff methodlogy here.
        # if total value = 6, It't takes totally 127 sec.

        retries = Retry(
            total=6,
            backoff_factor=1,
        )

        with Session() as cls.session:
            cls.session.mount(
                cls.uri,
                Pkcs12Adapter(
                    pkcs12_filename=cls.orca_client_cert_path,
                    pkcs12_password=cls.cert_pass,
                    max_retries=retries,
                ),
            )

    @classmethod
    def get_session(cls) -> tuple[Session, str]:
        if cls.session is None and cls.uri is None:
            cls.client()
            return cls.session, cls.uri
        elif cls.session is not None and cls.uri is not None:
            return cls.session, cls.uri
        else:
            raise Exception("Failed to get session, please check ORCA health status")
