import os
import pickle

from flask import Flask, render_template, request, jsonify
from trie import Trie

swarm_node_api = os.getenv('SWARM_BEE_API_URL', 'http://localhost:1633') + '/bzz/'

index_swarm_hashes = {
    0: os.getenv('SHARD_SWARM_HASH_0'),
    1: os.getenv('SHARD_SWARM_HASH_1'),
    2: os.getenv('SHARD_SWARM_HASH_2'),
}


def shard_hash_func(k): return ord(k) % 3


class NFTIndex:
    def __init__(self, description, keywords, image_url):
        self.description = description
        self.keywords = keywords
        self.image_url = image_url

    def __hash__(self):
        return hash((self.description, frozenset(self.keywords), self.image_url))

    def __eq__(self, other):
        if isinstance(other, NFTIndex):
            return (self.description, frozenset(self.keywords), self.image_url) == (
                other.description, frozenset(other.keywords), other.image_url)
        return False


class ShardedIndex:
    def query(self, query_words: list[str]):
        results = None
        for word in query_words:
            word_results = self._search_word(word)
            print(f"Found {len(word_results)} results for '{word}'")

            nft_indices = set(
                NFTIndex(result['description'], result['keywords'], result['image_url']) for result in word_results)
            if results is None:
                results = nft_indices
            else:
                results = results.intersection(nft_indices)
            print(f"Total results {len(results)} after '{word}'")

        return list(results)

    @staticmethod
    def _search_word(word):
        ref_char = word[0]
        print(f"Ref character: '{ref_char}'")
        shard_key = shard_hash_func(ref_char)

        index_swarn_hash = index_swarm_hashes[shard_key]
        print(f"Searching index {index_swarn_hash} for '{word}'")

        index = load_index(index_swarn_hash)

        return index[ref_char].search(word[1:])


class Index(Trie):

    def query(self, query_words: list[str]):
        results = None
        for word in query_words:
            word_results = self.search(word)
            print(f"Found {len(word_results)} results for '{word}'")

            nft_indices = set(
                NFTIndex(result['description'], result['keywords'], result['image_url']) for result in word_results)
            if results is None:
                results = nft_indices
            else:
                results = results.intersection(nft_indices)
            print(f"Total results {len(results)} after '{word}'")

        return list(results)


def load_index(swarm_hash):
    import requests

    url = f"{swarm_node_api}{swarm_hash}/"
    print(f"Loading index from {url}")
    response = requests.get(url)

    return pickle.loads(response.content)


app = Flask(__name__)


@app.route('/')
def home():
    return render_template('search.html')


@app.route('/examples')
def examples():
    return render_template('examples.html')


@app.route('/search')
def search():
    query = request.args.get('q', '').split(' ')
    print(query)
    results = ShardedIndex().query(query)

    response = []
    for result in results:
        response.append({
            'description': result.description,
            'keywords': list(result.keywords),
            'image_url': result.image_url,
        })
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
