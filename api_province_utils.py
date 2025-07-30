#!/usr/bin/env python3
"""
API Province extraction utilities
"""

import re

def extract_province_from_api_response(api_response):
    """
    Extract province information from API response
    
    Args:
        api_response: Raw API response
        
    Returns:
        tuple: (province_name, confidence, region)
    """
    try:
        if not api_response or not isinstance(api_response, dict):
            return None, 0.0, 'ไม่ระบุ'
        
        # Check for province in raw_response
        raw_response = api_response.get('raw_response', {})
        if not raw_response:
            return None, 0.0, 'ไม่ระบุ'
        
        # Extract province from API
        api_province = raw_response.get('province', '')
        if not api_province:
            return None, 0.0, 'ไม่ระบุ'
        
        # Parse province format: "th-10:Bangkok (กรุงเทพมหานคร)"
        province_match = re.search(r'\(([^)]+)\)', api_province)
        if province_match:
            thai_province = province_match.group(1).strip()
            
            # Map to standardized province names and regions
            province_mapping = {
                'กรุงเทพมหานคร': ('กรุงเทพมหานคร', 'กรุงเทพและปริมณฑล'),
                'นนทบุรี': ('นนทบุรี', 'กรุงเทพและปริมณฑล'),
                'ปทุมธานี': ('ปทุมธานี', 'กรุงเทพและปริมณฑล'),
                'สมุทรปราการ': ('สมุทรปราการ', 'กรุงเทพและปริมณฑล'),
                'สมุทรสาคร': ('สมุทรสาคร', 'กรุงเทพและปริมณฑล'),
                'สมุทรสงคราม': ('สมุทรสงคราม', 'กรุงเทพและปริมณฑล'),
                'เชียงใหม่': ('เชียงใหม่', 'ภาคเหนือ'),
                'เชียงราย': ('เชียงราย', 'ภาคเหนือ'),
                'นครราชสีมา': ('นครราชสีมา', 'ภาคอีสาน'),
                'ขอนแก่น': ('ขอนแก่น', 'ภาคอีสาน'),
                'ภูเก็ต': ('ภูเก็ต', 'ภาคใต้'),
                'สงขลา': ('สงขลา', 'ภาคใต้'),
                'ชลบุรี': ('ชลบุรี', 'ภาคตะวันออก'),
                'ระยอง': ('ระยอง', 'ภาคตะวันออก'),
                'นครปฐม': ('นครปฐม', 'ภาคกลาง'),
                'กาญจนบุรี': ('กาญจนบุรี', 'ภาคกลาง'),
                'สระบุรี': ('สระบุรี', 'ภาคกลาง'),
                'นครสวรรค์': ('นครสวรรค์', 'ภาคกลาง'),
                'ลพบุรี': ('ลพบุรี', 'ภาคกลาง')
            }
            
            if thai_province in province_mapping:
                province, region = province_mapping[thai_province]
                return province, 1.0, region
            else:
                # Fallback: use as-is with confidence 0.8
                return thai_province, 0.8, 'ไม่ระบุ'
        
        # Try to extract English province name
        english_match = re.search(r':([^(]+)', api_province)
        if english_match:
            english_province = english_match.group(1).strip()
            
            # Map common English names
            english_mapping = {
                'Bangkok': ('กรุงเทพมหานคร', 'กรุงเทพและปริมณฑล'),
                'Chiang Mai': ('เชียงใหม่', 'ภาคเหนือ'),
                'Chiang Rai': ('เชียงราย', 'ภาคเหนือ'),
                'Phuket': ('ภูเก็ต', 'ภาคใต้'),
                'Khon Kaen': ('ขอนแก่น', 'ภาคอีสาน'),
                'Nakhon Ratchasima': ('นครราชสีมา', 'ภาคอีสาน'),
                'Chonburi': ('ชลบุรี', 'ภาคตะวันออก'),
                'Songkhla': ('สงขลา', 'ภาคใต้')
            }
            
            if english_province in english_mapping:
                province, region = english_mapping[english_province]
                return province, 0.9, region
        
        return None, 0.0, 'ไม่ระบุ'
        
    except Exception as e:
        print(f"⚠️ Province extraction error: {e}")
        return None, 0.0, 'ไม่ระบุ'

def test_api_province_extraction():
    """Test API province extraction"""
    test_cases = [
        {
            'raw_response': {
                'province': 'th-10:Bangkok (กรุงเทพมหานคร)',
                'lp_number': 'กก1234'
            }
        },
        {
            'raw_response': {
                'province': 'th-50:Chiang Mai (เชียงใหม่)',
                'lp_number': 'ขข5678'
            }
        },
        {
            'raw_response': {
                'province': 'th-83:Phuket (ภูเก็ต)',
                'lp_number': 'ภก9999'
            }
        }
    ]
    
    print("🧪 Testing API Province Extraction:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        province, confidence, region = extract_province_from_api_response(test_case)
        print(f"Test {i}:")
        print(f"   Input: {test_case['raw_response']['province']}")
        print(f"   Output: {province} ({confidence:.1f}) - {region}")
        print()

if __name__ == "__main__":
    test_api_province_extraction()
