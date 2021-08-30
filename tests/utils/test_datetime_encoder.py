from datetime import datetime

from utils.datetime_encoder import datetime_encoder


def test_date_time_encoder():
    today = datetime.today()
    output_dict = datetime_encoder({"date": today})

    assert today.strftime("%Y-%m-%d %H:%M:%S.%f") == output_dict["date"]
