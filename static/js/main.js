/**
 * ========================================
 * 🚗 License Plate Reader - Main JavaScript
 * ========================================
 */

// Global Variables
let selectedFile = null;

// DOM Elements
const uploadArea = document.getElementById("uploadArea");
const fileInput = document.getElementById("fileInput");
const previewArea = document.getElementById("previewArea");
const previewImage = document.getElementById("previewImage");
const loading = document.getElementById("loading");
const results = document.getElementById("results");
const errorArea = document.getElementById("errorArea");

/**
 * Initialize the application
 */
document.addEventListener("DOMContentLoaded", function () {
  initializeDragAndDrop();
  console.log("🚗 License Plate Reader initialized");
});

/**
 * Initialize drag and drop functionality
 */
function initializeDragAndDrop() {
  uploadArea.addEventListener("dragover", handleDragOver);
  uploadArea.addEventListener("dragleave", handleDragLeave);
  uploadArea.addEventListener("drop", handleDrop);
}

/**
 * Handle drag over event
 */
function handleDragOver(e) {
  e.preventDefault();
  uploadArea.classList.add("dragover");
}

/**
 * Handle drag leave event
 */
function handleDragLeave() {
  uploadArea.classList.remove("dragover");
}

/**
 * Handle drop event
 */
function handleDrop(e) {
  e.preventDefault();
  uploadArea.classList.remove("dragover");
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
}

/**
 * Handle file selection from input
 */
function handleFileSelect(input) {
  if (input.files && input.files[0]) {
    handleFile(input.files[0]);
  }
}

/**
 * Process selected file
 */
function handleFile(file) {
  // Validate file type
  if (!file.type.startsWith("image/")) {
    showAlert("โปรดเลือกไฟล์รูปภาพ", "warning");
    return;
  }

  // Validate file size (16MB)
  if (file.size > 16 * 1024 * 1024) {
    showAlert("ไฟล์ใหญ่เกินไป (ขนาดไม่เกิน 16MB)", "warning");
    return;
  }

  selectedFile = file;
  showPreview(file);
}

/**
 * Show image preview
 */
function showPreview(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImage.src = e.target.result;
    showElement(previewArea);
    hideElement(uploadArea);
  };
  reader.readAsDataURL(file);
}

/**
 * Upload file to server
 */
function uploadFile() {
  if (!selectedFile) {
    showAlert("กรุณาเลือกไฟล์ก่อน", "warning");
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);

  // Show loading state
  showLoading();
  hideElement(previewArea);
  hideElement(results);
  hideElement(errorArea);

  // Send request to server
  fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      hideLoading();
      if (data.error) {
        showError(data.error);
      } else {
        showResults(data);
      }
    })
    .catch((error) => {
      hideLoading();
      showError("เกิดข้อผิดพลาดในการเชื่อมต่อ: " + error.message);
      console.error("Upload error:", error);
    });
}

/**
 * Display analysis results
 */
function showResults(data) {
  // Update license plate
  updateElement("licensePlate", data.lp_number || "ไม่พบ");

  // Update confidence bar
  const confidence = data.conf || 0;
  updateConfidence(confidence);

  // Update processing info
  updateElement("processTime", data["infer_time(s)"] || "-");
  updateElement("uploadTime", data.upload_time || "-");

  // Update vehicle info
  updateVehicleInfo(data);

  // Show results
  showElement(results);

  // Log success
  console.log("✅ Results displayed successfully", data);
}

/**
 * Update confidence display
 */
function updateConfidence(confidence) {
  const confidenceBar = document.getElementById("confidenceBar");
  const confidenceText = document.getElementById("confidenceText");

  confidenceBar.style.width = confidence + "%";
  confidenceText.textContent = confidence.toFixed(1) + "%";

  // Change color based on confidence level
  if (confidence >= 80) {
    confidenceBar.style.background = "linear-gradient(45deg, #28a745, #20c997)";
  } else if (confidence >= 60) {
    confidenceBar.style.background = "linear-gradient(45deg, #ffc107, #fd7e14)";
  } else {
    confidenceBar.style.background = "linear-gradient(45deg, #dc3545, #e83e8c)";
  }
}

/**
 * Update vehicle information grid
 */
function updateVehicleInfo(data) {
  const vehicleInfo = document.getElementById("vehicleInfo");
  vehicleInfo.innerHTML = `
        <div class="info-item">
            <h6><i class="fas fa-map-marker-alt"></i> จังหวัด</h6>
            <p>${data.province || "ไม่ระบุ"}</p>
        </div>
        <div class="info-item">
            <h6><i class="fas fa-car"></i> ประเภทรถ</h6>
            <p>${data.vehicle_body_type || "ไม่ระบุ"}</p>
        </div>
        <div class="info-item">
            <h6><i class="fas fa-industry"></i> ยี่ห้อ</h6>
            <p>${data.vehicle_brand || "ไม่ระบุ"}</p>
        </div>
        <div class="info-item">
            <h6><i class="fas fa-car-side"></i> รุ่น</h6>
            <p>${data.vehicle_model || "ไม่ระบุ"}</p>
        </div>
        <div class="info-item">
            <h6><i class="fas fa-palette"></i> สี</h6>
            <p>${data.vehicle_color || "ไม่ระบุ"}</p>
        </div>
        <div class="info-item">
            <h6><i class="fas fa-calendar-alt"></i> ปี</h6>
            <p>${data.vehicle_year || "ไม่ระบุ"}</p>
        </div>
    `;
}

/**
 * Show error message
 */
function showError(message) {
  updateElement("errorMessage", message);
  showElement(errorArea);
  console.error("❌ Error:", message);
}

/**
 * Reset form to initial state
 */
function resetForm() {
  selectedFile = null;
  fileInput.value = "";

  // Reset UI
  showElement(uploadArea);
  hideElement(previewArea);
  hideElement(results);
  hideElement(errorArea);
  hideLoading();

  console.log("🔄 Form reset");
}

/**
 * Show loading state
 */
function showLoading() {
  showElement(loading);
}

/**
 * Hide loading state
 */
function hideLoading() {
  hideElement(loading);
}

/**
 * Show element
 */
function showElement(element) {
  if (element) {
    element.style.display = "block";
  }
}

/**
 * Hide element
 */
function hideElement(element) {
  if (element) {
    element.style.display = "none";
  }
}

/**
 * Update element content
 */
function updateElement(id, content) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = content;
  }
}

/**
 * Show alert message
 */
function showAlert(message, type = "info") {
  // You can implement a custom alert system here
  // For now, using browser alert
  alert(message);
}

/**
 * Click handler for upload area
 */
function clickUploadArea() {
  fileInput.click();
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

/**
 * Get file extension
 */
function getFileExtension(filename) {
  return filename.slice(((filename.lastIndexOf(".") - 1) >>> 0) + 2);
}

// Export functions for global access
window.handleFileSelect = handleFileSelect;
window.uploadFile = uploadFile;
window.resetForm = resetForm;
window.clickUploadArea = clickUploadArea;
