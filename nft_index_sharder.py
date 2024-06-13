import pickle

from nft_search_web_swarm import Index, shard_hash_func
from trie import Trie


def shard_index(single_index: Trie) -> {}:
    multi_index = {}
    sub_indexes = single_index.root.children.items()
    for char, node in sub_indexes:
        sub_trie = Trie(node.children)
        multi_index[char] = sub_trie

    print(multi_index)
    return multi_index


def shard_index_file(filename: str) -> {}:
    with open(filename, 'rb') as f:
        single_index = pickle.load(f)
        return shard_index(single_index)


hashmap = {}
for key, trie in shard_index_file('nft_index.pkl').items():
    # Calculate the hash of the key, take mod 3
    new_key = shard_hash_func(key)

    if new_key in hashmap:
        hashmap[new_key][key] = trie
    else:
        hashmap[new_key] = {key: trie}

print(hashmap.keys())

for key, value in hashmap.items():
    print(f'{key}:\n{value}')
    with open(f'nft_index_hash_{key}.pkl', 'wb') as f:
        pickle.dump(value, f)
        print(f"Saved nft_index_hash_{key}.pkl")
