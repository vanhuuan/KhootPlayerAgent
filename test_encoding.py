#!/usr/bin/env python3
"""
Test script for encoding detection and decoding functionality
"""

from encoding_helper import handle_encoded_question, detect_and_decode, extract_encoded_string
import base64

def test_base64_encoding():
    """Test Base64 encoding detection and decoding"""
    print("🧪 Testing Base64 encoding...")
    
    # Test the example from the user
    test_question = "Select the right answer for this questions that encoded in Base64: d2hhdCBpcyB0aGUgcmVzdWx0IG9mIDErMT8="
    
    print(f"Original question: {test_question}")
    
    # Test extraction
    encoded_string = extract_encoded_string(test_question)
    print(f"Extracted string: {encoded_string}")
    
    # Test decoding
    decoded_text, encoding_type = detect_and_decode(encoded_string)
    print(f"Decoded text: {decoded_text}")
    print(f"Encoding type: {encoding_type}")
    
    # Test full handling
    full_decoded, full_type = handle_encoded_question(test_question)
    print(f"Full handling result: {full_decoded} ({full_type})")
    
    print("✅ Base64 test completed\n")

def test_other_encodings():
    """Test other encoding types"""
    print("🧪 Testing other encodings...")
    
    # Test URL encoding
    url_encoded = "What%20is%20the%20result%20of%201%2B1%3F"
    print(f"URL encoded: {url_encoded}")
    decoded, enc_type = detect_and_decode(url_encoded)
    print(f"Decoded: {decoded} ({enc_type})")
    
    # Test HTML entities
    html_encoded = "What is the result of 1&plus;1&quest;"
    print(f"HTML encoded: {html_encoded}")
    decoded, enc_type = detect_and_decode(html_encoded)
    print(f"Decoded: {decoded} ({enc_type})")
    
    print("✅ Other encodings test completed\n")

def test_manual_base64():
    """Test manual Base64 creation and decoding"""
    print("🧪 Testing manual Base64 creation...")
    
    # Create a Base64 encoded question
    original_text = "What is the capital of France?"
    encoded = base64.b64encode(original_text.encode('utf-8')).decode('utf-8')
    
    print(f"Original: {original_text}")
    print(f"Base64 encoded: {encoded}")
    
    # Test our decoding
    decoded, enc_type = detect_and_decode(encoded)
    print(f"Our decoded: {decoded} ({enc_type})")
    
    # Test with question format
    question_with_encoded = f"Decode this Base64 string: {encoded}"
    full_decoded, full_type = handle_encoded_question(question_with_encoded)
    print(f"Full question handling: {full_decoded} ({full_type})")
    
    print("✅ Manual Base64 test completed\n")

if __name__ == "__main__":
    print("🔐 Testing Encoding/Decoding Functionality\n")
    
    test_base64_encoding()
    test_other_encodings()
    test_manual_base64()
    
    print("🎉 All encoding tests completed!") 