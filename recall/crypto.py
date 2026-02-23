def encrypt(text: str) -> str:
    return "".join(chr(ord(c) + 3) for c in text)


def decrypt(text: str) -> str:
    return "".join(chr(ord(c) - 3) for c in text)
