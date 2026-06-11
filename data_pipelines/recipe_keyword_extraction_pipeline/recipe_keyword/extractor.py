import re
from typing import Any

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "without",
}

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _collect_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        texts = []
        for key in ("name", "title", "ingredient", "text", "description", "value"):
            if key in value and value[key]:
                texts.append(str(value[key]))
        for nested in value.values():
            texts.extend(_collect_text(nested))
        return texts
    if isinstance(value, list):
        texts = []
        for item in value:
            texts.extend(_collect_text(item))
        return texts
    return [str(value)]


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def extract_keywords(recipe: dict) -> list[str]:
    texts = _collect_text(recipe.get("name"))
    texts.extend(_collect_text(recipe.get("recipe_category")))
    texts.extend(_collect_text(recipe.get("ingredients")))
    texts.extend(_collect_text(recipe.get("method")))
    texts.extend(_collect_text(recipe.get("meta_data")))

    keywords: set[str] = set()
    for text in texts:
        for token in _tokenize(text):
            if len(token) < 2 or token in STOPWORDS:
                continue
            keywords.add(token)

    return sorted(keywords)
