from utils.orca_setup import OrcaSingleton


def test_orca_client_set_credentials_and_read_p12_cert_with_pass(mocker):
    """
    Scenario:
    set credential from local folder
    - Able to read the method read credentials from localfile
    """
    orca_client = OrcaSingleton()
    mocker.patch("utils.orca_setup.OrcaSingleton.open_session", return_value=None)
    orca_client.client()
    assert (
        orca_client.orca_client_cert_path
        == "/secrets/orca_client_cert/orca_client_cert.p12"
    )
    assert orca_client.apikey == "api key"
    assert orca_client.cert_pass == "pass"
    assert orca_client.fqdn == "demo-weborca.cloud.orcamo.jp"
