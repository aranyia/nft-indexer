class TrieNode:
    def __init__(self):
        self.children = {}
        self.endOfWord = False
        self.images = []


class Trie:

    def __init__(self, children=None):
        self.root = TrieNode()
        if children is not None:
            self.root.children = children

    def insert(self, word, image):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.endOfWord = True
        node.images.append(image)

    def search(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        return self._collect_images(node)

    def _collect_images(self, node):
        images = []
        if node.endOfWord:
            images.extend(node.images)
        for child in node.children.values():
            images.extend(self._collect_images(child))
        return images
