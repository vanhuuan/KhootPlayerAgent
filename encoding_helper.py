import base64
import binascii
import urllib.parse
import html
import re


def detect_and_decode(text: str) -> tuple[str, str]:
    """
    Detect encoding type and decode the text.
    Returns (decoded_text, encoding_type)
    """
    text = text.strip()
    
    # Base64 detection and decoding
    if is_base64(text):
        try:
            decoded = base64.b64decode(text).decode('utf-8')
            print(f"🔐 Detected Base64 encoding: {text}")
            print(f"🔓 Decoded: {decoded}")
            return decoded, "base64"
        except Exception as e:
            print(f"Failed to decode Base64: {e}")
    
    # URL encoding detection and decoding
    if '%' in text and is_url_encoded(text):
        try:
            decoded = urllib.parse.unquote(text)
            if decoded != text:  # Only if actually decoded something
                print(f"🔐 Detected URL encoding: {text}")
                print(f"🔓 Decoded: {decoded}")
                return decoded, "url"
        except Exception as e:
            print(f"Failed to decode URL encoding: {e}")
    
    # HTML entity decoding
    if '&' in text and (';' in text):
        try:
            decoded = html.unescape(text)
            if decoded != text:  # Only if actually decoded something
                print(f"🔐 Detected HTML entities: {text}")
                print(f"🔓 Decoded: {decoded}")
                return decoded, "html"
        except Exception as e:
            print(f"Failed to decode HTML entities: {e}")
    
    # Hex decoding
    if is_hex(text):
        try:
            decoded = bytes.fromhex(text).decode('utf-8')
            print(f"🔐 Detected Hex encoding: {text}")
            print(f"🔓 Decoded: {decoded}")
            return decoded, "hex"
        except Exception as e:
            print(f"Failed to decode Hex: {e}")
    
    # ROT13 decoding
    if text.isalpha():
        try:
            decoded = text.encode('rot13')
            if decoded != text:
                print(f"🔐 Detected ROT13 encoding: {text}")
                print(f"🔓 Decoded: {decoded}")
                return decoded, "rot13"
        except Exception as e:
            print(f"Failed to decode ROT13: {e}")
    
    # No encoding detected
    return text, "none"


def is_base64(text: str) -> bool:
    """Check if text is valid Base64"""
    try:
        # Base64 strings should only contain A-Z, a-z, 0-9, +, /, and = for padding
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', text):
            return False
        
        # Length should be multiple of 4
        if len(text) % 4 != 0:
            return False
        
        # Try to decode
        base64.b64decode(text, validate=True)
        return True
    except Exception:
        return False


def is_url_encoded(text: str) -> bool:
    """Check if text contains URL encoding"""
    # Look for % followed by two hex digits
    return bool(re.search(r'%[0-9A-Fa-f]{2}', text))


def is_hex(text: str) -> bool:
    """Check if text is valid hexadecimal"""
    try:
        # Remove spaces and check if it's valid hex
        clean_text = text.replace(' ', '').replace('-', '')
        if len(clean_text) % 2 != 0:
            return False
        int(clean_text, 16)
        return len(clean_text) > 4  # Must be at least 2 bytes
    except ValueError:
        return False


def extract_encoded_string(question_text: str) -> str:
    """
    Extract the encoded string from a question.
    Looks for common patterns like "encoded in Base64: <string>"
    """
    # Common patterns for encoded questions
    patterns = [
        r'encoded in base64[:\s]+([A-Za-z0-9+/=]+)',
        r'base64[:\s]+([A-Za-z0-9+/=]+)',
        r'encoded[:\s]+([A-Za-z0-9+/=]+)',
        r'decode[:\s]+([A-Za-z0-9+/=]+)',
        r'[:\s]([A-Za-z0-9+/=]{20,})',  # Long base64-like strings
    ]
    
    question_lower = question_text.lower()
    
    for pattern in patterns:
        match = re.search(pattern, question_lower, re.IGNORECASE)
        if match:
            encoded_string = match.group(1).strip()
            print(f"🔍 Found encoded string: {encoded_string}")
            return encoded_string
    
    # If no pattern matches, look for the longest base64-like string
    words = question_text.split()
    for word in words:
        if len(word) > 10 and is_base64(word):
            print(f"🔍 Found potential Base64 string: {word}")
            return word
    
    return ""


def handle_encoded_question(question_text: str) -> tuple[str, str]:
    """
    Handle encoded questions by extracting and decoding the encoded part.
    Returns (decoded_text, encoding_type)
    """
    # First, extract the encoded string from the question
    encoded_string = extract_encoded_string(question_text)
    
    if not encoded_string:
        print("❌ No encoded string found in question")
        return question_text, "none"
    
    # Try to decode the extracted string
    decoded_text, encoding_type = detect_and_decode(encoded_string)
    
    if encoding_type != "none":
        print(f"✅ Successfully decoded {encoding_type} string")
        return decoded_text, encoding_type
    else:
        print("❌ Could not decode the extracted string")
        return question_text, "none" 