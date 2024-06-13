from abc import ABC, abstractmethod

from trie import Trie


def shard_hash_func(k): return ord(k) % 3


class Index(Trie):

    def add(self, metadata: [], nft):
        nft_index = {
            "description": nft['ai_description'],
            "keywords": nft['ai_keywords'],
            "image_url": nft['image_url'],
        }
        for word in metadata:
            self.insert(word, nft_index)

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


class ShardedIndex(Index, ABC):

    def __init__(self, index_shards):
        super().__init__()
        self.index_shards = index_shards

    def search(self, word):
        ref_char = word[0]
        print(f"Ref character: '{ref_char}'")
        shard_key = shard_hash_func(ref_char)

        index_key = self.index_shards[shard_key]
        print(f"Searching index {index_key} for '{word}'")

        index = self.load_index(index_key)

        return index[ref_char].search(word[1:])

    @abstractmethod
    def load_index(self, index_key):
        pass
