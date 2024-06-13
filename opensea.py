from dataclasses import dataclass
import base64
import requests


@dataclass
class Trait:
    trait_type: str
    value: str

    def __str__(self):
        return f'{self.trait_type} is {self.value}.'


class OpenSeaAPI:
    url = "https://api.opensea.io/api/v2"
    limit_default = 4

    def __init__(self, api_key):
        self.headers = {
            "accept": "application/json",
            "x-api-key": api_key
        }

    def get_collection(self, name):
        response = requests.get(self.url + "/collections/" + name, headers=self.headers)
        return response.json()

    def get_collection_nfts(self, chain, contract, limit=limit_default) -> list[dict]:
        response = requests.get(self.url + f"/chain/{chain}/contract/{contract}/nfts?limit={limit}",
                                headers=self.headers)
        return response.json()['nfts']

    def get_collection_nfts_by_name(self, name, limit=limit_default) -> list[dict]:
        response = requests.get(self.url + f"//collection/{name}/nfts?limit={limit}",
                                headers=self.headers)
        return response.json()['nfts']

    @staticmethod
    def get_traits(metadata: dict) -> list[Trait]:
        traits = []
        for trait in metadata.get('attributes', []):
            traits.append(Trait(trait['trait_type'], trait['value']))
        return traits

    @staticmethod
    def get_metadata(metadata_url) -> dict:
        if metadata_url is None:
            return {}
        response = requests.get(metadata_url)
        metadata = response.json()
        return metadata

    @staticmethod
    def get_image_as_base64(image_url):
        response = requests.get(image_url)
        base64_image = base64.b64encode(response.content)
        return base64_image.decode('utf-8')
