import logging
import os
import pickle
import re
import sys
import time

from langchain_community.chat_models import ChatOllama
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser, BaseTransformOutputParser

from index import Index
from opensea import OpenSeaAPI

start_time = time.time()


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

if os.getenv("OPENSEA_API_KEY") is None:
    sys.exit("Please set the environment variable OPENSEA_API_KEY with your OpenSea API key.")
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
