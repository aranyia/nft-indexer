import os
import sys

from flask import Flask, render_template, Blueprint
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from opensea import OpenSeaAPI


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
        print(f"Q: {q}\n\nA: {result}\n\n")
        return result


class AiModelText:

    def __init__(self):
        self.llm = ChatOllama(model="llama2:13b", temperature=0.7)

    def short_poem(self, description: str) -> str:
        chain_poem = (SystemMessage(content="Do not repeat instructions in the response. Do not include a title.") +
                      HumanMessage(content=f"Write a one-stanza short poem about this character: {description}") |
                      self.llm | StrOutputParser())
        return chain_poem.invoke({"description": description})

    def free_text(self, instructions: str, description: str) -> str:
        prompt = ChatPromptTemplate.from_template("{instructions}\nBased on this: {description}")
        chain_poem = prompt | self.llm | StrOutputParser()
        return chain_poem.invoke({"instructions": instructions, "description": description})


def load_nfts(collection_name):
    nfts = opensea.get_collection_nfts_by_name(collection_name)
    print(nfts)
    for nft in nfts:
        print(
            f'ID: {nft["identifier"]}\nName: {nft["name"]}\nDescription: {nft["description"]}\nImage: {nft["image_url"]}\nOpenSea: {nft["opensea_url"]}\nMetadata: {nft["metadata_url"]}\n')

        metadata = opensea.get_metadata(nft["metadata_url"])
        traits = opensea.get_traits(metadata)
        nft['traits'] = traits
        nft['metadata'] = metadata

        image_content = opensea.get_image_as_base64(nft['image_url'])
        nft['image_base64'] = image_content
    return nfts


def create_app():
    app = Flask(__name__)
    app.register_blueprint(main_bp)
    return app


ai_model_image = AiModelImage()
ai_model_text = AiModelText()

if os.getenv("OPENSEA_API_KEY") is None:
    sys.exit("Please set the environment variable OPENSEA_API_KEY with your OpenSea API key.")
opensea = OpenSeaAPI(os.getenv("OPENSEA_API_KEY"))

nfts = load_nfts('azukielementals')  # 'azukielementals','the-anata-nft','parallelalpha','pudgypenguins','lasogette'

main_bp = Blueprint('main', __name__)


def render_string(value: str) -> str:
    return value.strip('\n').replace('\n', '<br/>')


@main_bp.route('/')
def home():
    return render_template('index.html', nfts=nfts)


@main_bp.route('/ai/describe/<id>')
def ai_describe(id):
    for nft in nfts:
        if nft['identifier'] == id:
            traits_str = ' '.join(str(trait) for trait in nft['traits'])
            image_content = nft['image_base64']
            result = ai_model_image.question("Describe this image. \nHints: " + traits_str, image_content)
            nft['ai_description'] = result
            return render_string(result)


@main_bp.route('/ai/colors/<id>')
def ai_colors(id):
    for nft in nfts:
        if nft['identifier'] == id:
            image_content = opensea.get_image_as_base64(nft['image_url'])
            result = ai_model_image.question("List up to dominant 5 colors, return a bullet point list only.",
                                             image_content)
            nft['ai_color_palette'] = result
            return render_string(result)


@main_bp.route('/ai/poem/short/<id>')
def ai_short_poem(id):
    for ntf in nfts:
        if ntf['identifier'] == id:
            description = ntf['ai_description']
            poem = ai_model_text.short_poem(description)
            print(poem)
            return render_string(poem)


@main_bp.route('/ai/freetext/<id>/<text>')
def ai_free_text(id, text):
    for ntf in nfts:
        if ntf['identifier'] == id:
            nft_description = ntf['ai_description']
            result = ai_model_text.free_text(text, nft_description)
            print(result)
            return render_string(result)


create_app().run()
