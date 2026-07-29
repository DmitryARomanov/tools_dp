import pytest
import pandas as pd
import responses

from dp_tools.geocoder import get_geodata

@responses.activate
def test_get_geodata_single_location_required_columns():
    mock_result = {
        "name": "Владивосток",
        "latitude": 43.1155,
        "longitude": 131.8853,
        "timezone": "Asia/Vladivostok",
        # остальные поля могут быть или не быть — не важно
    }

    responses.add(
        responses.GET,
        url="https://geocoding-api.open-meteo.com/v1/search",
        json={"results": [mock_result]},
        status=200,

    )

    df = get_geodata("Владивосток")

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1

    required_cols = ["name", "latitude", "longitude", "timezone"]
    assert all(col in df.columns for col in required_cols)


    row = df.iloc[0]
    assert row["name"] == "Владивосток"
    assert pd.notna(row["latitude"])
    assert pd.notna(row["longitude"])
    assert pd.notna(row["timezone"])


@responses.activate
def test_get_geodata_list_locations_required_columns():
    mock_results = [
        {
            "name": "Владивосток",
            "latitude": 43.1155,
            "longitude": 131.8853,
            "timezone": "Asia/Vladivostok",
        },
        {
            "name": "Чита",
            "latitude": 52.0317,
            "longitude": 113.5009,
            "timezone": "Asia/Chita",
        },
    ]

    def callback(request):
        name = request.params.get("name")
        for r in mock_results:
            if r["name"] == name:
                return 200, {}, '{"results": [' + str(r).replace("'", '"') + ']}'
        return 404, {}, '{"results": []}'

    responses.add_callback(
        responses.GET,
        url="https://geocoding-api.open-meteo.com/v1/search",
        callback=callback,
        content_type="application/json",
    )

    df = get_geodata(["Владивосток", "Чита"])

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2

    required_cols = ["name", "latitude", "longitude", "timezone"]
    assert all(col in df.columns for col in required_cols)
    assert set(df["name"]) == {"Владивосток", "Чита"}
    assert df["latitude"].notna().all()
    assert df["longitude"].notna().all()
    assert df["timezone"].notna().all()


@responses.activate
def test_get_geodata_http_error_raises():
    responses.add(
        responses.GET,
        url="https://geocoding-api.open-meteo.com/v1/search",
        status=500,
    )

    with pytest.raises(Exception):
        get_geodata("ЛюбойГород")
