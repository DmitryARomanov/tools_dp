from urllib.parse import quote
import pandas as pd
import requests




def get_geodata(location: str | list, verify=True) -> pd.DataFrame:
    data_list = []
    if isinstance(location, list):
        for item in location:
            encoded_str = quote(f'{item}')
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_str}&count=100&language=ru&format=json&countryCode=RU"
            resp = requests.get(url, verify=verify)
            resp.raise_for_status()
            tmp = resp.json()["results"][0]
            tmp = pd.Series(tmp).to_frame().T
            data_list.append(pd.DataFrame.from_dict(tmp))
        res = pd.concat(data_list, ignore_index=True)
        return res
    else:
        encoded_str = quote(location)
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_str}&count=100&language=ru&format=json&countryCode=RU"
        resp = requests.get(url, verify=verify)
        resp.raise_for_status()
        tmp = resp.json()["results"][0]
        res = pd.DataFrame(pd.Series(tmp).to_frame().T)
    return res

