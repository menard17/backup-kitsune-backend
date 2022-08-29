import json
from unittest import TestCase

from pytest import raises

from src.blueprints.address import (
    AddressController,
    get_prefecture_by_id,
    get_region_by_id,
    get_validated_processed_code,
)


class TestGetDataById:
    def test_invalid_region_id(self):
        # Given
        region_id = 0

        # When and Then
        assert get_region_by_id(region_id) == {}

    def test_valid_region_id(self):
        # Given
        region_id = 1
        expected_output = {
            "id": 1,
            "name": "北海道",
            "kana": "ホッカイドウ",
            "en": "hokkaido",
            "neighbor": [2],
        }

        # When
        actual_output = get_region_by_id(region_id)

        # Then
        TestCase().assertDictEqual(expected_output, actual_output)

    def test_invalid_pref_id(self):
        # Given
        pref_id = 0

        # When and Then
        assert get_prefecture_by_id(pref_id) == {}

    def test_valid_pref_id(self):
        # Given
        pref_id = 1
        expected_output = {
            "id": 1,
            "region": 1,
            "name": "北海道",
            "short": "北海道",
            "kana": "ホッカイドウ",
            "en": "hokkaido",
            "neighbor": [2],
        }

        # When
        actual_output = get_prefecture_by_id(pref_id)

        # Then
        TestCase().assertDictEqual(expected_output, actual_output)


class TestGetValidatedProcessedCode:
    def test_short_zipcode(self):
        # Given
        zipcode = "123"

        # When and Then
        with raises(Exception):
            _ = get_validated_processed_code(zipcode)

    def test_long_zipcode(self):
        # Given
        zipcode = "12345678"

        # When and Then
        with raises(Exception):
            _ = get_validated_processed_code(zipcode)

    def test_dash_and_spaces(self):
        # Given
        zipcode = "  123-00 21"
        expected_output = "1230021"

        # When
        actual_output = get_validated_processed_code(zipcode)

        # Then
        assert actual_output == expected_output

    def test_non_numeric(self):
        # Given
        zipcode = "123@111"

        # When and Then
        with raises(Exception):
            _ = get_validated_processed_code(zipcode)


class TestGetAddressByZip:
    def test_get_address_by_zip(self):
        # Given
        zipcode = "1000001"
        expected_output = {
            "region": "関東",
            "prefecture": "東京都",
            "city": "千代田区",
            "area": "千代田",
            "street": None,
        }

        # When
        actual_output = AddressController.get_address_by_zip(zipcode).response[0]

        # Then
        assert expected_output == json.loads(actual_output)

    def test_four_items_get_address_by_zip(self):
        # Given
        zipcode = "9768501"
        expected_output = {
            "region": "東北",
            "prefecture": "福島県",
            "city": "相馬市",
            "area": "沖ノ内",
            "street": "１丁目２－１",
        }

        # When
        actual_output = AddressController.get_address_by_zip(zipcode).response[0]

        # Then
        assert expected_output == json.loads(actual_output)
