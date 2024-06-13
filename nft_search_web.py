import pickle

from flask import Flask, render_template, request, jsonify
from index import Index


def load_index() -> Index:
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
