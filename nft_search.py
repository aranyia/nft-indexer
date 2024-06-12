import base64
import logging
import os
import pickle
import re
import requests
import time

from dataclasses import dataclass
from langchain_community.chat_models import ChatOllama
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser, BaseTransformOutputParser
from langchain_core.prompts import ChatPromptTemplate

from trie import Trie

start_time = time.time()


@dataclass
class Trait:
    trait_type: str
    value: str

    def __str__(self):
        return f'{self.trait_type} is {self.value}.'


class KeywordParser(BaseTransformOutputParser[set[str]]):

    def parse(self, output: str) -> set[str]:
        match = re.search(r'(\w)+((, )\w+)*$', output)
        result = match.group() if match else output
        return set(result.lower().split(', '))


class AiModelImage:

    def __init__(self):
        llm = ChatOllama(model="moondream", temperature=0.7)
        self.chain = AiModelImage.prompt_func | llm | StrOutputParser()

    @staticmethod
    def prompt_func(data):
        image_part = {
            "type": "image_url",
            "image_url": f"data:image/jpeg;base64,{data['image']}"
        }
        text_part = {"type": "text", "text": data['text']}

        return [HumanMessage(content=[image_part, text_part])]

    def question(self, q: str, image_base64: str) -> str:
        result = self.chain.invoke(
            {"text": q, "image": image_base64}
        )
        return result


class AiModelText:

    def __init__(self):
        self.llm = Ollama(model="llama3", temperature=0.7)

    def keywords(self, text: str) -> set[str]:
        chain_keywords = (
                SystemMessage(
                    content="Only return a comma-separated simple array. Extract only major features into keywords.") +
                HumanMessage(
                    content=f"Give a list of one-word keywords for indexing the following text: {text}") |
                self.llm | KeywordParser())
        return chain_keywords.invoke({"text": text})

    def short_poem(self, description: str) -> str:
        chain_poem = (SystemMessage(content="Do not repeat instructions in the response. Do not include a title.") +
                      HumanMessage(content=f"Write a one-stanza short poem about this character: {description}") |
                      self.llm | StrOutputParser())
        return chain_poem.invoke({"description": description})

    def free_text(self, instructions: str, description: str) -> str:
        prompt = ChatPromptTemplate.from_template("{instructions}\nBased on this: {description}")
        chain_poem = prompt | self.llm | StrOutputParser()
        return chain_poem.invoke({"instructions": instructions, "description": description})


class OpenSeaAPI:
    url = "https://api.opensea.io/api/v2"
    limit_default = 5

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


def load_nfts(collection_name):
    max_limit = 200
    nfts = opensea.get_collection_nfts_by_name(collection_name, max_limit)
    print(f"Queried {len(nfts)} NFTs from collection '{collection_name}'\n")

    fetched_images = 0
    for nft in nfts:
        if nft['image_url'] is None:
            continue
        metadata = opensea.get_metadata(nft["metadata_url"])
        traits = opensea.get_traits(metadata)
        nft['traits'] = traits
        nft['metadata'] = metadata

        image_content = opensea.get_image_as_base64(nft['image_url'])
        nft['image_base64'] = image_content
        fetched_images += 1
        print(f"Fetched images {fetched_images}/{len(nfts)} NFTs")
    return nfts


ai_model_image = AiModelImage()
ai_model_text = AiModelText()
opensea = OpenSeaAPI(os.getenv("OPENSEA_API_KEY"))

nfts = load_nfts('azukielementals')  # 'azukielementals','the-anata-nft','parallelalpha','pudgypenguins','lasogette'


def generate_description(nft):
    if 'image_base64' not in nft:
        raise Exception("Image content missing")
    if 'traits' not in nft:
        raise Exception("Traits missing")
    traits_str = ' '.join(str(trait) for trait in nft['traits'])
    image_content = nft['image_base64']
    description = ai_model_image.question("Describe this image. \nHints: " + traits_str, image_content)
    nft['ai_description'] = description
    return nft


def generate_keywords(nft):
    if 'ai_description' not in nft or nft['ai_description'] is None:
        raise Exception("Description not generated")
    description = nft['ai_description']
    nft['ai_keywords'] = ai_model_text.keywords(description)
    for word in nft['ai_keywords']:
        if len(word) > 20:
            raise Exception("Invalid keyword generated", word)
    return nft


processed_images = 0
for nft in nfts:
    try:
        generate_description(nft)
        processed_images += 1
        print(f"Description gen. {processed_images}/{len(nfts)} NFTs")
    except Exception as e:
        logging.error(f"Error generating description for NFT {nft['image_url']}: {e}")

for nft in nfts:
    try:
        generate_keywords(nft)
        print(f"Description: {nft['ai_description']}\nKeywords: {nft['ai_keywords']}\n\n")
    except Exception as e:
        logging.error(f"Error generating keywords for NFT {nft['image_url']}: {e}")


class Index(Trie):

    def add(self, metadata: [], nft):
        nft_index = {
            "description": nft['ai_description'],
            "keywords": nft['ai_keywords'],
            "image_url": nft['image_url'],
        }
        for word in metadata:
            self.insert(word, nft_index)


index = Index()
for nft in nfts:
    if 'ai_keywords' not in nft or nft['ai_keywords'] is None:
        continue
    index.add(nft['ai_keywords'], nft)

end_time = time.time()
elapsed_time = end_time - start_time

print(f"Elapsed time: {format(elapsed_time, '.1f')} seconds for {len(nfts)} NFTs "
      f"({format(elapsed_time / len(nfts), '.1f')} sec / NFT)")

# Serialize the Index
index_file = 'nft_index.pkl'
print(f"\nSaving index to {index_file}")
with open(index_file, 'wb') as f:
    pickle.dump(index, f)
