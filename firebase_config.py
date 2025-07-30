"""
========================================
🔥 Firebase Configuration & Database Operations
========================================
"""

import firebase_admin
from firebase_admin import credentials, db
import pyrebase
import os
from datetime import datetime
import logging
import json
from province_utils import analyze_license_plate
from api_province_utils import extract_province_from_api_response

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Firebase configuration
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyBsXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",  # เปลี่ยนเป็น API Key จริง
    "authDomain": "testdatabase-7ebbc.firebaseapp.com",
    "databaseURL": "https://testdatabase-7ebbc-default-rtdb.asia-southeast1.firebasedatabase.app/",
    "projectId": "testdatabase-7ebbc",
    "storageBucket": "testdatabase-7ebbc.appspot.com",
    "messagingSenderId": "123456789012",  # เปลี่ยนเป็นตัวเลขจริง
    "appId": "1:123456789012:web:abcdefghijklmnop",  # เปลี่ยนเป็น App ID จริง
    "databaseSecret": "1R8G0J2vnFNxyDsdhma0XnETTZfOb8PX8aYOQuwJ"
}

class FirebaseManager:
    def __init__(self, service_account_path=None):
        """
        Initialize Firebase connection
        
        Args:
            service_account_path: Path to Firebase service account JSON file
        """
        self.database = None
        self.pyrebase_db = None
        self.initialized = False
        self.mock_mode = False
        self.mock_data = []  # สำหรับเก็บข้อมูล mock
        
        try:
            # Try Firebase Admin SDK first
            if not firebase_admin._apps:
                firebase_admin.initialize_app(options={
                    'databaseURL': FIREBASE_CONFIG['databaseURL'],
                    'databaseAuthVariableOverride': None
                })
                
            self.database = db.reference()
            self.initialized = True
            logger.info("✅ Firebase Admin SDK initialized successfully")
            
        except Exception as admin_error:
            logger.warning(f"⚠️ Firebase Admin SDK failed: {admin_error}")
            
            try:
                # Fallback to pyrebase
                firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
                self.pyrebase_db = firebase.database()
                self.initialized = True
                self.mock_mode = False
                logger.info("✅ Firebase Pyrebase initialized successfully")
                
            except Exception as pyrebase_error:
                logger.error(f"❌ Pyrebase initialization failed: {pyrebase_error}")
                logger.info("💡 Switching to Mock Firebase mode for local development")
                self.mock_mode = True
                self.initialized = True  # Set to true for mock mode
    
    def is_connected(self):
        """Check if Firebase is properly connected"""
        return self.initialized and (self.database is not None or self.pyrebase_db is not None or self.mock_mode)
    
    def save_detection_result(self, license_plate, confidence_api, confidence_yolo=None, 
                            image_data=None, detection_mode="manual", api_response=None):
        """
        Save license plate detection result to Firebase Realtime Database
        
        Args:
            license_plate: Detected license plate text
            confidence_api: API confidence score
            confidence_yolo: YOLO confidence score (optional)
            image_data: Base64 encoded image data (optional)
            detection_mode: "auto" or "manual"
            api_response: Full API response for province extraction (optional)
        
        Returns:
            Document ID if successful, None if failed
        """
        if not self.is_connected():
            logger.error("❌ Firebase not connected")
            return None
        
        # Mock mode
        if self.mock_mode:
            # Province analysis priority: API response > License plate text analysis
            province = None
            province_confidence = 0.0
            region = 'ไม่ระบุ'
            analysis_success = False
            
            # Try API response first
            if api_response:
                api_province, api_confidence, api_region = extract_province_from_api_response(api_response)
                if api_province:
                    province = api_province
                    province_confidence = api_confidence
                    region = api_region
                    analysis_success = True
            
            # Fallback to license plate text analysis
            if not province:
                plate_analysis = analyze_license_plate(license_plate)
                province = plate_analysis.get('province')
                province_confidence = plate_analysis.get('province_confidence', 0.0)
                region = plate_analysis.get('region', 'ไม่ระบุ')
                analysis_success = plate_analysis.get('analysis_success', False)
            
            doc_id = f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
            mock_doc = {
                'id': doc_id,
                'license_plate': license_plate,
                'confidence_api': confidence_api,
                'detection_mode': detection_mode,
                'timestamp': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                # Province information
                'province': province,
                'province_confidence': province_confidence,
                'region': region,
                'province_analysis_success': analysis_success
            }
            if confidence_yolo is not None:
                mock_doc['confidence_yolo'] = confidence_yolo
            if image_data:
                mock_doc['has_image'] = True
                mock_doc['image_size'] = len(image_data)
            else:
                mock_doc['has_image'] = False
            
            self.mock_data.append(mock_doc)
            logger.info(f"✅ Detection saved to Mock Firebase: {doc_id}")
            return doc_id
            
        try:
            # Province analysis priority: API response > License plate text analysis
            province = None
            province_confidence = 0.0
            region = 'ไม่ระบุ'
            analysis_success = False
            
            # Try API response first
            if api_response:
                api_province, api_confidence, api_region = extract_province_from_api_response(api_response)
                if api_province:
                    province = api_province
                    province_confidence = api_confidence
                    region = api_region
                    analysis_success = True
                    logger.info(f"🗺️ Province from API: {province} ({province_confidence:.1f})")
            
            # Fallback to license plate text analysis
            if not province:
                plate_analysis = analyze_license_plate(license_plate)
                province = plate_analysis.get('province')
                province_confidence = plate_analysis.get('province_confidence', 0.0)
                region = plate_analysis.get('region', 'ไม่ระบุ')
                analysis_success = plate_analysis.get('analysis_success', False)
                if province:
                    logger.info(f"🗺️ Province from text: {province} ({province_confidence:.1f})")
            
            # Prepare document data
            doc_data = {
                'license_plate': license_plate,
                'confidence_api': confidence_api,
                'detection_mode': detection_mode,
                'timestamp': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                # Province information
                'province': province,
                'province_confidence': province_confidence,
                'region': region,
                'province_analysis_success': analysis_success
            }
            
            # Add YOLO confidence if available
            if confidence_yolo is not None:
                doc_data['confidence_yolo'] = confidence_yolo
            
            # Add image data if provided
            if image_data:
                doc_data['has_image'] = True
                doc_data['image_size'] = len(image_data)
            else:
                doc_data['has_image'] = False
            
            # Save to Firebase Realtime Database
            if self.database:
                # Using Firebase Admin SDK
                detections_ref = self.database.child('license_plate_detections')
                result = detections_ref.push(doc_data)
                doc_id = result.key
            elif self.pyrebase_db:
                # Using Pyrebase
                result = self.pyrebase_db.child('license_plate_detections').push(doc_data)
                doc_id = result['name']
            else:
                raise Exception("No database connection available")
            
            logger.info(f"✅ Detection saved to Firebase: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save detection: {e}")
            return None
    
    def get_recent_detections(self, limit=50):
        """
        Get recent license plate detections
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of detection documents
        """
        if not self.is_connected():
            logger.error("❌ Firebase not connected")
            return []
        
        # Mock mode
        if self.mock_mode:
            # Return recent mock data
            sorted_data = sorted(self.mock_data, key=lambda x: x['timestamp'], reverse=True)
            return sorted_data[:limit]
            
        try:
            # Query recent detections from Firebase Realtime Database
            if self.database:
                # Using Firebase Admin SDK
                detections_ref = self.database.child('license_plate_detections')
                docs = detections_ref.get()
            elif self.pyrebase_db:
                # Using Pyrebase - get all data and sort in Python
                docs = self.pyrebase_db.child('license_plate_detections').get()
                if hasattr(docs, 'val'):
                    docs = docs.val()
            else:
                return []
            
            detections = []
            if docs:
                for key, value in docs.items():
                    data = value
                    data['id'] = key
                    detections.append(data)
            
            # Sort by timestamp (newest first) and limit
            detections.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            detections = detections[:limit]
            
            logger.info(f"✅ Retrieved {len(detections)} recent detections")
            return detections
            
        except Exception as e:
            logger.error(f"❌ Failed to get detections: {e}")
            return []
    
    def get_detection_stats(self):
        """
        Get detection statistics
        
        Returns:
            Dictionary with statistics
        """
        if not self.is_connected():
            return {
                'total_detections': 0,
                'auto_detections': 0,
                'manual_detections': 0,
                'avg_confidence_api': 0,
                'avg_confidence_yolo': 0
            }
        
        # Mock mode
        if self.mock_mode:
            total = len(self.mock_data)
            auto_count = sum(1 for d in self.mock_data if d.get('detection_mode') == 'auto')
            manual_count = total - auto_count
            
            api_confidence_sum = sum(d.get('confidence_api', 0) for d in self.mock_data)
            yolo_data = [d for d in self.mock_data if 'confidence_yolo' in d]
            yolo_confidence_sum = sum(d['confidence_yolo'] for d in yolo_data)
            
            return {
                'total_detections': total,
                'auto_detections': auto_count,
                'manual_detections': manual_count,
                'avg_confidence_api': api_confidence_sum / total if total > 0 else 0,
                'avg_confidence_yolo': yolo_confidence_sum / len(yolo_data) if yolo_data else 0
            }
            
        try:
            # Get all detections for stats
            if self.database:
                # Using Firebase Admin SDK
                detections_ref = self.database.child('license_plate_detections')
                docs = detections_ref.get()
            elif self.pyrebase_db:
                # Using Pyrebase
                docs = self.pyrebase_db.child('license_plate_detections').get()
                if hasattr(docs, 'val'):
                    docs = docs.val()
            else:
                return {}
            
            if not docs:
                return {
                    'total_detections': 0,
                    'auto_detections': 0,
                    'manual_detections': 0,
                    'avg_confidence_api': 0,
                    'avg_confidence_yolo': 0
                }
            
            total = 0
            auto_count = 0
            manual_count = 0
            api_confidence_sum = 0
            yolo_confidence_sum = 0
            yolo_count = 0
            
            for key, data in docs.items():
                total += 1
                
                if data.get('detection_mode') == 'auto':
                    auto_count += 1
                else:
                    manual_count += 1
                
                api_confidence_sum += data.get('confidence_api', 0)
                
                if 'confidence_yolo' in data:
                    yolo_confidence_sum += data['confidence_yolo']
                    yolo_count += 1
            
            return {
                'total_detections': total,
                'auto_detections': auto_count,
                'manual_detections': manual_count,
                'avg_confidence_api': api_confidence_sum / total if total > 0 else 0,
                'avg_confidence_yolo': yolo_confidence_sum / yolo_count if yolo_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}
    
    def search_detections(self, license_plate=None, start_date=None, end_date=None):
        """
        Search detections by criteria
        
        Args:
            license_plate: License plate text to search for
            start_date: Start date for search
            end_date: End date for search
            
        Returns:
            List of matching detections
        """
        if not self.is_connected():
            return []
        
        # Mock mode
        if self.mock_mode:
            results = self.mock_data[:]
            
            # Filter by license plate
            if license_plate:
                results = [d for d in results if license_plate.lower() in d.get('license_plate', '').lower()]
            
            # Filter by date range (simplified for mock)
            # In a real implementation, you'd properly parse and compare dates
            
            return results
            
        try:
            # Get all detections from Firebase Realtime Database
            if self.database:
                # Using Firebase Admin SDK
                detections_ref = self.database.child('license_plate_detections')
                docs = detections_ref.get()
            elif self.pyrebase_db:
                # Using Pyrebase
                docs = self.pyrebase_db.child('license_plate_detections').get()
                if hasattr(docs, 'val'):
                    docs = docs.val()
            else:
                return []
            
            results = []
            if docs:
                for key, data in docs.items():
                    # Filter by license plate
                    if license_plate and license_plate.lower() not in data.get('license_plate', '').lower():
                        continue
                    
                    # Add date filtering logic here if needed
                    # For now, we'll just do license plate matching
                    
                    data['id'] = key
                    results.append(data)
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            logger.info(f"✅ Search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def get_province_stats(self):
        """
        Get detection statistics by province and region
        
        Returns:
            dict: Province and region statistics
        """
        if not self.is_connected():
            return {}
        
        # Mock mode
        if self.mock_mode:
            province_counts = {}
            region_counts = {}
            
            for detection in self.mock_data:
                province = detection.get('province')
                region = detection.get('region')
                
                if province:
                    province_counts[province] = province_counts.get(province, 0) + 1
                if region:
                    region_counts[region] = region_counts.get(region, 0) + 1
            
            return {
                'province_stats': province_counts,
                'region_stats': region_counts,
                'total_with_province': sum(province_counts.values()),
                'top_provinces': sorted(province_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                'top_regions': sorted(region_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            }
        
        try:
            # Get all detections
            if self.database:
                # Using Firebase Admin SDK
                detections_ref = self.database.child('license_plate_detections')
                docs = detections_ref.get()
            elif self.pyrebase_db:
                # Using Pyrebase
                docs = self.pyrebase_db.child('license_plate_detections').get()
                if hasattr(docs, 'val'):
                    docs = docs.val()
            else:
                return {}
            
            if not docs:
                return {}
            
            province_counts = {}
            region_counts = {}
            total_analyzed = 0
            
            for key, data in docs.items():
                province = data.get('province')
                region = data.get('region')
                
                if data.get('province_analysis_success', False):
                    total_analyzed += 1
                
                if province:
                    province_counts[province] = province_counts.get(province, 0) + 1
                if region:
                    region_counts[region] = region_counts.get(region, 0) + 1
            
            return {
                'province_stats': province_counts,
                'region_stats': region_counts,
                'total_with_province': len([d for d in docs.values() if d.get('province')]),
                'total_analyzed': total_analyzed,
                'success_rate': total_analyzed / len(docs) if len(docs) > 0 else 0,
                'top_provinces': sorted(province_counts.items(), key=lambda x: x[1], reverse=True)[:10],
                'top_regions': sorted(region_counts.items(), key=lambda x: x[1], reverse=True)[:6]
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get province stats: {e}")
            return {}
    
    def delete_detection(self, doc_id):
        """
        Delete a detection record
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        # Mock mode
        if self.mock_mode:
            self.mock_data = [d for d in self.mock_data if d.get('id') != doc_id]
            logger.info(f"✅ Detection deleted from Mock Firebase: {doc_id}")
            return True
            
        try:
            if self.database:
                # Using Firebase Admin SDK
                detections_ref = self.database.child('license_plate_detections').child(doc_id)
                detections_ref.delete()
            elif self.pyrebase_db:
                # Using Pyrebase
                self.pyrebase_db.child('license_plate_detections').child(doc_id).remove()
            else:
                return False
            logger.info(f"✅ Detection deleted: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete detection: {e}")
            return False

# Global Firebase manager instance
firebase_manager = FirebaseManager()

# Convenience functions for easy usage
def save_detection(license_plate, confidence_api, confidence_yolo=None, detection_mode="manual"):
    """Convenience function to save detection"""
    return firebase_manager.save_detection_result(
        license_plate, confidence_api, confidence_yolo, None, detection_mode
    )

def get_recent_detections(limit=50):
    """Convenience function to get recent detections"""
    return firebase_manager.get_recent_detections(limit)

def get_stats():
    """Convenience function to get detection statistics"""
    return firebase_manager.get_detection_stats()

def search_by_plate(license_plate):
    """Convenience function to search by license plate"""
    return firebase_manager.search_detections(license_plate=license_plate)
