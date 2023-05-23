from services.document_reference_service import DocumentReferenceService


class MockResourceClient(object):
    """
    dummy class object
    """


def test_check_create_document_reference_happy_path():
    service = DocumentReferenceService(MockResourceClient())
    pages = [{"url": "https://my.image.url"}, {"data": "dummy-image-data"}]
    ok, err_msg = service.check_create_document_reference(pages)
    assert ok
    assert err_msg is None


def test_check_create_document_reference_must_have_url_or_data():
    service = DocumentReferenceService(MockResourceClient())
    pages = [{"urll": "https://my.image.url"}, {"dataa": "dummy-image-data"}]
    ok, err_msg = service.check_create_document_reference(pages)
    assert not ok
    assert err_msg == "Page data should have either `url` or `data`"
