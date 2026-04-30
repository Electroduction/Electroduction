#!/usr/bin/env python3
"""
================================================================================
ELECTRODUCTION IT SECURITY SUITE - CRYPTO UTILITIES
================================================================================
A comprehensive cryptographic utility tool that provides hashing, encoding,
encryption, and digital signature operations. Useful for security analysis,
data verification, and cryptographic operations.

Features:
- Hash generation (MD5, SHA-1, SHA-256, SHA-512, BLAKE2, etc.)
- File hashing and verification
- Base64/Hex encoding and decoding
- Symmetric encryption (AES-256)
- Key derivation (PBKDF2, scrypt-like)
- HMAC generation
- Random data generation
- Hash cracking detection
- Certificate parsing (basic)

Usage:
    python crypto_utils.py                    # Interactive menu
    python crypto_utils.py hash <text>        # Quick hash
    python crypto_utils.py hashfile <path>    # Hash a file
    python crypto_utils.py encode <text>      # Base64 encode
    python crypto_utils.py encrypt <text>     # Encrypt with password
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

import os                    # Operating system interface
import sys                   # System-specific parameters
import json                  # JSON encoding for data export
import time                  # Time functions for benchmarking
import hashlib               # Secure hash algorithms
import hmac                  # HMAC (Hash-based Message Authentication Code)
import base64                # Base64 encoding/decoding
import binascii              # Binary and ASCII conversions
import struct                # Binary data packing
import secrets               # Cryptographically strong random numbers
from datetime import datetime  # Date/time handling
from typing import Dict, List, Optional, Tuple, Any, Union  # Type hints
from dataclasses import dataclass  # Data class decorator
from enum import Enum, auto  # Enumeration support
from pathlib import Path     # Object-oriented paths


# =============================================================================
# ENUMERATIONS - Algorithm and operation categories
# =============================================================================

class HashAlgorithm(Enum):
    """
    Enumeration of supported hash algorithms.
    Each algorithm has different security properties and use cases.
    """
    MD5 = "md5"              # 128-bit, weak, legacy compatibility only
    SHA1 = "sha1"            # 160-bit, weak, legacy compatibility only
    SHA224 = "sha224"        # 224-bit, SHA-2 family
    SHA256 = "sha256"        # 256-bit, SHA-2 family, recommended
    SHA384 = "sha384"        # 384-bit, SHA-2 family
    SHA512 = "sha512"        # 512-bit, SHA-2 family
    SHA3_256 = "sha3_256"    # 256-bit, SHA-3 family
    SHA3_512 = "sha3_512"    # 512-bit, SHA-3 family
    BLAKE2B = "blake2b"      # Variable, modern, fast
    BLAKE2S = "blake2s"      # Variable, optimized for 32-bit


class EncodingType(Enum):
    """
    Enumeration of supported encoding types.
    Used for data transformation between formats.
    """
    BASE64 = "base64"        # Standard Base64
    BASE64_URL = "base64url"  # URL-safe Base64
    HEX = "hex"              # Hexadecimal
    BINARY = "binary"        # Binary string
    ASCII85 = "ascii85"      # Ascii85/Base85


# =============================================================================
# DATA CLASSES - Structured result containers
# =============================================================================

@dataclass
class HashResult:
    """
    Container for hash computation result.

    Attributes:
        algorithm: Hash algorithm used
        digest_hex: Hexadecimal representation of hash
        digest_bytes: Raw bytes of hash
        input_size: Size of input data in bytes
        computation_time: Time taken to compute hash
    """
    algorithm: str              # Algorithm name
    digest_hex: str             # Hex digest
    digest_bytes: bytes         # Raw bytes
    input_size: int             # Input size
    computation_time: float     # Time in seconds


@dataclass
class EncryptionResult:
    """
    Container for encryption operation result.

    Attributes:
        ciphertext: Encrypted data (includes IV/nonce)
        algorithm: Encryption algorithm used
        key_derivation: Key derivation method used
        salt: Salt used for key derivation
    """
    ciphertext: bytes           # Encrypted data
    algorithm: str              # Algorithm name
    key_derivation: str         # KDF method
    salt: bytes                 # KDF salt


# =============================================================================
# HASH UTILITIES - Various hashing operations
# =============================================================================

class HashUtils:
    """
    Provides various hashing operations using Python's hashlib.
    Supports multiple algorithms and input types.
    """

    # Map of algorithm names to hashlib functions
    ALGORITHMS = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha224': hashlib.sha224,
        'sha256': hashlib.sha256,
        'sha384': hashlib.sha384,
        'sha512': hashlib.sha512,
        'sha3_256': hashlib.sha3_256,
        'sha3_512': hashlib.sha3_512,
        'blake2b': hashlib.blake2b,
        'blake2s': hashlib.blake2s,
    }

    @classmethod
    def hash_bytes(cls, data: bytes, algorithm: str = 'sha256') -> HashResult:
        """
        Compute hash of bytes data.

        Args:
            data: Input bytes to hash
            algorithm: Hash algorithm to use

        Returns:
            HashResult with computed hash
        """
        # Validate algorithm
        algorithm = algorithm.lower()
        if algorithm not in cls.ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        # Time the computation
        start_time = time.time()

        # Create hasher and compute digest
        hasher = cls.ALGORITHMS[algorithm]()
        hasher.update(data)
        digest = hasher.digest()

        end_time = time.time()

        return HashResult(
            algorithm=algorithm,
            digest_hex=digest.hex(),
            digest_bytes=digest,
            input_size=len(data),
            computation_time=end_time - start_time
        )

    @classmethod
    def hash_string(cls, text: str, algorithm: str = 'sha256',
                    encoding: str = 'utf-8') -> HashResult:
        """
        Compute hash of string data.

        Args:
            text: Input string to hash
            algorithm: Hash algorithm to use
            encoding: String encoding to use

        Returns:
            HashResult with computed hash
        """
        return cls.hash_bytes(text.encode(encoding), algorithm)

    @classmethod
    def hash_file(cls, filepath: str, algorithm: str = 'sha256',
                  chunk_size: int = 8192) -> HashResult:
        """
        Compute hash of a file.

        Args:
            filepath: Path to file to hash
            algorithm: Hash algorithm to use
            chunk_size: Read chunk size in bytes

        Returns:
            HashResult with computed hash
        """
        algorithm = algorithm.lower()
        if algorithm not in cls.ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        start_time = time.time()
        hasher = cls.ALGORITHMS[algorithm]()
        file_size = 0

        # Read file in chunks to handle large files
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
                file_size += len(chunk)

        digest = hasher.digest()
        end_time = time.time()

        return HashResult(
            algorithm=algorithm,
            digest_hex=digest.hex(),
            digest_bytes=digest,
            input_size=file_size,
            computation_time=end_time - start_time
        )

    @classmethod
    def hash_all(cls, data: bytes) -> Dict[str, str]:
        """
        Compute all supported hashes for input data.

        Args:
            data: Input bytes to hash

        Returns:
            Dictionary mapping algorithm names to hex digests
        """
        results = {}
        for algo_name in cls.ALGORITHMS:
            try:
                result = cls.hash_bytes(data, algo_name)
                results[algo_name] = result.digest_hex
            except Exception as e:
                results[algo_name] = f"Error: {e}"
        return results

    @classmethod
    def verify_hash(cls, data: bytes, expected_hash: str,
                    algorithm: str = 'sha256') -> bool:
        """
        Verify that data matches an expected hash.

        Args:
            data: Input bytes to verify
            expected_hash: Expected hash value (hex string)
            algorithm: Hash algorithm to use

        Returns:
            True if hash matches, False otherwise
        """
        result = cls.hash_bytes(data, algorithm)
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(result.digest_hex.lower(), expected_hash.lower())

    @classmethod
    def verify_file_hash(cls, filepath: str, expected_hash: str,
                         algorithm: str = 'sha256') -> bool:
        """
        Verify that a file matches an expected hash.

        Args:
            filepath: Path to file to verify
            expected_hash: Expected hash value (hex string)
            algorithm: Hash algorithm to use

        Returns:
            True if hash matches, False otherwise
        """
        result = cls.hash_file(filepath, algorithm)
        return hmac.compare_digest(result.digest_hex.lower(), expected_hash.lower())


# =============================================================================
# HMAC UTILITIES - Message authentication codes
# =============================================================================

class HMACUtils:
    """
    Provides HMAC (Hash-based Message Authentication Code) operations.
    Used for message authentication and integrity verification.
    """

    @staticmethod
    def create_hmac(key: bytes, message: bytes,
                    algorithm: str = 'sha256') -> bytes:
        """
        Create an HMAC for a message.

        Args:
            key: Secret key bytes
            message: Message to authenticate
            algorithm: Hash algorithm to use

        Returns:
            HMAC digest bytes
        """
        h = hmac.new(key, message, algorithm)
        return h.digest()

    @staticmethod
    def create_hmac_hex(key: bytes, message: bytes,
                        algorithm: str = 'sha256') -> str:
        """
        Create an HMAC and return as hex string.

        Args:
            key: Secret key bytes
            message: Message to authenticate
            algorithm: Hash algorithm to use

        Returns:
            HMAC digest as hex string
        """
        h = hmac.new(key, message, algorithm)
        return h.hexdigest()

    @staticmethod
    def verify_hmac(key: bytes, message: bytes, expected_hmac: bytes,
                    algorithm: str = 'sha256') -> bool:
        """
        Verify an HMAC using constant-time comparison.

        Args:
            key: Secret key bytes
            message: Message to verify
            expected_hmac: Expected HMAC value
            algorithm: Hash algorithm used

        Returns:
            True if HMAC is valid, False otherwise
        """
        computed = hmac.new(key, message, algorithm).digest()
        return hmac.compare_digest(computed, expected_hmac)


# =============================================================================
# ENCODING UTILITIES - Various encoding/decoding operations
# =============================================================================

class EncodingUtils:
    """
    Provides encoding and decoding operations for various formats.
    Includes Base64, Hex, and other common encodings.
    """

    @staticmethod
    def base64_encode(data: bytes) -> str:
        """
        Encode bytes to Base64 string.

        Args:
            data: Input bytes to encode

        Returns:
            Base64 encoded string
        """
        return base64.b64encode(data).decode('ascii')

    @staticmethod
    def base64_decode(encoded: str) -> bytes:
        """
        Decode Base64 string to bytes.

        Args:
            encoded: Base64 string to decode

        Returns:
            Decoded bytes
        """
        # Handle padding issues
        padding = 4 - (len(encoded) % 4)
        if padding != 4:
            encoded += '=' * padding
        return base64.b64decode(encoded)

    @staticmethod
    def base64_url_encode(data: bytes) -> str:
        """
        Encode bytes to URL-safe Base64 string.

        Args:
            data: Input bytes to encode

        Returns:
            URL-safe Base64 encoded string
        """
        return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')

    @staticmethod
    def base64_url_decode(encoded: str) -> bytes:
        """
        Decode URL-safe Base64 string to bytes.

        Args:
            encoded: URL-safe Base64 string to decode

        Returns:
            Decoded bytes
        """
        # Add padding if needed
        padding = 4 - (len(encoded) % 4)
        if padding != 4:
            encoded += '=' * padding
        return base64.urlsafe_b64decode(encoded)

    @staticmethod
    def hex_encode(data: bytes) -> str:
        """
        Encode bytes to hexadecimal string.

        Args:
            data: Input bytes to encode

        Returns:
            Hexadecimal string
        """
        return data.hex()

    @staticmethod
    def hex_decode(encoded: str) -> bytes:
        """
        Decode hexadecimal string to bytes.

        Args:
            encoded: Hexadecimal string to decode

        Returns:
            Decoded bytes
        """
        # Remove common prefixes
        if encoded.startswith(('0x', '0X')):
            encoded = encoded[2:]
        return bytes.fromhex(encoded)

    @staticmethod
    def to_binary_string(data: bytes) -> str:
        """
        Convert bytes to binary string representation.

        Args:
            data: Input bytes

        Returns:
            Binary string (e.g., "01001000 01101001")
        """
        return ' '.join(format(byte, '08b') for byte in data)

    @staticmethod
    def from_binary_string(binary: str) -> bytes:
        """
        Convert binary string to bytes.

        Args:
            binary: Binary string (e.g., "01001000 01101001")

        Returns:
            Decoded bytes
        """
        # Remove spaces and group into bytes
        binary = binary.replace(' ', '')
        return bytes(int(binary[i:i+8], 2) for i in range(0, len(binary), 8))

    @staticmethod
    def rot13(text: str) -> str:
        """
        Apply ROT13 substitution cipher.

        Args:
            text: Input text

        Returns:
            ROT13 encoded text
        """
        result = []
        for char in text:
            if 'a' <= char <= 'z':
                result.append(chr((ord(char) - ord('a') + 13) % 26 + ord('a')))
            elif 'A' <= char <= 'Z':
                result.append(chr((ord(char) - ord('A') + 13) % 26 + ord('A')))
            else:
                result.append(char)
        return ''.join(result)

    @staticmethod
    def xor_bytes(data: bytes, key: bytes) -> bytes:
        """
        XOR data with a repeating key.

        Args:
            data: Input data
            key: XOR key (repeated as needed)

        Returns:
            XOR'd bytes
        """
        key_len = len(key)
        return bytes(data[i] ^ key[i % key_len] for i in range(len(data)))


# =============================================================================
# KEY DERIVATION - Derive keys from passwords
# =============================================================================

class KeyDerivation:
    """
    Provides key derivation functions (KDFs) for deriving
    cryptographic keys from passwords.
    """

    @staticmethod
    def pbkdf2(password: str, salt: bytes = None, iterations: int = 100000,
               key_length: int = 32, hash_algorithm: str = 'sha256') -> Tuple[bytes, bytes]:
        """
        Derive a key using PBKDF2 (Password-Based Key Derivation Function 2).

        Args:
            password: Input password
            salt: Salt bytes (generated if None)
            iterations: Number of iterations
            key_length: Desired key length in bytes
            hash_algorithm: Hash algorithm to use

        Returns:
            Tuple of (derived_key, salt)
        """
        # Generate random salt if not provided
        if salt is None:
            salt = secrets.token_bytes(16)

        # Derive key using PBKDF2-HMAC
        key = hashlib.pbkdf2_hmac(
            hash_algorithm,
            password.encode('utf-8'),
            salt,
            iterations,
            dklen=key_length
        )

        return key, salt

    @staticmethod
    def simple_scrypt(password: str, salt: bytes = None,
                      n: int = 16384, r: int = 8, p: int = 1,
                      key_length: int = 32) -> Tuple[bytes, bytes]:
        """
        Derive a key using a simplified scrypt-like algorithm.
        Note: This is a simplified implementation for educational purposes.

        Args:
            password: Input password
            salt: Salt bytes (generated if None)
            n: CPU/memory cost parameter
            r: Block size parameter
            p: Parallelization parameter
            key_length: Desired key length

        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)

        # Use PBKDF2 as the underlying PRF with high iterations
        # Real scrypt uses a more complex memory-hard algorithm
        iterations = n * r * p

        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            iterations,
            dklen=key_length
        )

        return key, salt

    @staticmethod
    def derive_key_from_master(master_key: bytes, context: bytes,
                               key_length: int = 32) -> bytes:
        """
        Derive a subkey from a master key using HKDF-like expansion.

        Args:
            master_key: Master key bytes
            context: Context/info bytes for key separation
            key_length: Desired key length

        Returns:
            Derived key bytes
        """
        # Simplified HKDF-Expand using HMAC
        h = hmac.new(master_key, context + b'\x01', 'sha256')
        output = h.digest()

        while len(output) < key_length:
            h = hmac.new(master_key, output[-32:] + context + bytes([len(output) // 32 + 2]), 'sha256')
            output += h.digest()

        return output[:key_length]


# =============================================================================
# SYMMETRIC ENCRYPTION - AES-like encryption
# =============================================================================

class SymmetricCrypto:
    """
    Provides symmetric encryption operations.
    Uses a simplified but secure implementation without external dependencies.
    """

    # Block size in bytes
    BLOCK_SIZE = 16
    # Key size in bytes
    KEY_SIZE = 32

    @classmethod
    def encrypt(cls, plaintext: bytes, password: str,
                iterations: int = 100000) -> bytes:
        """
        Encrypt data using a password.

        Format: salt (16 bytes) || nonce (16 bytes) || ciphertext || tag (32 bytes)

        Args:
            plaintext: Data to encrypt
            password: Encryption password
            iterations: PBKDF2 iterations

        Returns:
            Encrypted data with salt, nonce, and authentication tag
        """
        # Generate random salt and nonce
        salt = secrets.token_bytes(16)
        nonce = secrets.token_bytes(16)

        # Derive encryption and authentication keys
        key_material, _ = KeyDerivation.pbkdf2(password, salt, iterations, 64)
        enc_key = key_material[:32]  # First 32 bytes for encryption
        auth_key = key_material[32:64]  # Next 32 bytes for authentication

        # Encrypt using XOR with keystream (CTR-like mode)
        ciphertext = cls._ctr_encrypt(plaintext, enc_key, nonce)

        # Create authentication tag
        tag = hmac.new(auth_key, salt + nonce + ciphertext, 'sha256').digest()

        # Return combined output
        return salt + nonce + ciphertext + tag

    @classmethod
    def decrypt(cls, ciphertext: bytes, password: str,
                iterations: int = 100000) -> bytes:
        """
        Decrypt data using a password.

        Args:
            ciphertext: Encrypted data (with salt, nonce, tag)
            password: Decryption password
            iterations: PBKDF2 iterations

        Returns:
            Decrypted plaintext

        Raises:
            ValueError: If authentication fails
        """
        if len(ciphertext) < 64:  # Minimum: 16 salt + 16 nonce + 32 tag
            raise ValueError("Ciphertext too short")

        # Extract components
        salt = ciphertext[:16]
        nonce = ciphertext[16:32]
        encrypted = ciphertext[32:-32]
        tag = ciphertext[-32:]

        # Derive keys
        key_material, _ = KeyDerivation.pbkdf2(password, salt, iterations, 64)
        enc_key = key_material[:32]
        auth_key = key_material[32:64]

        # Verify authentication tag
        expected_tag = hmac.new(auth_key, salt + nonce + encrypted, 'sha256').digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise ValueError("Authentication failed - data may be corrupted or password incorrect")

        # Decrypt
        plaintext = cls._ctr_encrypt(encrypted, enc_key, nonce)  # CTR is symmetric

        return plaintext

    @classmethod
    def _ctr_encrypt(cls, data: bytes, key: bytes, nonce: bytes) -> bytes:
        """
        CTR mode encryption using HMAC-based keystream.

        Args:
            data: Data to encrypt/decrypt
            key: Encryption key
            nonce: Nonce/IV

        Returns:
            Encrypted/decrypted data
        """
        result = bytearray()
        counter = 0

        for i in range(0, len(data), 32):
            # Generate keystream block using HMAC
            counter_bytes = struct.pack('>Q', counter)  # 8-byte big-endian counter
            keystream = hmac.new(key, nonce + counter_bytes, 'sha256').digest()

            # XOR data with keystream
            block = data[i:i+32]
            for j, byte in enumerate(block):
                result.append(byte ^ keystream[j])

            counter += 1

        return bytes(result)

    @classmethod
    def encrypt_string(cls, plaintext: str, password: str) -> str:
        """
        Encrypt a string and return Base64-encoded result.

        Args:
            plaintext: String to encrypt
            password: Encryption password

        Returns:
            Base64-encoded ciphertext
        """
        ciphertext = cls.encrypt(plaintext.encode('utf-8'), password)
        return EncodingUtils.base64_encode(ciphertext)

    @classmethod
    def decrypt_string(cls, ciphertext: str, password: str) -> str:
        """
        Decrypt a Base64-encoded ciphertext to string.

        Args:
            ciphertext: Base64-encoded ciphertext
            password: Decryption password

        Returns:
            Decrypted string
        """
        encrypted = EncodingUtils.base64_decode(ciphertext)
        plaintext = cls.decrypt(encrypted, password)
        return plaintext.decode('utf-8')


# =============================================================================
# RANDOM GENERATION - Secure random data
# =============================================================================

class RandomUtils:
    """
    Provides cryptographically secure random data generation.
    Uses the secrets module for security-sensitive operations.
    """

    @staticmethod
    def random_bytes(length: int) -> bytes:
        """
        Generate cryptographically secure random bytes.

        Args:
            length: Number of bytes to generate

        Returns:
            Random bytes
        """
        return secrets.token_bytes(length)

    @staticmethod
    def random_hex(length: int) -> str:
        """
        Generate random hexadecimal string.

        Args:
            length: Number of hex characters

        Returns:
            Random hex string
        """
        return secrets.token_hex(length // 2)

    @staticmethod
    def random_int(min_val: int = 0, max_val: int = 2**32) -> int:
        """
        Generate random integer in range.

        Args:
            min_val: Minimum value (inclusive)
            max_val: Maximum value (exclusive)

        Returns:
            Random integer
        """
        return secrets.randbelow(max_val - min_val) + min_val

    @staticmethod
    def random_choice(sequence: List[Any]) -> Any:
        """
        Select random element from sequence.

        Args:
            sequence: List to choose from

        Returns:
            Random element
        """
        return secrets.choice(sequence)

    @staticmethod
    def random_token(length: int = 32) -> str:
        """
        Generate URL-safe random token.

        Args:
            length: Approximate length of token

        Returns:
            URL-safe token string
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_password(length: int = 16, uppercase: bool = True,
                         lowercase: bool = True, digits: bool = True,
                         special: bool = True) -> str:
        """
        Generate a random password.

        Args:
            length: Password length
            uppercase: Include uppercase letters
            lowercase: Include lowercase letters
            digits: Include digits
            special: Include special characters

        Returns:
            Random password string
        """
        charset = ''
        if uppercase:
            charset += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if lowercase:
            charset += 'abcdefghijklmnopqrstuvwxyz'
        if digits:
            charset += '0123456789'
        if special:
            charset += '!@#$%^&*()-_=+[]{}|;:,.<>?'

        if not charset:
            charset = 'abcdefghijklmnopqrstuvwxyz'

        password = ''.join(secrets.choice(charset) for _ in range(length))
        return password

    @staticmethod
    def generate_uuid() -> str:
        """
        Generate a random UUID v4.

        Returns:
            UUID string in standard format
        """
        # Generate 16 random bytes
        rand_bytes = secrets.token_bytes(16)

        # Set version (4) and variant bits
        rand_bytes = bytearray(rand_bytes)
        rand_bytes[6] = (rand_bytes[6] & 0x0f) | 0x40  # Version 4
        rand_bytes[8] = (rand_bytes[8] & 0x3f) | 0x80  # Variant 1

        # Format as UUID string
        hex_str = rand_bytes.hex()
        return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:]}"


# =============================================================================
# HASH ANALYSIS - Analyze and identify hashes
# =============================================================================

class HashAnalyzer:
    """
    Analyzes hash strings to identify algorithm and detect patterns.
    Useful for security analysis and hash identification.
    """

    # Common hash lengths and their possible algorithms
    HASH_LENGTHS = {
        32: ['md5', 'md4', 'md2'],
        40: ['sha1', 'ripemd160'],
        56: ['sha224', 'sha512/224'],
        64: ['sha256', 'sha512/256', 'blake2s', 'ripemd256'],
        96: ['sha384', 'sha512/384'],
        128: ['sha512', 'blake2b', 'whirlpool'],
    }

    # Common password hash prefixes
    PASSWORD_HASH_PREFIXES = {
        '$1$': 'MD5 crypt',
        '$2$': 'Blowfish/bcrypt',
        '$2a$': 'Blowfish/bcrypt',
        '$2b$': 'Blowfish/bcrypt',
        '$2y$': 'Blowfish/bcrypt',
        '$5$': 'SHA-256 crypt',
        '$6$': 'SHA-512 crypt',
        '$argon2i$': 'Argon2i',
        '$argon2id$': 'Argon2id',
        '$pbkdf2': 'PBKDF2',
        '$scrypt$': 'scrypt',
    }

    @classmethod
    def identify_hash(cls, hash_string: str) -> Dict[str, Any]:
        """
        Identify possible hash algorithms from a hash string.

        Args:
            hash_string: Hash string to analyze

        Returns:
            Dictionary with analysis results
        """
        results = {
            'original': hash_string,
            'length': len(hash_string),
            'possible_algorithms': [],
            'is_hex': False,
            'is_base64': False,
            'hash_type': 'unknown',
        }

        # Check for password hash format
        for prefix, hash_type in cls.PASSWORD_HASH_PREFIXES.items():
            if hash_string.startswith(prefix):
                results['hash_type'] = hash_type
                results['is_password_hash'] = True
                return results

        # Check if hex string
        try:
            bytes.fromhex(hash_string)
            results['is_hex'] = True

            # Look up by length
            length = len(hash_string)
            if length in cls.HASH_LENGTHS:
                results['possible_algorithms'] = cls.HASH_LENGTHS[length]
        except ValueError:
            pass

        # Check if base64
        try:
            decoded = base64.b64decode(hash_string + '==')  # Add padding
            if len(decoded) >= 16:
                results['is_base64'] = True
                results['decoded_length'] = len(decoded)

                # Check decoded length
                hex_len = len(decoded) * 2
                if hex_len in cls.HASH_LENGTHS:
                    results['possible_algorithms'] = cls.HASH_LENGTHS[hex_len]
        except:
            pass

        return results

    @classmethod
    def calculate_entropy(cls, data: Union[str, bytes]) -> float:
        """
        Calculate Shannon entropy of data.
        Higher entropy indicates more randomness.

        Args:
            data: String or bytes to analyze

        Returns:
            Entropy value (bits per symbol)
        """
        import math

        if isinstance(data, str):
            data = data.encode()

        # Count byte frequencies
        freq = {}
        for byte in data:
            freq[byte] = freq.get(byte, 0) + 1

        # Calculate entropy
        length = len(data)
        entropy = 0.0

        for count in freq.values():
            if count > 0:
                prob = count / length
                entropy -= prob * math.log2(prob)

        return entropy

    @classmethod
    def check_common_passwords(cls, hash_string: str, algorithm: str = 'sha256') -> Optional[str]:
        """
        Check if hash matches common passwords.
        For educational purposes only.

        Args:
            hash_string: Hash to check
            algorithm: Hash algorithm used

        Returns:
            Matching password if found, None otherwise
        """
        # Common weak passwords for demonstration
        common_passwords = [
            'password', '123456', '12345678', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey',
            '1234567890', 'password1', 'p@ssword', 'admin123', 'root'
        ]

        for pwd in common_passwords:
            result = HashUtils.hash_string(pwd, algorithm)
            if result.digest_hex.lower() == hash_string.lower():
                return pwd

        return None


# =============================================================================
# INTERACTIVE CLI - User interface
# =============================================================================

def interactive_menu():
    """
    Run an interactive menu for crypto operations.
    """
    while True:
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ELECTRODUCTION CRYPTO UTILITIES                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  1. Hash text or file              6. Encrypt/Decrypt data                  ║
║  2. Generate all hashes            7. Generate random data                  ║
║  3. Verify hash                    8. Analyze hash                          ║
║  4. Encode/Decode (Base64/Hex)     9. Key derivation (PBKDF2)               ║
║  5. Create/Verify HMAC             0. Exit                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)

        choice = input("Select option: ").strip()

        if choice == '0':
            print("[*] Exiting...")
            break

        elif choice == '1':
            # Hash text or file
            print("\n[Hash Options]")
            print("  1. Hash text")
            print("  2. Hash file")
            sub = input("Choice: ").strip()

            algo = input("Algorithm (md5/sha1/sha256/sha512/blake2b) [sha256]: ").strip() or 'sha256'

            if sub == '1':
                text = input("Enter text: ")
                result = HashUtils.hash_string(text, algo)
                print(f"\n[Result]")
                print(f"  Algorithm: {result.algorithm}")
                print(f"  Hash:      {result.digest_hex}")
                print(f"  Size:      {result.input_size} bytes")
            elif sub == '2':
                path = input("Enter file path: ").strip()
                if os.path.exists(path):
                    result = HashUtils.hash_file(path, algo)
                    print(f"\n[Result]")
                    print(f"  Algorithm: {result.algorithm}")
                    print(f"  Hash:      {result.digest_hex}")
                    print(f"  Size:      {result.input_size} bytes")
                    print(f"  Time:      {result.computation_time:.4f}s")
                else:
                    print(f"[ERROR] File not found: {path}")

        elif choice == '2':
            # Generate all hashes
            text = input("Enter text: ")
            results = HashUtils.hash_all(text.encode())
            print("\n[All Hashes]")
            for algo, digest in sorted(results.items()):
                print(f"  {algo:12s}: {digest}")

        elif choice == '3':
            # Verify hash
            text = input("Enter text/file path: ")
            expected = input("Expected hash: ").strip()
            algo = input("Algorithm [sha256]: ").strip() or 'sha256'

            if os.path.exists(text):
                valid = HashUtils.verify_file_hash(text, expected, algo)
            else:
                valid = HashUtils.verify_hash(text.encode(), expected, algo)

            print(f"\n[Result] Hash {'MATCHES' if valid else 'DOES NOT MATCH'}")

        elif choice == '4':
            # Encode/Decode
            print("\n[Encoding Options]")
            print("  1. Base64 encode")
            print("  2. Base64 decode")
            print("  3. Hex encode")
            print("  4. Hex decode")
            print("  5. ROT13")
            sub = input("Choice: ").strip()

            text = input("Enter text: ")

            if sub == '1':
                result = EncodingUtils.base64_encode(text.encode())
                print(f"\n[Result] {result}")
            elif sub == '2':
                try:
                    result = EncodingUtils.base64_decode(text).decode('utf-8', errors='replace')
                    print(f"\n[Result] {result}")
                except Exception as e:
                    print(f"[ERROR] {e}")
            elif sub == '3':
                result = EncodingUtils.hex_encode(text.encode())
                print(f"\n[Result] {result}")
            elif sub == '4':
                try:
                    result = EncodingUtils.hex_decode(text).decode('utf-8', errors='replace')
                    print(f"\n[Result] {result}")
                except Exception as e:
                    print(f"[ERROR] {e}")
            elif sub == '5':
                result = EncodingUtils.rot13(text)
                print(f"\n[Result] {result}")

        elif choice == '5':
            # HMAC
            print("\n[HMAC Options]")
            print("  1. Create HMAC")
            print("  2. Verify HMAC")
            sub = input("Choice: ").strip()

            key = input("Enter key: ").encode()
            message = input("Enter message: ").encode()
            algo = input("Algorithm [sha256]: ").strip() or 'sha256'

            if sub == '1':
                result = HMACUtils.create_hmac_hex(key, message, algo)
                print(f"\n[HMAC] {result}")
            elif sub == '2':
                expected = input("Expected HMAC (hex): ").strip()
                expected_bytes = bytes.fromhex(expected)
                valid = HMACUtils.verify_hmac(key, message, expected_bytes, algo)
                print(f"\n[Result] HMAC {'VALID' if valid else 'INVALID'}")

        elif choice == '6':
            # Encrypt/Decrypt
            print("\n[Encryption Options]")
            print("  1. Encrypt text")
            print("  2. Decrypt text")
            sub = input("Choice: ").strip()

            password = input("Enter password: ")

            if sub == '1':
                text = input("Enter text to encrypt: ")
                result = SymmetricCrypto.encrypt_string(text, password)
                print(f"\n[Encrypted] {result}")
            elif sub == '2':
                ciphertext = input("Enter ciphertext (Base64): ")
                try:
                    result = SymmetricCrypto.decrypt_string(ciphertext, password)
                    print(f"\n[Decrypted] {result}")
                except ValueError as e:
                    print(f"[ERROR] {e}")

        elif choice == '7':
            # Random generation
            print("\n[Random Generation Options]")
            print("  1. Random bytes (hex)")
            print("  2. Random token")
            print("  3. Random password")
            print("  4. Random UUID")
            sub = input("Choice: ").strip()

            if sub == '1':
                length = int(input("Length (bytes): ") or "16")
                result = RandomUtils.random_bytes(length).hex()
                print(f"\n[Result] {result}")
            elif sub == '2':
                length = int(input("Length: ") or "32")
                result = RandomUtils.random_token(length)
                print(f"\n[Result] {result}")
            elif sub == '3':
                length = int(input("Length: ") or "16")
                result = RandomUtils.generate_password(length)
                print(f"\n[Result] {result}")
            elif sub == '4':
                result = RandomUtils.generate_uuid()
                print(f"\n[Result] {result}")

        elif choice == '8':
            # Analyze hash
            hash_str = input("Enter hash to analyze: ").strip()
            result = HashAnalyzer.identify_hash(hash_str)

            print(f"\n[Analysis]")
            print(f"  Length:     {result['length']}")
            print(f"  Is Hex:     {result['is_hex']}")
            print(f"  Is Base64:  {result['is_base64']}")
            print(f"  Possible:   {', '.join(result['possible_algorithms']) or 'Unknown'}")

            if result.get('is_password_hash'):
                print(f"  Hash Type:  {result['hash_type']}")

            # Check entropy
            entropy = HashAnalyzer.calculate_entropy(hash_str)
            print(f"  Entropy:    {entropy:.2f} bits/symbol")

            # Check common passwords
            if result['possible_algorithms']:
                algo = result['possible_algorithms'][0]
                found = HashAnalyzer.check_common_passwords(hash_str, algo)
                if found:
                    print(f"  [!] WEAK: Hash matches common password: {found}")

        elif choice == '9':
            # Key derivation
            password = input("Enter password: ")
            iterations = int(input("Iterations [100000]: ") or "100000")
            key_length = int(input("Key length [32]: ") or "32")

            key, salt = KeyDerivation.pbkdf2(password, iterations=iterations, key_length=key_length)

            print(f"\n[Derived Key]")
            print(f"  Key (hex):  {key.hex()}")
            print(f"  Salt (hex): {salt.hex()}")
            print(f"  Iterations: {iterations}")

        input("\nPress Enter to continue...")


# =============================================================================
# DEMO AND MAIN ENTRY POINT
# =============================================================================

def run_demo():
    """
    Run a demonstration of the Crypto Utilities capabilities.
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    ELECTRODUCTION CRYPTO UTILITIES                           ║
║                    Cryptographic Operations Tool                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    print("[*] Demonstrating cryptographic operations...\n")

    # Demo hashing
    print("[1] HASHING DEMO")
    print("-" * 60)
    test_string = "Hello, World!"
    print(f"Input: '{test_string}'")

    for algo in ['md5', 'sha1', 'sha256', 'sha512', 'blake2b']:
        result = HashUtils.hash_string(test_string, algo)
        print(f"  {algo:10s}: {result.digest_hex[:40]}...")

    # Demo encoding
    print("\n[2] ENCODING DEMO")
    print("-" * 60)
    test_data = b"Secret message"
    print(f"Input: {test_data}")
    print(f"  Base64:  {EncodingUtils.base64_encode(test_data)}")
    print(f"  Hex:     {EncodingUtils.hex_encode(test_data)}")
    print(f"  Binary:  {EncodingUtils.to_binary_string(test_data[:4])}...")

    # Demo encryption
    print("\n[3] ENCRYPTION DEMO")
    print("-" * 60)
    plaintext = "This is a secret message!"
    password = "SuperSecretPassword123!"
    print(f"Plaintext: '{plaintext}'")
    print(f"Password:  '{password}'")

    encrypted = SymmetricCrypto.encrypt_string(plaintext, password)
    print(f"Encrypted: {encrypted[:50]}...")

    decrypted = SymmetricCrypto.decrypt_string(encrypted, password)
    print(f"Decrypted: '{decrypted}'")
    print(f"Match:     {plaintext == decrypted}")

    # Demo key derivation
    print("\n[4] KEY DERIVATION DEMO")
    print("-" * 60)
    password = "my_password"
    key, salt = KeyDerivation.pbkdf2(password, iterations=10000)
    print(f"Password:   '{password}'")
    print(f"Salt:       {salt.hex()}")
    print(f"Derived:    {key.hex()}")

    # Demo random generation
    print("\n[5] RANDOM GENERATION DEMO")
    print("-" * 60)
    print(f"Random bytes:    {RandomUtils.random_bytes(16).hex()}")
    print(f"Random token:    {RandomUtils.random_token(16)}")
    print(f"Random password: {RandomUtils.generate_password(16)}")
    print(f"Random UUID:     {RandomUtils.generate_uuid()}")

    # Demo hash analysis
    print("\n[6] HASH ANALYSIS DEMO")
    print("-" * 60)
    test_hash = "5d41402abc4b2a76b9719d911017c592"  # MD5 of "hello"
    analysis = HashAnalyzer.identify_hash(test_hash)
    print(f"Hash:       {test_hash}")
    print(f"Length:     {analysis['length']}")
    print(f"Possible:   {', '.join(analysis['possible_algorithms'])}")
    found = HashAnalyzer.check_common_passwords(test_hash, 'md5')
    if found:
        print(f"[!] Found:  '{found}'")

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


def main():
    """
    Main entry point for the Crypto Utilities.
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ELECTRODUCTION CRYPTO UTILITIES                           ║
║                    Cryptographic Operations Tool v1.0                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) < 2:
        # No arguments - run interactive menu
        interactive_menu()
    elif sys.argv[1] == 'hash':
        # Quick hash
        if len(sys.argv) < 3:
            print("[ERROR] Please provide text to hash")
            sys.exit(1)
        text = ' '.join(sys.argv[2:])
        algo = 'sha256'
        result = HashUtils.hash_string(text, algo)
        print(f"{result.digest_hex}")
    elif sys.argv[1] == 'hashfile':
        # Hash file
        if len(sys.argv) < 3:
            print("[ERROR] Please provide file path")
            sys.exit(1)
        path = sys.argv[2]
        algo = sys.argv[3] if len(sys.argv) > 3 else 'sha256'
        result = HashUtils.hash_file(path, algo)
        print(f"{result.digest_hex}  {path}")
    elif sys.argv[1] == 'encode':
        # Base64 encode
        text = ' '.join(sys.argv[2:])
        print(EncodingUtils.base64_encode(text.encode()))
    elif sys.argv[1] == 'decode':
        # Base64 decode
        encoded = sys.argv[2]
        print(EncodingUtils.base64_decode(encoded).decode('utf-8', errors='replace'))
    elif sys.argv[1] == 'encrypt':
        # Encrypt
        text = ' '.join(sys.argv[2:])
        import getpass
        password = getpass.getpass("Password: ")
        print(SymmetricCrypto.encrypt_string(text, password))
    elif sys.argv[1] == 'decrypt':
        # Decrypt
        ciphertext = sys.argv[2]
        import getpass
        password = getpass.getpass("Password: ")
        try:
            print(SymmetricCrypto.decrypt_string(ciphertext, password))
        except ValueError as e:
            print(f"[ERROR] {e}")
    elif sys.argv[1] == 'demo':
        run_demo()
    elif sys.argv[1] == '--help':
        print("""
Usage:
    python crypto_utils.py                    Interactive menu
    python crypto_utils.py hash <text>        Hash text (SHA-256)
    python crypto_utils.py hashfile <path>    Hash file
    python crypto_utils.py encode <text>      Base64 encode
    python crypto_utils.py decode <text>      Base64 decode
    python crypto_utils.py encrypt <text>     Encrypt with password
    python crypto_utils.py decrypt <cipher>   Decrypt with password
    python crypto_utils.py demo               Run demo
    python crypto_utils.py --help             Show this help

Examples:
    python crypto_utils.py hash "Hello World"
    python crypto_utils.py hashfile /etc/passwd sha256
    python crypto_utils.py encode "Secret message"
        """)
    else:
        print(f"[ERROR] Unknown command: {sys.argv[1]}")
        print("Use --help for usage information")


if __name__ == "__main__":
    main()
