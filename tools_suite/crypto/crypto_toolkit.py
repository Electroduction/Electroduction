#!/usr/bin/env python3
"""
Cryptography Toolkit
====================

Tools for hashing, encryption, password generation, and encoding.

Author: Electroduction Security Team
Version: 1.0.0
"""

import os
import sys
import base64
import hashlib
import hmac
import secrets
import string
import binascii
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime


class HashingTools:
    """Cryptographic hashing utilities."""

    ALGORITHMS = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512', 'sha3_256', 'sha3_512']

    def hash_string(self, data: str, algorithm: str = 'sha256') -> str:
        """Hash a string using specified algorithm."""
        return self.hash_bytes(data.encode('utf-8'), algorithm)

    def hash_bytes(self, data: bytes, algorithm: str = 'sha256') -> str:
        """Hash bytes using specified algorithm."""
        if algorithm not in hashlib.algorithms_available:
            raise ValueError(f"Algorithm {algorithm} not available")
        h = hashlib.new(algorithm)
        h.update(data)
        return h.hexdigest()

    def hash_file(self, filepath: str, algorithm: str = 'sha256',
                  chunk_size: int = 8192) -> str:
        """Hash a file."""
        h = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()

    def hash_all(self, data: Union[str, bytes]) -> Dict[str, str]:
        """Hash data with all available algorithms."""
        if isinstance(data, str):
            data = data.encode('utf-8')

        results = {}
        for alg in self.ALGORITHMS:
            try:
                results[alg] = self.hash_bytes(data, alg)
            except:
                pass
        return results

    def verify_hash(self, data: Union[str, bytes], expected_hash: str,
                    algorithm: str = 'sha256') -> bool:
        """Verify data matches expected hash."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        actual = self.hash_bytes(data, algorithm)
        return hmac.compare_digest(actual.lower(), expected_hash.lower())

    def hmac_sign(self, key: bytes, message: bytes,
                  algorithm: str = 'sha256') -> str:
        """Create HMAC signature."""
        return hmac.new(key, message, algorithm).hexdigest()

    def hmac_verify(self, key: bytes, message: bytes,
                    signature: str, algorithm: str = 'sha256') -> bool:
        """Verify HMAC signature."""
        expected = self.hmac_sign(key, message, algorithm)
        return hmac.compare_digest(expected, signature)


class EncodingTools:
    """Encoding and decoding utilities."""

    def base64_encode(self, data: Union[str, bytes]) -> str:
        """Encode data to Base64."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.b64encode(data).decode('ascii')

    def base64_decode(self, data: str) -> bytes:
        """Decode Base64 data."""
        return base64.b64decode(data)

    def base64_url_encode(self, data: Union[str, bytes]) -> str:
        """URL-safe Base64 encoding."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.urlsafe_b64encode(data).decode('ascii')

    def base64_url_decode(self, data: str) -> bytes:
        """URL-safe Base64 decoding."""
        # Add padding if needed
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data)

    def hex_encode(self, data: Union[str, bytes]) -> str:
        """Encode data to hexadecimal."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return binascii.hexlify(data).decode('ascii')

    def hex_decode(self, data: str) -> bytes:
        """Decode hexadecimal data."""
        return binascii.unhexlify(data)

    def base32_encode(self, data: Union[str, bytes]) -> str:
        """Encode data to Base32."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.b32encode(data).decode('ascii')

    def base32_decode(self, data: str) -> bytes:
        """Decode Base32 data."""
        return base64.b32decode(data)

    def rot13(self, text: str) -> str:
        """Apply ROT13 encoding."""
        result = []
        for char in text:
            if 'a' <= char <= 'z':
                result.append(chr((ord(char) - ord('a') + 13) % 26 + ord('a')))
            elif 'A' <= char <= 'Z':
                result.append(chr((ord(char) - ord('A') + 13) % 26 + ord('A')))
            else:
                result.append(char)
        return ''.join(result)

    def caesar_cipher(self, text: str, shift: int) -> str:
        """Apply Caesar cipher with given shift."""
        result = []
        for char in text:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                result.append(chr((ord(char) - base + shift) % 26 + base))
            else:
                result.append(char)
        return ''.join(result)


class PasswordTools:
    """Password generation and validation."""

    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SPECIAL = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    AMBIGUOUS = "l1IO0"

    def generate_password(self, length: int = 16, lowercase: bool = True,
                          uppercase: bool = True, digits: bool = True,
                          special: bool = True, exclude_ambiguous: bool = False) -> str:
        """Generate a secure random password."""
        chars = ""
        required = []

        if lowercase:
            chars += self.LOWERCASE
            required.append(secrets.choice(self.LOWERCASE))
        if uppercase:
            chars += self.UPPERCASE
            required.append(secrets.choice(self.UPPERCASE))
        if digits:
            chars += self.DIGITS
            required.append(secrets.choice(self.DIGITS))
        if special:
            chars += self.SPECIAL
            required.append(secrets.choice(self.SPECIAL))

        if exclude_ambiguous:
            chars = ''.join(c for c in chars if c not in self.AMBIGUOUS)

        if not chars:
            raise ValueError("At least one character set must be enabled")

        # Generate remaining characters
        remaining = length - len(required)
        if remaining > 0:
            password = required + [secrets.choice(chars) for _ in range(remaining)]
        else:
            password = required[:length]

        # Shuffle
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        return ''.join(password_list)

    def generate_passphrase(self, words: int = 4, separator: str = '-',
                            capitalize: bool = True) -> str:
        """Generate a passphrase using random words."""
        # Simple word list (in production, use a larger dictionary)
        word_list = [
            'apple', 'banana', 'cherry', 'dragon', 'eagle', 'falcon',
            'garden', 'hammer', 'island', 'jungle', 'knight', 'lemon',
            'mountain', 'nebula', 'ocean', 'phoenix', 'quartz', 'river',
            'sunset', 'thunder', 'umbrella', 'valley', 'winter', 'xenon',
            'yellow', 'zebra', 'anchor', 'bridge', 'castle', 'diamond',
            'eclipse', 'forest', 'glacier', 'harbor', 'ivory', 'jasper',
            'kingdom', 'lantern', 'marble', 'neutron', 'oracle', 'plasma',
            'quantum', 'rainbow', 'silver', 'temple', 'uranium', 'velvet'
        ]

        selected = [secrets.choice(word_list) for _ in range(words)]
        if capitalize:
            selected = [w.capitalize() for w in selected]

        return separator.join(selected)

    def generate_pin(self, length: int = 6) -> str:
        """Generate a numeric PIN."""
        return ''.join(secrets.choice(string.digits) for _ in range(length))

    def check_strength(self, password: str) -> Dict[str, Any]:
        """Check password strength."""
        score = 0
        feedback = []

        # Length
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters")
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1

        # Character types
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in self.SPECIAL for c in password)

        if has_lower:
            score += 1
        else:
            feedback.append("Add lowercase letters")
        if has_upper:
            score += 1
        else:
            feedback.append("Add uppercase letters")
        if has_digit:
            score += 1
        else:
            feedback.append("Add numbers")
        if has_special:
            score += 1
        else:
            feedback.append("Add special characters")

        # Variety
        unique_chars = len(set(password))
        if unique_chars >= len(password) * 0.6:
            score += 1

        # Common patterns
        if password.lower() in ['password', '123456', 'qwerty', 'admin']:
            score = 0
            feedback = ["Password is too common"]

        # Rating
        if score <= 2:
            rating = 'weak'
        elif score <= 4:
            rating = 'fair'
        elif score <= 6:
            rating = 'good'
        else:
            rating = 'strong'

        return {
            'score': score,
            'max_score': 8,
            'rating': rating,
            'length': len(password),
            'unique_characters': unique_chars,
            'has_lowercase': has_lower,
            'has_uppercase': has_upper,
            'has_digits': has_digit,
            'has_special': has_special,
            'feedback': feedback
        }

    def hash_password(self, password: str, salt: Optional[bytes] = None,
                      iterations: int = 100000) -> Tuple[str, str]:
        """Hash password using PBKDF2."""
        if salt is None:
            salt = os.urandom(16)

        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            iterations,
            dklen=32
        )

        return binascii.hexlify(key).decode(), binascii.hexlify(salt).decode()

    def verify_password(self, password: str, hash_hex: str, salt_hex: str,
                        iterations: int = 100000) -> bool:
        """Verify password against hash."""
        salt = binascii.unhexlify(salt_hex)
        expected, _ = self.hash_password(password, salt, iterations)
        return hmac.compare_digest(expected, hash_hex)


class SecureRandom:
    """Secure random generation utilities."""

    def random_bytes(self, length: int) -> bytes:
        """Generate random bytes."""
        return os.urandom(length)

    def random_hex(self, length: int) -> str:
        """Generate random hex string."""
        return secrets.token_hex(length // 2)

    def random_urlsafe(self, length: int) -> str:
        """Generate URL-safe random string."""
        return secrets.token_urlsafe(length)

    def random_int(self, min_val: int, max_val: int) -> int:
        """Generate random integer in range."""
        return secrets.randbelow(max_val - min_val + 1) + min_val

    def random_choice(self, items: list) -> Any:
        """Randomly select from list."""
        return secrets.choice(items)

    def random_uuid(self) -> str:
        """Generate a random UUID v4."""
        rand_bytes = os.urandom(16)
        # Set version to 4
        rand_bytes = bytearray(rand_bytes)
        rand_bytes[6] = (rand_bytes[6] & 0x0f) | 0x40
        rand_bytes[8] = (rand_bytes[8] & 0x3f) | 0x80

        hex_str = binascii.hexlify(rand_bytes).decode()
        return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:]}"


class SimpleEncryption:
    """Simple encryption utilities (XOR-based for demo - use real crypto in production)."""

    def xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        """XOR encrypt data with key."""
        return bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))

    def xor_decrypt(self, data: bytes, key: bytes) -> bytes:
        """XOR decrypt data with key."""
        return self.xor_encrypt(data, key)  # XOR is symmetric

    def derive_key(self, password: str, salt: bytes, length: int = 32) -> bytes:
        """Derive key from password using PBKDF2."""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000, dklen=length)


class CryptoToolkit:
    """Main cryptography toolkit."""

    def __init__(self):
        self.hashing = HashingTools()
        self.encoding = EncodingTools()
        self.passwords = PasswordTools()
        self.random = SecureRandom()
        self.encryption = SimpleEncryption()

    def quick_hash(self, data: str, algorithm: str = 'sha256') -> str:
        """Quick hash of string data."""
        return self.hashing.hash_string(data, algorithm)

    def quick_encode(self, data: str, encoding: str = 'base64') -> str:
        """Quick encode string data."""
        if encoding == 'base64':
            return self.encoding.base64_encode(data)
        elif encoding == 'hex':
            return self.encoding.hex_encode(data)
        elif encoding == 'base32':
            return self.encoding.base32_encode(data)
        else:
            raise ValueError(f"Unknown encoding: {encoding}")

    def quick_decode(self, data: str, encoding: str = 'base64') -> str:
        """Quick decode string data."""
        if encoding == 'base64':
            return self.encoding.base64_decode(data).decode('utf-8')
        elif encoding == 'hex':
            return self.encoding.hex_decode(data).decode('utf-8')
        elif encoding == 'base32':
            return self.encoding.base32_decode(data).decode('utf-8')
        else:
            raise ValueError(f"Unknown encoding: {encoding}")


def main():
    """Command-line demo."""
    print("=" * 60)
    print("CRYPTOGRAPHY TOOLKIT")
    print("=" * 60)
    print()

    toolkit = CryptoToolkit()

    # Hashing Demo
    print("1. HASHING DEMO")
    print("-" * 40)
    test_data = "Hello, World!"
    print(f"Input: {test_data}")
    print(f"MD5:    {toolkit.hashing.hash_string(test_data, 'md5')}")
    print(f"SHA1:   {toolkit.hashing.hash_string(test_data, 'sha1')}")
    print(f"SHA256: {toolkit.hashing.hash_string(test_data, 'sha256')}")
    print()

    # HMAC Demo
    print("2. HMAC DEMO")
    print("-" * 40)
    key = b"secret_key"
    message = b"Important message"
    signature = toolkit.hashing.hmac_sign(key, message)
    verified = toolkit.hashing.hmac_verify(key, message, signature)
    print(f"Message: {message.decode()}")
    print(f"Signature: {signature[:32]}...")
    print(f"Verified: {verified}")
    print()

    # Encoding Demo
    print("3. ENCODING DEMO")
    print("-" * 40)
    text = "Hello, Crypto!"
    print(f"Original: {text}")
    print(f"Base64:   {toolkit.encoding.base64_encode(text)}")
    print(f"Hex:      {toolkit.encoding.hex_encode(text)}")
    print(f"Base32:   {toolkit.encoding.base32_encode(text)}")
    print(f"ROT13:    {toolkit.encoding.rot13(text)}")
    print()

    # Password Generation
    print("4. PASSWORD GENERATION")
    print("-" * 40)
    print(f"Password (16 chars): {toolkit.passwords.generate_password(16)}")
    print(f"Password (no special): {toolkit.passwords.generate_password(16, special=False)}")
    print(f"Passphrase: {toolkit.passwords.generate_passphrase(4)}")
    print(f"PIN (6 digits): {toolkit.passwords.generate_pin(6)}")
    print()

    # Password Strength
    print("5. PASSWORD STRENGTH CHECK")
    print("-" * 40)
    passwords = ["password123", "MyP@ss2024!", "Xk9#mN2$pL7@qR4"]
    for pwd in passwords:
        strength = toolkit.passwords.check_strength(pwd)
        print(f"  '{pwd}': {strength['rating']} ({strength['score']}/{strength['max_score']})")
    print()

    # Secure Random
    print("6. SECURE RANDOM")
    print("-" * 40)
    print(f"Random hex (16): {toolkit.random.random_hex(16)}")
    print(f"Random URL-safe: {toolkit.random.random_urlsafe(16)}")
    print(f"Random UUID: {toolkit.random.random_uuid()}")
    print(f"Random int (1-100): {toolkit.random.random_int(1, 100)}")
    print()

    # Password Hashing
    print("7. PASSWORD HASHING")
    print("-" * 40)
    password = "MySecretPassword"
    hash_val, salt = toolkit.passwords.hash_password(password)
    verified = toolkit.passwords.verify_password(password, hash_val, salt)
    print(f"Password: {password}")
    print(f"Hash: {hash_val[:32]}...")
    print(f"Salt: {salt}")
    print(f"Verified: {verified}")
    print()

    print("=" * 60)
    print("Cryptography Toolkit Demo Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
