import re

class SimpleTokenizer:
    def __init__(self, vocab, tokenize_fn=None):
        vocab["<|endoftext|>"] = len(vocab)
        vocab["<|unk|>"] = len(vocab)

        self.string_to_int = vocab
        self.int_to_string = {v: k for k, v in vocab.items()}
        self._tokenize = tokenize_fn or (lambda s: s.split())

    def encode(self, text: str) -> list[int]:
        return [self.string_to_int.get(t, self.string_to_int["<|unk|>"]) for t in self._tokenize(text)]

    def decode(self, tokens: list[int]) -> str:
        return re.sub(r'\s+([,.:;?!"()\'])', r'\1', " ".join([self.int_to_string[t] for t in tokens if t != self.string_to_int["<|endoftext|>"]]))
