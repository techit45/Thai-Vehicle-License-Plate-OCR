#!/usr/bin/env python3
"""
Province utilities for Thai license plates
"""

import re

# Thai provinces mapping
THAI_PROVINCES = {
    # กรุงเทพมหานคร และปริมณฑล
    'กรุงเทพมหานคร': ['กรุงเทพ', 'กทม', 'กทม.', 'bangkok'],
    'นนทบุรี': ['นนทบุรี', 'นท', 'nonthaburi'],
    'ปทุมธานี': ['ปทุมธานี', 'ปท', 'pathum thani'],
    'สมุทรปราการ': ['สมุทรปราการ', 'สป', 'samut prakan'],
    'สมุทรสาคร': ['สมุทรสาคร', 'สส', 'samut sakhon'],
    'สมุทรสงคราม': ['สมุทรสงคราม', 'สซ', 'samut songkhram'],
    
    # ภาคเหนือ
    'เชียงใหม่': ['เชียงใหม่', 'ชม', 'chiang mai'],
    'เชียงราย': ['เชียงราย', 'ชร', 'chiang rai'],
    'แม่ฮ่องสอน': ['แม่ฮ่องสอน', 'มส', 'mae hong son'],
    'น่าน': ['น่าน', 'นน', 'nan'],
    'พะเยา': ['พะเยา', 'พย', 'phayao'],
    'แพร่': ['แพร่', 'พร', 'phrae'],
    'ลำปาง': ['ลำปาง', 'ลป', 'lampang'],
    'ลำพูน': ['ลำพูน', 'ลพ', 'lamphun'],
    'อุตรดิตถ์': ['อุตรดิตถ์', 'อต', 'uttaradit'],
    'สุโขทัย': ['สุโขทัย', 'สท', 'sukhothai'],
    'ตาก': ['ตาก', 'ตก', 'tak'],
    'กำแพงเพชร': ['กำแพงเพชร', 'กพ', 'kamphaeng phet'],
    'พิจิตร': ['พิจิตร', 'พจ', 'phichit'],
    'พิษณุโลก': ['พิษณุโลก', 'พล', 'phitsanulok'],
    
    # ภาคอีสาน
    'นครราชสีมา': ['นครราชสีมา', 'นม', 'korat', 'nakhon ratchasima'],
    'ขอนแก่น': ['ขอนแก่น', 'ขก', 'khon kaen'],
    'อุดรธานี': ['อุดรธานี', 'อด', 'udon thani'],
    'เลย': ['เลย', 'ลย', 'loei'],
    'หนองคาย': ['หนองคาย', 'หนค', 'nong khai'],
    'หนองบัวลำภู': ['หนองบัวลำภู', 'นภ', 'nong bua lam phu'],
    'บึงกาฬ': ['บึงกาฬ', 'บก', 'bueng kan'],
    'สกลนคร': ['สกลนคร', 'สน', 'sakon nakhon'],
    'นครพนม': ['นครพนม', 'นพ', 'nakhon phanom'],
    'มุกดาหาร': ['มุกดาหาร', 'มห', 'mukdahan'],
    'กาฬสินธุ์': ['กาฬสินธุ์', 'กส', 'kalasin'],
    'ร้อยเอ็ด': ['ร้อยเอ็ด', 'รอ', 'roi et'],
    'มหาสารคาม': ['มหาสารคาม', 'มค', 'maha sarakham'],
    'ยะโสธร': ['ยะโสธร', 'ยส', 'yasothon'],
    'อำนาจเจริญ': ['อำนาจเจริญ', 'อจ', 'amnat charoen'],
    'อุบลราชธานี': ['อุบลราชธานี', 'อบ', 'ubon ratchathani'],
    'ศีสะเกษ': ['ศีสะเกษ', 'ศก', 'si sa ket'],
    'สุรินทร์': ['สุรินทร์', 'สร', 'surin'],
    'บุรีรัมย์': ['บุรีรัมย์', 'บร', 'buriram'],
    'ชัยภูมิ': ['ชัยภูมิ', 'ชย', 'chaiyaphum'],
    
    # ภาคกลาง
    'นครสวรรค์': ['นครสวรรค์', 'นส', 'nakhon sawan'],
    'ชัยนาท': ['ชัยนาท', 'ชน', 'chai nat'],
    'สิงห์บุรี': ['สิงห์บุรี', 'สบ', 'sing buri'],
    'อ่างทอง': ['อ่างทอง', 'อท', 'ang thong'],
    'สระบุรี': ['สระบุรี', 'สระ', 'saraburi'],
    'ลพบุรี': ['ลพบุรี', 'ลบ', 'lopburi'],
    'อยุธยา': ['อยุธยา', 'อย', 'ayutthaya', 'พระนครศรีอยุธยา'],
    'สุพรรณบุรี': ['สุพรรณบุรี', 'สพ', 'suphanburi'],
    'กาญจนบุรี': ['กาญจนบุรี', 'กจ', 'kanchanaburi'],
    'เพชรบุรี': ['เพชรบุรี', 'พบ', 'phetchaburi'],
    'ประจวบคีรีขันธ์': ['ประจวบคีรีขันธ์', 'ปข', 'prachuap khiri khan'],
    'นครปฐม': ['นครปฐม', 'นฐ', 'nakhon pathom'],
    'ราชบุรี': ['ราชบุรี', 'รบ', 'ratchaburi'],
    
    # ภาคตะวันออก
    'ฉะเชิงเทรา': ['ฉะเชิงเทรา', 'ฉช', 'chachoengsao'],
    'ปราจีนบุรี': ['ปราจีนบุรี', 'ปจ', 'prachin buri'],
    'นครนายก': ['นครนายก', 'นย', 'nakhon nayok'],
    'ชลบุรี': ['ชลบุรี', 'ชบ', 'chonburi'],
    'ระยอง': ['ระยอง', 'รย', 'rayong'],
    'จันทบุรี': ['จันทบุรี', 'จบ', 'chanthaburi'],
    'ตราด': ['ตราด', 'ตด', 'trat'],
    'สระแก้ว': ['สระแก้ว', 'สก', 'sa kaeo'],
    
    # ภาคใต้
    'เพชรบูรณ์': ['เพชรบูรณ์', 'พช', 'phetchabun'],
    'ชุมพร': ['ชุมพร', 'ชพ', 'chumphon'],
    'ระนอง': ['ระนอง', 'รน', 'ranong'],
    'สุราษฎร์ธานี': ['สุราษฎร์ธานี', 'สฎ', 'surat thani'],
    'นครศรีธรรมราช': ['นครศรีธรรมราช', 'นศ', 'nakhon si thammarat'],
    'กระบี่': ['กระบี่', 'กบ', 'krabi'],
    'พังงา': ['พังงา', 'พง', 'phang nga'],
    'ภูเก็ต': ['ภูเก็ต', 'ภก', 'phuket'],
    'ตรัง': ['ตรัง', 'ตร', 'trang'],
    'พัทลุง': ['พัทลุง', 'พท', 'phatthalung'],
    'สงขลา': ['สงขลา', 'สข', 'songkhla'],
    'สตูล': ['สตูล', 'สต', 'satun'],
    'ปัตตานี': ['ปัตตานี', 'ปต', 'pattani'],
    'ยะลา': ['ยะลา', 'ยล', 'yala'],
    'นราธิวาส': ['นราธิวาส', 'นธ', 'narathiwat']
}

def extract_province_from_plate(license_plate):
    """
    Extract province from Thai license plate text
    
    Args:
        license_plate: License plate text
        
    Returns:
        tuple: (province_name, confidence)
    """
    if not license_plate:
        return None, 0.0
    
    # Clean the input
    plate_text = license_plate.strip().lower()
    
    # Try exact matches first
    for province, variations in THAI_PROVINCES.items():
        for variation in variations:
            if variation.lower() in plate_text:
                return province, 1.0
    
    # Try partial matches with common patterns
    # Pattern: XX #### PROVINCE or PROVINCE XX ####
    words = plate_text.split()
    
    for word in words:
        word_clean = word.strip('.,!?()[]{}')
        for province, variations in THAI_PROVINCES.items():
            for variation in variations:
                # Fuzzy matching
                if (len(word_clean) > 2 and 
                    (word_clean in variation.lower() or 
                     variation.lower() in word_clean)):
                    return province, 0.8
    
    # Special patterns for common abbreviations
    abbreviation_patterns = {
        'กรุงเทพ': ['กทม', 'bkk', 'bangkok', 'กรุงเทพมหานคร'],
        'เชียงใหม่': ['ชม', 'cm', 'chiangmai'],
        'เชียงราย': ['ชร', 'cr', 'chiangrai'],
        'ขอนแก่น': ['ขก', 'kk', 'khonkaen'],
        'นครราชสีมา': ['นม', 'korat', 'nakhonratchasima'],
        'ภูเก็ต': ['ภก', 'phuket'],
        'สงขลา': ['สข', 'songkhla'],
        'ชลบุรี': ['ชบ', 'chonburi', 'pattaya']
    }
    
    for province, patterns in abbreviation_patterns.items():
        for pattern in patterns:
            if pattern.lower() in plate_text:
                return province, 0.9
    
    return None, 0.0

def get_province_region(province):
    """
    Get region of a province
    
    Args:
        province: Province name
        
    Returns:
        str: Region name
    """
    regions = {
        'ภาคเหนือ': [
            'เชียงใหม่', 'เชียงราย', 'แม่ฮ่องสอน', 'น่าน', 'พะเยา', 'แพร่',
            'ลำปาง', 'ลำพูน', 'อุตรดิตถ์', 'สุโขทัย', 'ตาก', 'กำแพงเพชร',
            'พิจิตร', 'พิษณุโลก'
        ],
        'ภาคอีสาน': [
            'นครราชสีมา', 'ขอนแก่น', 'อุดรธานี', 'เลย', 'หนองคาย', 'หนองบัวลำภู',
            'บึงกาฬ', 'สกลนคร', 'นครพนม', 'มุกดาหาร', 'กาฬสินธุ์', 'ร้อยเอ็ด',
            'มหาสารคาม', 'ยะโสธร', 'อำนาจเจริญ', 'อุบลราชธานี', 'ศีสะเกษ',
            'สุรินทร์', 'บุรีรัมย์', 'ชัยภูมิ'
        ],
        'ภาคกลาง': [
            'นครสวรรค์', 'ชัยนาท', 'สิงห์บุรี', 'อ่างทอง', 'สระบุรี', 'ลพบุรี',
            'อยุธยา', 'สุพรรณบุรี', 'กาญจนบุรี', 'เพชรบุรี', 'ประจวบคีรีขันธ์',
            'นครปฐม', 'ราชบุรี', 'เพชรบูรณ์'
        ],
        'ภาคตะวันออก': [
            'ฉะเชิงเทรา', 'ปราจีนบุรี', 'นครนายก', 'ชลบุรี', 'ระยอง',
            'จันทบุรี', 'ตราด', 'สระแก้ว'
        ],
        'ภาคใต้': [
            'ชุมพร', 'ระนอง', 'สุราษฎร์ธานี', 'นครศรีธรรมราช', 'กระบี่',
            'พังงา', 'ภูเก็ต', 'ตรัง', 'พัทลุง', 'สงขลา', 'สตูล',
            'ปัตตานี', 'ยะลา', 'นราธิวาส'
        ],
        'กรุงเทพและปริมณฑล': [
            'กรุงเทพมหานคร', 'นนทบุรี', 'ปทุมธานี', 'สมุทรปราการ',
            'สมุทรสาคร', 'สมุทรสงคราม'
        ]
    }
    
    for region, provinces in regions.items():
        if province in provinces:
            return region
    
    return 'ไม่ระบุ'

def analyze_license_plate(license_plate):
    """
    Analyze license plate and extract all information
    
    Args:
        license_plate: License plate text
        
    Returns:
        dict: Analysis results
    """
    province, confidence = extract_province_from_plate(license_plate)
    region = get_province_region(province) if province else 'ไม่ระบุ'
    
    return {
        'license_plate': license_plate,
        'province': province,
        'province_confidence': confidence,
        'region': region,
        'analysis_success': province is not None
    }

if __name__ == "__main__":
    # Test cases
    test_plates = [
        "กก 1234 กรุงเทพ",
        "ขข 5678 เชียงใหม่",
        "นส 9999 นครสวรรค์",
        "ABC 123 Bangkok",
        "1234 กทม",
        "ชม 4567"
    ]
    
    print("🔍 Testing Province Extraction:")
    print("=" * 50)
    
    for plate in test_plates:
        result = analyze_license_plate(plate)
        print(f"📋 {plate}")
        print(f"   🏛️ จังหวัด: {result['province']} ({result['province_confidence']:.1f})")
        print(f"   🗺️ ภาค: {result['region']}")
        print(f"   ✅ สำเร็จ: {result['analysis_success']}")
        print()
