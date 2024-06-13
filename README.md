NFT metadata indexing & searching
=================================

A proof of concept project focused on processing and indexing Non-Fungible Tokens (NFTs)
for search functionality. Here's a breakdown of what each script does:

1. `nft_search.py`: This script fetches NFTs, generates descriptions and keywords for each NFT using AI models, and then
   indexes these NFTs in a Trie data structure. The index is then serialized and saved to a file.

2. `nft_index_sharder.py`: This script loads the serialized index from the file, shards the index into smaller
   sub-indexes based on the first character of the keywords, and then saves each shard to a separate file.

3. `nft_search_web_swarm.py`: This script is a Flask web application that provides a search interface for the NFTs. It
   loads the sharded indexes from the Swarm network (a decentralized storage and communication network), performs search
   queries on these indexes, and returns the results. The search functionality is designed to work with sharded indexes,
   which allows it to efficiently search across multiple shards.

4. `nft.py`: This script is responsible for interacting with the OpenSea API to fetch NFTs and their associated
   metadata. It also uses AI models to generate descriptions and keywords for each NFT. The script is built around a
   Flask application that provides several routes for different AI functionalities such as describing an image, listing
   dominant colors, generating a short poem, and generating free text based on a given instruction. The fetched NFTs and
   their AI-generated descriptions are stored and can be accessed via the Flask app.

In summary, it is the basis of a system that uses AI to generate descriptions and keywords for NFTs, indexes these NFTs
for efficient search, shards the index for distributed storage, and provides a web interface for searching the NFTs.