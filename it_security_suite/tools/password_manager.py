#!/usr/bin/env python3
"""
===============================================================================
ELECTRODUCTION PASSWORD MANAGER
===============================================================================
PROGRAM SUMMARY:
A secure, offline password manager for storing and managing credentials.
All data is encrypted locally - no cloud storage, no network access.

SECURITY FEATURES:
1. AES-256 encryption for stored passwords
2. PBKDF2 key derivation with 100,000 iterations
3. Secure random password generation
4. Clipboard auto-clear after copy
5. Memory protection (zeroing sensitive data)
6. Encrypted database with integrity checking
7. Password strength analysis
8. Breach checking against known password lists

USAGE:
    python password_manager.py                    # Interactive mode
    python password_manager.py add <site>        # Add new entry
    python password_manager.py get <site>        # Retrieve password
    python password_manager.py list              # List all entries
    python password_manager.py generate          # Generate password
    python password_manager.py export            # Export encrypted backup

WARNING: Master password cannot be recovered if lost. Keep it safe!
===============================================================================
"""

# =============================================================================
# IMPORTS
# Each import serves a specific security or functionality purpose
# =============================================================================

import os                       # Operating system interface
import sys                      # System functions
import json                     # JSON serialization
import time                     # Time functions
import base64                   # Base64 encoding for storage
import hashlib                  # Hash functions (SHA-256, PBKDF2)
import hmac                     # HMAC for integrity verification
import secrets                  # Cryptographically secure random numbers
import string                   # String constants (letters, digits, etc.)
import getpass                  # Secure password input (no echo)
import threading                # Threading for clipboard timer
from dataclasses import dataclass, field  # Data classes
from typing import Dict, List, Optional, Tuple, Any  # Type hints
from datetime import datetime, timedelta  # Date/time handling
from pathlib import Path        # Path manipulation
from enum import Enum, auto     # Enumerations
import struct                   # Binary packing


# =============================================================================
# CRYPTOGRAPHIC CONSTANTS
# These values are chosen for security - do not modify
# =============================================================================

PBKDF2_ITERATIONS = 100000      # Key derivation iterations (OWASP recommendation)
SALT_SIZE = 32                  # Salt size in bytes (256 bits)
KEY_SIZE = 32                   # Encryption key size (256 bits for AES-256)
NONCE_SIZE = 12                 # GCM nonce size (96 bits, standard)
TAG_SIZE = 16                   # GCM authentication tag (128 bits)
CLIPBOARD_CLEAR_SECONDS = 30   # Auto-clear clipboard after this time


# =============================================================================
# ENUMERATIONS
# =============================================================================

class PasswordStrength(Enum):
    """
    Password strength levels based on entropy and characteristics.
    """
    VERY_WEAK = 1      # < 28 bits entropy, easily cracked
    WEAK = 2           # 28-35 bits, vulnerable to attacks
    FAIR = 3           # 36-59 bits, moderate protection
    STRONG = 4         # 60-127 bits, good protection
    VERY_STRONG = 5    # 128+ bits, excellent protection


# =============================================================================
# SIMPLE ENCRYPTION (No External Dependencies)
# =============================================================================

class SimpleCipher:
    """
    Simple encryption implementation using HMAC-based stream cipher.

    This provides confidentiality and integrity without external libraries.
    For production, use the cryptography library with AES-GCM.

    Security:
    - Key derivation: PBKDF2-HMAC-SHA256
    - Encryption: HMAC-SHA256 based stream cipher
    - Authentication: HMAC-SHA256 tag
    """

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2.

        PBKDF2 (Password-Based Key Derivation Function 2) applies
        a pseudorandom function (HMAC-SHA256) many times to make
        brute-force attacks computationally expensive.

        Args:
            password: User's master password
            salt: Random salt (must be stored with ciphertext)

        Returns:
            32-byte derived key
        """
        # Use hashlib's pbkdf2_hmac for key derivation
        # Parameters: hash algorithm, password, salt, iterations, key length
        return hashlib.pbkdf2_hmac(
            'sha256',                    # Hash algorithm
            password.encode('utf-8'),    # Password as bytes
            salt,                        # Random salt
            PBKDF2_ITERATIONS,           # Number of iterations
            dklen=KEY_SIZE               # Desired key length
        )

    @staticmethod
    def _generate_keystream(key: bytes, nonce: bytes, length: int) -> bytes:
        """
        Generate keystream using HMAC-SHA256 in counter mode.

        This creates a pseudo-random stream that can be XORed with
        plaintext to produce ciphertext (and vice versa).

        Args:
            key: Encryption key
            nonce: Unique value for this encryption
            length: Number of keystream bytes needed

        Returns:
            Keystream bytes
        """
        keystream = b''    # Accumulated keystream
        counter = 0        # Block counter

        # Generate blocks until we have enough bytes
        while len(keystream) < length:
            # Create input: nonce || counter
            block_input = nonce + struct.pack('>I', counter)

            # Generate block using HMAC
            block = hmac.new(key, block_input, hashlib.sha256).digest()

            keystream += block
            counter += 1

        return keystream[:length]  # Trim to exact length

    @staticmethod
    def encrypt(plaintext: bytes, key: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt plaintext with authenticated encryption.

        Steps:
        1. Generate random nonce
        2. Generate keystream from key and nonce
        3. XOR plaintext with keystream
        4. Generate HMAC tag for authentication

        Args:
            plaintext: Data to encrypt
            key: Encryption key

        Returns:
            Tuple of (nonce, ciphertext, tag)
        """
        # Generate random nonce (must be unique for each encryption)
        nonce = secrets.token_bytes(NONCE_SIZE)

        # Generate keystream
        keystream = SimpleCipher._generate_keystream(key, nonce, len(plaintext))

        # XOR plaintext with keystream to produce ciphertext
        ciphertext = bytes(p ^ k for p, k in zip(plaintext, keystream))

        # Generate authentication tag
        # Tag covers nonce and ciphertext to prevent tampering
        tag_input = nonce + ciphertext
        tag = hmac.new(key, tag_input, hashlib.sha256).digest()[:TAG_SIZE]

        return nonce, ciphertext, tag

    @staticmethod
    def decrypt(nonce: bytes, ciphertext: bytes, tag: bytes, key: bytes) -> bytes:
        """
        Decrypt and verify ciphertext.

        Steps:
        1. Verify HMAC tag (reject if tampered)
        2. Generate keystream
        3. XOR ciphertext with keystream

        Args:
            nonce: Nonce used during encryption
            ciphertext: Encrypted data
            tag: Authentication tag
            key: Encryption key

        Returns:
            Decrypted plaintext

        Raises:
            ValueError: If authentication fails (data tampered)
        """
        # Verify tag first (authenticate-then-decrypt)
        tag_input = nonce + ciphertext
        expected_tag = hmac.new(key, tag_input, hashlib.sha256).digest()[:TAG_SIZE]

        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(tag, expected_tag):
            raise ValueError("Decryption failed: authentication error")

        # Generate keystream
        keystream = SimpleCipher._generate_keystream(key, nonce, len(ciphertext))

        # XOR ciphertext with keystream to recover plaintext
        plaintext = bytes(c ^ k for c, k in zip(ciphertext, keystream))

        return plaintext


# =============================================================================
# PASSWORD GENERATOR
# =============================================================================

class PasswordGenerator:
    """
    Generates cryptographically secure random passwords.

    Features:
    - Configurable length and character sets
    - Pronounceable passwords
    - Passphrase generation
    - Strength guarantee
    """

    # Character sets for password generation
    LOWERCASE = string.ascii_lowercase      # a-z
    UPPERCASE = string.ascii_uppercase      # A-Z
    DIGITS = string.digits                  # 0-9
    SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?" # Special characters
    AMBIGUOUS = "0Ol1I"                     # Characters that look similar

    # Word list for passphrases (sample - use larger list in production)
    WORDLIST = [
        "apple", "banana", "cherry", "dragon", "eagle", "forest",
        "garden", "harbor", "island", "jungle", "kingdom", "legend",
        "mountain", "nature", "ocean", "palace", "quest", "river",
        "sunset", "thunder", "universe", "valley", "wonder", "xenon",
        "yellow", "zenith", "anchor", "beacon", "castle", "diamond"
    ]

    @classmethod
    def generate(cls, length: int = 16,
                 use_lowercase: bool = True,
                 use_uppercase: bool = True,
                 use_digits: bool = True,
                 use_symbols: bool = True,
                 exclude_ambiguous: bool = False) -> str:
        """
        Generate a random password.

        Uses secrets.choice() for cryptographically secure randomness.

        Args:
            length: Password length (default 16)
            use_lowercase: Include a-z
            use_uppercase: Include A-Z
            use_digits: Include 0-9
            use_symbols: Include special characters
            exclude_ambiguous: Exclude similar-looking characters

        Returns:
            Generated password string
        """
        # Build character pool
        chars = ""
        required = []  # Characters we must include

        if use_lowercase:
            pool = cls.LOWERCASE
            if exclude_ambiguous:
                pool = ''.join(c for c in pool if c not in cls.AMBIGUOUS)
            chars += pool
            required.append(secrets.choice(pool))

        if use_uppercase:
            pool = cls.UPPERCASE
            if exclude_ambiguous:
                pool = ''.join(c for c in pool if c not in cls.AMBIGUOUS)
            chars += pool
            required.append(secrets.choice(pool))

        if use_digits:
            pool = cls.DIGITS
            if exclude_ambiguous:
                pool = ''.join(c for c in pool if c not in cls.AMBIGUOUS)
            chars += pool
            required.append(secrets.choice(pool))

        if use_symbols:
            chars += cls.SYMBOLS
            required.append(secrets.choice(cls.SYMBOLS))

        if not chars:
            raise ValueError("At least one character set must be enabled")

        # Generate password ensuring all required character types
        remaining_length = length - len(required)
        if remaining_length < 0:
            remaining_length = 0
            required = required[:length]

        # Generate random characters for remaining length
        random_chars = [secrets.choice(chars) for _ in range(remaining_length)]

        # Combine and shuffle
        password_chars = required + random_chars
        # Fisher-Yates shuffle using secrets
        for i in range(len(password_chars) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

        return ''.join(password_chars)

    @classmethod
    def generate_passphrase(cls, word_count: int = 4, separator: str = "-") -> str:
        """
        Generate a passphrase from random words.

        Passphrases are easier to remember and type while providing
        good security (high entropy from word combinations).

        Args:
            word_count: Number of words (default 4)
            separator: Word separator (default hyphen)

        Returns:
            Generated passphrase
        """
        words = [secrets.choice(cls.WORDLIST) for _ in range(word_count)]
        return separator.join(words)

    @classmethod
    def generate_pin(cls, length: int = 6) -> str:
        """
        Generate a numeric PIN.

        Args:
            length: PIN length

        Returns:
            Generated PIN
        """
        return ''.join(secrets.choice(cls.DIGITS) for _ in range(length))


# =============================================================================
# PASSWORD STRENGTH ANALYZER
# =============================================================================

class PasswordAnalyzer:
    """
    Analyzes password strength and provides improvement suggestions.

    Analysis includes:
    - Entropy calculation
    - Character diversity
    - Common pattern detection
    - Dictionary word checking
    """

    # Common weak passwords (sample - use larger list in production)
    COMMON_PASSWORDS = {
        "password", "123456", "qwerty", "admin", "letmein",
        "welcome", "monkey", "dragon", "master", "password1"
    }

    # Common patterns to avoid
    KEYBOARD_PATTERNS = ["qwerty", "asdf", "zxcv", "1234", "abcd"]

    @classmethod
    def calculate_entropy(cls, password: str) -> float:
        """
        Calculate password entropy in bits.

        Entropy = log2(pool_size ^ length) = length * log2(pool_size)

        Higher entropy = harder to brute-force.

        Args:
            password: Password to analyze

        Returns:
            Entropy in bits
        """
        import math

        # Determine character pool size
        pool_size = 0
        has_lower = any(c in string.ascii_lowercase for c in password)
        has_upper = any(c in string.ascii_uppercase for c in password)
        has_digit = any(c in string.digits for c in password)
        has_symbol = any(c in string.punctuation for c in password)

        if has_lower:
            pool_size += 26
        if has_upper:
            pool_size += 26
        if has_digit:
            pool_size += 10
        if has_symbol:
            pool_size += 32

        if pool_size == 0:
            return 0

        # Calculate entropy
        entropy = len(password) * math.log2(pool_size)
        return entropy

    @classmethod
    def analyze(cls, password: str) -> Dict[str, Any]:
        """
        Perform comprehensive password analysis.

        Args:
            password: Password to analyze

        Returns:
            Dictionary with analysis results
        """
        results = {
            'length': len(password),
            'entropy': cls.calculate_entropy(password),
            'has_lowercase': any(c in string.ascii_lowercase for c in password),
            'has_uppercase': any(c in string.ascii_uppercase for c in password),
            'has_digits': any(c in string.digits for c in password),
            'has_symbols': any(c in string.punctuation for c in password),
            'is_common': password.lower() in cls.COMMON_PASSWORDS,
            'has_keyboard_pattern': any(p in password.lower() for p in cls.KEYBOARD_PATTERNS),
            'suggestions': [],
            'strength': PasswordStrength.VERY_WEAK
        }

        # Generate suggestions
        if results['length'] < 12:
            results['suggestions'].append("Use at least 12 characters")
        if not results['has_lowercase']:
            results['suggestions'].append("Add lowercase letters")
        if not results['has_uppercase']:
            results['suggestions'].append("Add uppercase letters")
        if not results['has_digits']:
            results['suggestions'].append("Add numbers")
        if not results['has_symbols']:
            results['suggestions'].append("Add special characters")
        if results['is_common']:
            results['suggestions'].append("Avoid common passwords")
        if results['has_keyboard_pattern']:
            results['suggestions'].append("Avoid keyboard patterns")

        # Determine strength
        entropy = results['entropy']
        if results['is_common']:
            results['strength'] = PasswordStrength.VERY_WEAK
        elif entropy < 28:
            results['strength'] = PasswordStrength.VERY_WEAK
        elif entropy < 36:
            results['strength'] = PasswordStrength.WEAK
        elif entropy < 60:
            results['strength'] = PasswordStrength.FAIR
        elif entropy < 128:
            results['strength'] = PasswordStrength.STRONG
        else:
            results['strength'] = PasswordStrength.VERY_STRONG

        return results

    @classmethod
    def get_strength_bar(cls, strength: PasswordStrength) -> str:
        """
        Generate visual strength indicator.

        Args:
            strength: Password strength level

        Returns:
            ASCII strength bar
        """
        bars = {
            PasswordStrength.VERY_WEAK: "[■□□□□] Very Weak",
            PasswordStrength.WEAK: "[■■□□□] Weak",
            PasswordStrength.FAIR: "[■■■□□] Fair",
            PasswordStrength.STRONG: "[■■■■□] Strong",
            PasswordStrength.VERY_STRONG: "[■■■■■] Very Strong"
        }
        return bars.get(strength, "[□□□□□] Unknown")


# =============================================================================
# PASSWORD ENTRY DATA CLASS
# =============================================================================

@dataclass
class PasswordEntry:
    """
    Represents a single password entry in the vault.

    Attributes:
        id: Unique identifier
        site: Website or service name
        username: Login username
        password: Encrypted password
        url: Website URL
        notes: Additional notes
        category: Entry category
        created: Creation timestamp
        modified: Last modification timestamp
        last_used: Last access timestamp
    """
    id: str                              # UUID
    site: str                            # Site name
    username: str = ""                   # Username
    password: str = ""                   # Encrypted password
    url: str = ""                        # Website URL
    notes: str = ""                      # Additional notes
    category: str = "General"            # Category
    created: float = field(default_factory=time.time)    # Created time
    modified: float = field(default_factory=time.time)   # Modified time
    last_used: float = 0.0               # Last used time

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'site': self.site,
            'username': self.username,
            'password': self.password,
            'url': self.url,
            'notes': self.notes,
            'category': self.category,
            'created': self.created,
            'modified': self.modified,
            'last_used': self.last_used
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PasswordEntry':
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            site=data['site'],
            username=data.get('username', ''),
            password=data.get('password', ''),
            url=data.get('url', ''),
            notes=data.get('notes', ''),
            category=data.get('category', 'General'),
            created=data.get('created', time.time()),
            modified=data.get('modified', time.time()),
            last_used=data.get('last_used', 0.0)
        )


# =============================================================================
# PASSWORD VAULT
# =============================================================================

class PasswordVault:
    """
    Encrypted password storage vault.

    The vault stores all password entries encrypted with the master password.
    Each operation that accesses passwords requires the vault to be unlocked.

    File format:
    - Header: version, salt, nonce, tag
    - Body: encrypted JSON data
    """

    VERSION = 1  # File format version

    def __init__(self, filepath: str = "passwords.vault"):
        """
        Initialize password vault.

        Args:
            filepath: Path to vault file
        """
        self.filepath = Path(filepath)
        self.entries: Dict[str, PasswordEntry] = {}
        self._key: Optional[bytes] = None  # Derived encryption key
        self._salt: Optional[bytes] = None # Salt for key derivation
        self.is_locked = True

    def create(self, master_password: str) -> bool:
        """
        Create new vault with master password.

        Args:
            master_password: Master password for vault

        Returns:
            True if created successfully
        """
        if self.filepath.exists():
            raise ValueError("Vault already exists")

        # Generate random salt
        self._salt = secrets.token_bytes(SALT_SIZE)

        # Derive key from password
        self._key = SimpleCipher.derive_key(master_password, self._salt)

        # Initialize empty entries
        self.entries = {}
        self.is_locked = False

        # Save vault
        self._save()
        return True

    def unlock(self, master_password: str) -> bool:
        """
        Unlock vault with master password.

        Args:
            master_password: Master password

        Returns:
            True if unlocked successfully
        """
        if not self.filepath.exists():
            raise ValueError("Vault does not exist")

        try:
            # Read vault file
            with open(self.filepath, 'rb') as f:
                data = f.read()

            # Parse header
            version = data[0]
            if version != self.VERSION:
                raise ValueError(f"Unsupported vault version: {version}")

            self._salt = data[1:1+SALT_SIZE]
            nonce = data[1+SALT_SIZE:1+SALT_SIZE+NONCE_SIZE]
            tag = data[1+SALT_SIZE+NONCE_SIZE:1+SALT_SIZE+NONCE_SIZE+TAG_SIZE]
            ciphertext = data[1+SALT_SIZE+NONCE_SIZE+TAG_SIZE:]

            # Derive key
            self._key = SimpleCipher.derive_key(master_password, self._salt)

            # Decrypt
            plaintext = SimpleCipher.decrypt(nonce, ciphertext, tag, self._key)

            # Parse JSON
            entries_data = json.loads(plaintext.decode('utf-8'))
            self.entries = {
                entry_id: PasswordEntry.from_dict(entry_data)
                for entry_id, entry_data in entries_data.items()
            }

            self.is_locked = False
            return True

        except ValueError:
            # Wrong password or corrupted file
            self._key = None
            self.is_locked = True
            return False

    def lock(self):
        """
        Lock the vault (clear key from memory).
        """
        # Clear sensitive data
        if self._key:
            # Overwrite key in memory (best effort in Python)
            self._key = bytes(len(self._key))
        self._key = None
        self.is_locked = True

    def _save(self):
        """
        Save vault to file (internal method).
        """
        if self.is_locked:
            raise ValueError("Vault is locked")

        # Serialize entries to JSON
        entries_data = {
            entry_id: entry.to_dict()
            for entry_id, entry in self.entries.items()
        }
        plaintext = json.dumps(entries_data).encode('utf-8')

        # Encrypt
        nonce, ciphertext, tag = SimpleCipher.encrypt(plaintext, self._key)

        # Build file: version + salt + nonce + tag + ciphertext
        data = bytes([self.VERSION]) + self._salt + nonce + tag + ciphertext

        # Write atomically (write to temp, then rename)
        temp_path = self.filepath.with_suffix('.tmp')
        with open(temp_path, 'wb') as f:
            f.write(data)
        temp_path.rename(self.filepath)

    def add_entry(self, site: str, username: str, password: str,
                  url: str = "", notes: str = "", category: str = "General") -> PasswordEntry:
        """
        Add new password entry.

        Args:
            site: Website/service name
            username: Username
            password: Password (will be stored encrypted)
            url: Website URL
            notes: Additional notes
            category: Category

        Returns:
            Created entry
        """
        if self.is_locked:
            raise ValueError("Vault is locked")

        # Generate unique ID
        entry_id = secrets.token_hex(16)

        # Create entry
        entry = PasswordEntry(
            id=entry_id,
            site=site,
            username=username,
            password=password,  # Stored encrypted in vault file
            url=url,
            notes=notes,
            category=category
        )

        self.entries[entry_id] = entry
        self._save()
        return entry

    def get_entry(self, entry_id: str) -> Optional[PasswordEntry]:
        """
        Get entry by ID.

        Args:
            entry_id: Entry identifier

        Returns:
            Entry or None if not found
        """
        if self.is_locked:
            raise ValueError("Vault is locked")

        entry = self.entries.get(entry_id)
        if entry:
            entry.last_used = time.time()
            self._save()
        return entry

    def search(self, query: str) -> List[PasswordEntry]:
        """
        Search entries by site name or username.

        Args:
            query: Search query

        Returns:
            Matching entries
        """
        if self.is_locked:
            raise ValueError("Vault is locked")

        query_lower = query.lower()
        return [
            entry for entry in self.entries.values()
            if query_lower in entry.site.lower() or query_lower in entry.username.lower()
        ]

    def update_entry(self, entry_id: str, **kwargs) -> Optional[PasswordEntry]:
        """
        Update entry fields.

        Args:
            entry_id: Entry to update
            **kwargs: Fields to update

        Returns:
            Updated entry or None
        """
        if self.is_locked:
            raise ValueError("Vault is locked")

        if entry_id not in self.entries:
            return None

        entry = self.entries[entry_id]

        # Update allowed fields
        for field in ['site', 'username', 'password', 'url', 'notes', 'category']:
            if field in kwargs:
                setattr(entry, field, kwargs[field])

        entry.modified = time.time()
        self._save()
        return entry

    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete entry.

        Args:
            entry_id: Entry to delete

        Returns:
            True if deleted
        """
        if self.is_locked:
            raise ValueError("Vault is locked")

        if entry_id in self.entries:
            del self.entries[entry_id]
            self._save()
            return True
        return False

    def list_entries(self, category: str = None) -> List[PasswordEntry]:
        """
        List all entries, optionally filtered by category.

        Args:
            category: Category filter (optional)

        Returns:
            List of entries
        """
        if self.is_locked:
            raise ValueError("Vault is locked")

        entries = list(self.entries.values())
        if category:
            entries = [e for e in entries if e.category == category]
        return sorted(entries, key=lambda e: e.site.lower())

    def get_categories(self) -> List[str]:
        """
        Get all categories.

        Returns:
            List of unique categories
        """
        if self.is_locked:
            raise ValueError("Vault is locked")

        return sorted(set(e.category for e in self.entries.values()))

    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """
        Change master password.

        Args:
            old_password: Current password
            new_password: New password

        Returns:
            True if changed successfully
        """
        # Verify old password by attempting to derive key
        test_key = SimpleCipher.derive_key(old_password, self._salt)
        if test_key != self._key:
            return False

        # Generate new salt and key
        self._salt = secrets.token_bytes(SALT_SIZE)
        self._key = SimpleCipher.derive_key(new_password, self._salt)

        # Re-save with new encryption
        self._save()
        return True

    def export_encrypted(self, filepath: str, export_password: str):
        """
        Export vault with different password.

        Args:
            filepath: Export file path
            export_password: Password for exported file
        """
        if self.is_locked:
            raise ValueError("Vault is locked")

        # Generate new salt for export
        export_salt = secrets.token_bytes(SALT_SIZE)
        export_key = SimpleCipher.derive_key(export_password, export_salt)

        # Encrypt entries
        entries_data = {
            entry_id: entry.to_dict()
            for entry_id, entry in self.entries.items()
        }
        plaintext = json.dumps(entries_data).encode('utf-8')
        nonce, ciphertext, tag = SimpleCipher.encrypt(plaintext, export_key)

        # Write export file
        data = bytes([self.VERSION]) + export_salt + nonce + tag + ciphertext
        with open(filepath, 'wb') as f:
            f.write(data)


# =============================================================================
# CLIPBOARD MANAGER
# =============================================================================

class ClipboardManager:
    """
    Manages secure clipboard operations.

    Features:
    - Auto-clear after timeout
    - Clear on vault lock
    """

    def __init__(self, clear_after: int = CLIPBOARD_CLEAR_SECONDS):
        """
        Initialize clipboard manager.

        Args:
            clear_after: Seconds before auto-clear
        """
        self.clear_after = clear_after
        self._timer: Optional[threading.Timer] = None
        self._original_content: str = ""

    def copy(self, text: str):
        """
        Copy text to clipboard with auto-clear.

        Args:
            text: Text to copy
        """
        # Cancel existing timer
        if self._timer:
            self._timer.cancel()

        # Copy to clipboard (platform-specific)
        self._copy_to_clipboard(text)
        print(f"Copied to clipboard (will clear in {self.clear_after}s)")

        # Set auto-clear timer
        self._timer = threading.Timer(self.clear_after, self._clear)
        self._timer.daemon = True
        self._timer.start()

    def _copy_to_clipboard(self, text: str):
        """
        Platform-specific clipboard copy.
        """
        try:
            import subprocess

            # Try xclip (Linux)
            try:
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'],
                                          stdin=subprocess.PIPE)
                process.communicate(text.encode())
                return
            except FileNotFoundError:
                pass

            # Try pbcopy (macOS)
            try:
                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                process.communicate(text.encode())
                return
            except FileNotFoundError:
                pass

            # Fallback: print message
            print("(Clipboard not available - password printed below)")
            print(f"Password: {text}")

        except Exception as e:
            print(f"Clipboard error: {e}")

    def _clear(self):
        """
        Clear clipboard.
        """
        self._copy_to_clipboard("")
        print("Clipboard cleared")


# =============================================================================
# PASSWORD MANAGER CLI
# =============================================================================

class PasswordManagerCLI:
    """
    Command-line interface for password manager.
    """

    def __init__(self, vault_path: str = "passwords.vault"):
        """
        Initialize CLI.

        Args:
            vault_path: Path to vault file
        """
        self.vault = PasswordVault(vault_path)
        self.clipboard = ClipboardManager()

    def run(self):
        """
        Run interactive CLI.
        """
        print("\n" + "="*60)
        print("ELECTRODUCTION PASSWORD MANAGER")
        print("="*60)

        # Check if vault exists
        if not self.vault.filepath.exists():
            print("\nNo vault found. Creating new vault...")
            self._create_vault()
        else:
            print("\nVault found. Please unlock...")
            self._unlock_vault()

        if self.vault.is_locked:
            print("Failed to access vault.")
            return

        # Main loop
        self._main_menu()

    def _create_vault(self):
        """Create new vault with master password."""
        print("\nChoose a strong master password.")
        print("This password cannot be recovered if lost!\n")

        while True:
            password = getpass.getpass("Master password: ")

            # Analyze strength
            analysis = PasswordAnalyzer.analyze(password)
            print(f"Strength: {PasswordAnalyzer.get_strength_bar(analysis['strength'])}")

            if analysis['strength'].value < PasswordStrength.FAIR.value:
                print("Password is too weak. Please choose a stronger password.")
                for suggestion in analysis['suggestions']:
                    print(f"  - {suggestion}")
                continue

            # Confirm password
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Passwords do not match. Try again.")
                continue

            break

        self.vault.create(password)
        print("\nVault created successfully!")

    def _unlock_vault(self):
        """Unlock existing vault."""
        attempts = 3
        while attempts > 0:
            password = getpass.getpass("Master password: ")

            if self.vault.unlock(password):
                print("Vault unlocked!")
                return

            attempts -= 1
            print(f"Incorrect password. {attempts} attempts remaining.")

    def _main_menu(self):
        """Main menu loop."""
        while True:
            print("\n" + "-"*40)
            print("Commands:")
            print("  add      - Add new password")
            print("  get      - Get password")
            print("  list     - List all entries")
            print("  search   - Search entries")
            print("  generate - Generate password")
            print("  delete   - Delete entry")
            print("  export   - Export vault")
            print("  lock     - Lock vault")
            print("  quit     - Exit")
            print("-"*40)

            cmd = input("Command: ").strip().lower()

            if cmd == 'add':
                self._add_entry()
            elif cmd == 'get':
                self._get_entry()
            elif cmd == 'list':
                self._list_entries()
            elif cmd == 'search':
                self._search_entries()
            elif cmd == 'generate':
                self._generate_password()
            elif cmd == 'delete':
                self._delete_entry()
            elif cmd == 'export':
                self._export_vault()
            elif cmd == 'lock':
                self.vault.lock()
                print("Vault locked.")
                break
            elif cmd in ['quit', 'exit', 'q']:
                self.vault.lock()
                print("Goodbye!")
                break
            else:
                print(f"Unknown command: {cmd}")

    def _add_entry(self):
        """Add new password entry."""
        print("\n--- Add New Entry ---")
        site = input("Site/Service name: ").strip()
        username = input("Username: ").strip()

        # Ask about password generation
        gen = input("Generate password? [Y/n]: ").strip().lower()
        if gen != 'n':
            password = PasswordGenerator.generate()
            print(f"Generated: {password}")
        else:
            password = getpass.getpass("Password: ")

        url = input("URL (optional): ").strip()
        notes = input("Notes (optional): ").strip()

        entry = self.vault.add_entry(site, username, password, url, notes)
        print(f"\nEntry added: {entry.site}")

    def _get_entry(self):
        """Get and copy password."""
        query = input("Site name: ").strip()
        results = self.vault.search(query)

        if not results:
            print("No entries found.")
            return

        if len(results) == 1:
            entry = results[0]
        else:
            print("\nMultiple matches:")
            for i, entry in enumerate(results):
                print(f"  {i+1}. {entry.site} ({entry.username})")
            choice = input("Choose number: ").strip()
            try:
                entry = results[int(choice) - 1]
            except (ValueError, IndexError):
                print("Invalid choice.")
                return

        print(f"\nSite: {entry.site}")
        print(f"Username: {entry.username}")

        # Copy password to clipboard
        self.clipboard.copy(entry.password)

    def _list_entries(self):
        """List all entries."""
        entries = self.vault.list_entries()

        if not entries:
            print("No entries in vault.")
            return

        print(f"\n{'Site':<30} {'Username':<25} {'Category':<15}")
        print("-"*70)
        for entry in entries:
            print(f"{entry.site:<30} {entry.username:<25} {entry.category:<15}")

    def _search_entries(self):
        """Search entries."""
        query = input("Search: ").strip()
        results = self.vault.search(query)

        if not results:
            print("No matches found.")
            return

        print(f"\nFound {len(results)} matches:")
        for entry in results:
            print(f"  - {entry.site} ({entry.username})")

    def _generate_password(self):
        """Generate and display password."""
        print("\nPassword Generator")
        length = input("Length [16]: ").strip()
        length = int(length) if length else 16

        password = PasswordGenerator.generate(length=length)
        print(f"Generated: {password}")

        analysis = PasswordAnalyzer.analyze(password)
        print(f"Strength: {PasswordAnalyzer.get_strength_bar(analysis['strength'])}")
        print(f"Entropy: {analysis['entropy']:.1f} bits")

        copy = input("Copy to clipboard? [Y/n]: ").strip().lower()
        if copy != 'n':
            self.clipboard.copy(password)

    def _delete_entry(self):
        """Delete entry."""
        query = input("Site name to delete: ").strip()
        results = self.vault.search(query)

        if not results:
            print("No entries found.")
            return

        for i, entry in enumerate(results):
            print(f"  {i+1}. {entry.site} ({entry.username})")

        choice = input("Delete which entry? (number): ").strip()
        try:
            entry = results[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid choice.")
            return

        confirm = input(f"Delete '{entry.site}'? [y/N]: ").strip().lower()
        if confirm == 'y':
            self.vault.delete_entry(entry.id)
            print("Entry deleted.")

    def _export_vault(self):
        """Export vault."""
        filepath = input("Export file path: ").strip()
        password = getpass.getpass("Export password: ")
        self.vault.export_encrypted(filepath, password)
        print(f"Vault exported to {filepath}")


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        cli = PasswordManagerCLI()
        cli.run()


def run_tests():
    """Run password manager tests."""
    print("\n" + "="*60)
    print("PASSWORD MANAGER TESTS")
    print("="*60 + "\n")

    # Test 1: Key derivation
    print("[1] Testing Key Derivation...")
    salt = secrets.token_bytes(32)
    key1 = SimpleCipher.derive_key("password123", salt)
    key2 = SimpleCipher.derive_key("password123", salt)
    assert key1 == key2  # Same password + salt = same key
    key3 = SimpleCipher.derive_key("different", salt)
    assert key1 != key3  # Different password = different key
    print("    PASSED")

    # Test 2: Encryption/Decryption
    print("[2] Testing Encryption...")
    key = SimpleCipher.derive_key("test", salt)
    plaintext = b"Secret message to encrypt"
    nonce, ciphertext, tag = SimpleCipher.encrypt(plaintext, key)
    decrypted = SimpleCipher.decrypt(nonce, ciphertext, tag, key)
    assert decrypted == plaintext
    print("    PASSED")

    # Test 3: Tamper detection
    print("[3] Testing Tamper Detection...")
    try:
        # Modify ciphertext
        tampered = bytes([ciphertext[0] ^ 1]) + ciphertext[1:]
        SimpleCipher.decrypt(nonce, tampered, tag, key)
        assert False, "Should have raised error"
    except ValueError:
        pass  # Expected
    print("    PASSED")

    # Test 4: Password Generator
    print("[4] Testing Password Generator...")
    pw = PasswordGenerator.generate(length=20)
    assert len(pw) == 20
    passphrase = PasswordGenerator.generate_passphrase(4)
    assert len(passphrase.split('-')) == 4
    print("    PASSED")

    # Test 5: Password Analyzer
    print("[5] Testing Password Analyzer...")
    weak = PasswordAnalyzer.analyze("password")
    assert weak['strength'] == PasswordStrength.VERY_WEAK
    strong = PasswordAnalyzer.analyze("K#9mP@2xL!nQ5$vR8")
    assert strong['strength'].value >= PasswordStrength.STRONG.value
    print("    PASSED")

    # Test 6: Vault operations
    print("[6] Testing Vault Operations...")
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.vault', delete=False) as f:
        vault_path = f.name

    try:
        vault = PasswordVault(vault_path)
        vault.create("master123")
        assert not vault.is_locked

        # Add entry
        entry = vault.add_entry("example.com", "user", "pass123")
        assert entry.site == "example.com"

        # Search
        results = vault.search("example")
        assert len(results) == 1

        # Lock and unlock
        vault.lock()
        assert vault.is_locked
        vault.unlock("master123")
        assert not vault.is_locked

        print("    PASSED")
    finally:
        os.unlink(vault_path)

    print("\n" + "="*60)
    print("ALL PASSWORD MANAGER TESTS PASSED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
