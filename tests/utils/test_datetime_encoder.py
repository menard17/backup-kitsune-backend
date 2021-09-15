from datetime import date, datetime

import pytest

from utils.datetime_encoder import datetime_encoder


def test_date_time_encoder(today):
    output_dict = datetime_encoder({"date": today})
    assert today.strftime("%Y-%m-%d %H:%M:%S.%f") == output_dict["date"]


def test_date_encoder(specific_day):
    output_dict = datetime_encoder({"date": specific_day})
    assert specific_day.strftime("%Y-%m-%d") == output_dict["date"]


def test_combined_items(today, specific_day):
    actual = {"date": today, "day": specific_day}
    output_dict = datetime_encoder(actual)
    assert today.strftime("%Y-%m-%d %H:%M:%S.%f") == output_dict["date"]
    assert specific_day.strftime("%Y-%m-%d") == output_dict["day"]


@pytest.fixture
def today():
    return datetime.today()


@pytest.fixture
def specific_day():
    return date(1990, 1, 1)
