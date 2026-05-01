#!/usr/bin/env python3
import secrets

def generate_secret_key():
    """Generate a secure Django SECRET_KEY."""
    return ''.join(secrets.token_urlsafe(50))

if __name__ == "__main__":
    secret_key = generate_secret_key()
    print(f"SECRET_KEY={secret_key}")
    print("\nCopie esta chave e cole no Render Dashboard como valor da variável SECRET_KEY")
