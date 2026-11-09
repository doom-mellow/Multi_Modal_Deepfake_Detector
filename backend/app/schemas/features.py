
from pydantic import BaseModel


class TextFeaturesResponse(BaseModel):
    character_count: int
    word_count: int
    sentence_count: int
    unique_word_count: int
    lexical_diversity: float
    average_sentence_length: float
    sentence_length_variation: int
    frequently_repeated_words: dict[str, int]


class CodeFeaturesResponse(BaseModel):
    language_hint: str
    character_count: int
    line_count: int
    nonempty_line_count: int
    token_count: int
    unique_token_count: int
    token_diversity: float
    comment_line_count: int
    comment_line_ratio: float
    average_line_length: float
    repeated_lines: dict[str, int]

