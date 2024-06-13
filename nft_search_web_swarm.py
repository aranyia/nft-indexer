import os
import pickle

from index import NFTIndex, ShardedIndex

from flask import Flask, render_template, request, jsonify

swarm_node_api = os.getenv('SWARM_BEE_API_URL', 'http://localhost:1633') + '/bzz/'

index_swarm_hashes = {
    0: os.getenv('SHARD_SWARM_HASH_0'),
    1: os.getenv('SHARD_SWARM_HASH_1'),
    2: os.getenv('SHARD_SWARM_HASH_2'),
}


class SwarmIndex(ShardedIndex):

    def load_index(self, swarm_hash):
        import requests

        url = f"{swarm_node_api}{swarm_hash}/"
        print(f"Loading index from {url}")
        response = requests.get(url)

        return pickle.loads(response.content)


index = SwarmIndex(index_swarm_hashes)
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
