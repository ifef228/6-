import re
from pathlib import Path
from simple_tokenizer import SimpleTokenizer
import tiktoken

DATA_DIR = Path(__file__).parent / "data"
TEXT_FILE = DATA_DIR / "The_Verdict.txt"


def tokenize(text: str) -> list[str]:
    """Разбивает текст на токены по шаблону ([,.]|\\s); пробелы в результат не входят."""
    parts = re.split(r'([,.:;?_!"()\']|--|\s)', text)
    return [p.strip() for p in parts if p.strip()]


def main():
    text = TEXT_FILE.read_text(encoding="utf-8")

    tiktoken_enc = tiktoken.get_encoding("gpt2")

    integers = tiktoken_enc.encode(text, allowed_special={"<|endoftext|>"})[50:]

    


if __name__ == "__main__":
    main()
