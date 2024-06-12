import pickle

from flask import Flask, render_template, request, jsonify
from trie import Trie


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


def load_index():
    with open('nft_index.pkl', 'rb') as f:
        return pickle.load(f)


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
    index = load_index()
    results = index.query(query)

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
