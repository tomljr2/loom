def count_tokens(text: str) -> int:
    """
    Heuristic token counter.
    Standard LLM approximation: 1 token ≈ 0.75 words, or 1 word ≈ 1.33 tokens.
    """
    words = text.split()
    return int(len(words) * 1.35)