/**
 * ========================================
 * 🚗 License Plate Reader - Webcam JavaScript
 * ========================================
 */

// Global Variables
let video = null;
let canvas = null;
let ctx = null;
let stream = null;
let isRunning = false;
let isProcessing = false; // Track API processing state
let detectionMode = "auto";
let lastApiCall = 0;
let sessionResults = [];
let fpsCounter = 0;
let lastFpsTime = Date.now();
let animationId = null; // Track animation frame for stopping

// Statistics
let stats = {
  detections: 0,
  apiCalls: 0,
  fps: 0,
};

// Settings
let settings = {
  confidence: 0.25,
  iou: 0.45,
  camera: 0,
  resolution: "1280x720",
  autoInterval: 3, // Back to 3 seconds for faster detection
};

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  initializeWebcam();
  console.log("📷 Webcam page initialized");
});

/**
 * Initialize webcam functionality
 */
function initializeWebcam() {
  // Get DOM elements
  canvas = document.getElementById("videoCanvas");
  ctx = canvas.getContext("2d");

  // Set initial canvas size
  canvas.width = 640;
  canvas.height = 480;

  // Draw initial state
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#fff";
  ctx.font = "20px Arial";
  ctx.textAlign = "center";
  ctx.fillText(
    "กดเริ่มกล้องเพื่อเริ่มใช้งาน",
    canvas.width / 2,
    canvas.height / 2
  );

  // Initialize event listeners
  initializeEventListeners();

  // Initialize available cameras
  initializeCameras();

  // Initialize settings
  loadSettings();

  // Update timestamp
  updateTimestamp();
  setInterval(updateTimestamp, 1000);

  console.log("🎥 Webcam system ready");
}

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
  // Control buttons
  document.getElementById("startBtn").addEventListener("click", startCamera);
  document.getElementById("stopBtn").addEventListener("click", stopCamera);
  document.getElementById("captureBtn").addEventListener("click", captureFrame);
  document.getElementById("resetBtn").addEventListener("click", resetSettings);
  document
    .getElementById("forceStopBtn")
    .addEventListener("click", forceStopProcessing);
  document
    .getElementById("clearBackdropBtn")
    .addEventListener("click", clearAllBackdrops);
  document.getElementById("debugBtn").addEventListener("click", showDebugInfo);

  // Settings controls
  document
    .getElementById("confidenceSlider")
    .addEventListener("input", updateConfidence);
  document.getElementById("iouSlider").addEventListener("input", updateIou);
  document
    .getElementById("autoInterval")
    .addEventListener("input", updateInterval);
  document
    .getElementById("cameraSelect")
    .addEventListener("change", updateCamera);
  document
    .getElementById("resolutionSelect")
    .addEventListener("change", updateResolution);

  // Mode selection
  document.querySelectorAll('input[name="detectionMode"]').forEach((radio) => {
    radio.addEventListener("change", updateDetectionMode);
  });

  // Export buttons
  document
    .getElementById("exportJsonBtn")
    .addEventListener("click", exportJSON);
  document.getElementById("exportCsvBtn").addEventListener("click", exportCSV);

  // Keyboard controls
  document.addEventListener("keydown", handleKeyPress);

  console.log("🎮 Event listeners initialized");
}

/**
 * Initialize available cameras
 */
async function initializeCameras() {
  try {
    // Request permission first
    await navigator.mediaDevices.getUserMedia({ video: true });

    // Get available devices
    const devices = await navigator.mediaDevices.enumerateDevices();
    const videoDevices = devices.filter(
      (device) => device.kind === "videoinput"
    );

    // Update camera select options
    const cameraSelect = document.getElementById("cameraSelect");
    cameraSelect.innerHTML = "";

    videoDevices.forEach((device, index) => {
      const option = document.createElement("option");
      option.value = index;
      option.textContent = device.label || `กล้อง ${index + 1}`;
      cameraSelect.appendChild(option);
    });

    console.log(`📹 Found ${videoDevices.length} camera(s)`);

    // Stop the permission stream
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    stream.getTracks().forEach((track) => track.stop());
  } catch (error) {
    console.warn("Could not initialize cameras:", error);

    // Fallback to default options
    const cameraSelect = document.getElementById("cameraSelect");
    cameraSelect.innerHTML = `
      <option value="0">กล้องหลัก (0)</option>
      <option value="1">กล้องรอง (1)</option>
      <option value="2">กล้องที่ 3 (2)</option>
    `;
  }
}

/**
 * Load saved settings
 */
function loadSettings() {
  const savedSettings = localStorage.getItem("webcamSettings");
  if (savedSettings) {
    settings = { ...settings, ...JSON.parse(savedSettings) };
    applySettings();
  }
}

/**
 * Save current settings
 */
function saveSettings() {
  localStorage.setItem("webcamSettings", JSON.stringify(settings));
}

/**
 * Apply settings to UI
 */
function applySettings() {
  document.getElementById("confidenceSlider").value = settings.confidence;
  document.getElementById("confidenceValue").textContent = settings.confidence;

  document.getElementById("iouSlider").value = settings.iou;
  document.getElementById("iouValue").textContent = settings.iou;

  document.getElementById("autoInterval").value = settings.autoInterval;
  document.getElementById("intervalValue").textContent = settings.autoInterval;

  document.getElementById("cameraSelect").value = settings.camera;
  document.getElementById("resolutionSelect").value = settings.resolution;
}

/**
 * Reset settings to default
 */
function resetSettings() {
  settings = {
    confidence: 0.25,
    iou: 0.45,
    camera: 0,
    resolution: "1280x720",
    autoInterval: 3, // Back to 3 seconds
  };

  applySettings();
  saveSettings();

  showNotification("การตั้งค่าถูกรีเซ็ตแล้ว", "info");
  console.log("⚙️ Settings reset to default");
}

/**
 * Start camera
 */
async function startCamera() {
  try {
    updateStatus("กำลังเริ่มกล้อง...", "warning");

    // Stop existing stream
    if (stream) {
      stopCamera();
    }

    // Get resolution
    const [width, height] = settings.resolution.split("x").map(Number);

    // Configure video constraints with fallback
    let constraints = {
      video: {
        width: { ideal: width, max: width },
        height: { ideal: height, max: height },
        frameRate: { ideal: 30, max: 30 },
      },
    };

    // Add device ID if not default
    if (
      settings.camera !== 0 &&
      settings.camera !== "0" &&
      settings.camera !== "default"
    ) {
      // Try to get available devices first
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(
          (device) => device.kind === "videoinput"
        );

        if (videoDevices.length > settings.camera) {
          constraints.video.deviceId = {
            exact: videoDevices[settings.camera].deviceId,
          };
        }
      } catch (deviceError) {
        console.warn("Could not enumerate devices, using default camera");
      }
    }

    console.log("Camera constraints:", constraints);

    // Get user media with error handling
    try {
      stream = await navigator.mediaDevices.getUserMedia(constraints);
    } catch (constraintError) {
      console.warn(
        "Specific constraints failed, trying basic constraints:",
        constraintError
      );

      // Fallback to basic constraints
      constraints = {
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      };

      stream = await navigator.mediaDevices.getUserMedia(constraints);
    }

    // Create video element
    video = document.createElement("video");
    video.srcObject = stream;
    video.autoplay = true;
    video.playsInline = true;

    // Wait for video to load
    await new Promise((resolve) => {
      video.onloadedmetadata = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        resolve();
      };
    });

    // Start processing
    isRunning = true;
    animationId = requestAnimationFrame(processFrame);

    // Update UI
    updateStatus("กล้องทำงาน", "success");
    updateControlButtons(true);

    console.log("📹 Camera started successfully");
    console.log(`Video resolution: ${video.videoWidth}x${video.videoHeight}`);
  } catch (error) {
    console.error("Error starting camera:", error);
    showError("ไม่สามารถเริ่มกล้องได้: " + error.message);
    updateStatus("ไม่สามารถเริ่มกล้องได้", "danger");
  }
}

/**
 * Stop camera
 */
function stopCamera() {
  isRunning = false;

  // หยุด animation frame
  if (animationId) {
    cancelAnimationFrame(animationId);
    animationId = null;
    console.log("🛑 Animation frame stopped on camera stop");
  }

  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }

  if (video) {
    video.srcObject = null;
    video = null;
  }

  // Clear canvas
  if (ctx) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Add stopped text
    ctx.fillStyle = "#fff";
    ctx.font = "24px Arial";
    ctx.textAlign = "center";
    ctx.fillText("กล้องหยุดทำงาน", canvas.width / 2, canvas.height / 2);
  }

  updateStatus("กล้องหยุดทำงาน", "danger");
  updateControlButtons(false);
  hideDetectionInfo();

  console.log("📹 Camera stopped");
}

/**
 * Process video frame
 */
function processFrame() {
  if (!isRunning || !video) {
    // หยุด animation frame หากไม่ทำงาน
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }
    return;
  }

  // Draw video frame
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  // Update FPS
  updateFPS();

  // Auto detection - only if not currently processing
  if (detectionMode === "auto" && !isProcessing) {
    const now = Date.now();
    if (now - lastApiCall >= settings.autoInterval * 1000) {
      captureAndAnalyze();
      lastApiCall = now;
    }
  }

  // Continue processing
  animationId = requestAnimationFrame(processFrame);
}

/**
 * Capture frame manually
 */
function captureFrame() {
  if (!isRunning) {
    showError("กรุณาเริ่มกล้องก่อน");
    return;
  }

  if (isProcessing) {
    showError("กำลังประมวลผลอยู่ กรุณารอสักครู่");
    return;
  }

  captureAndAnalyze();
}

/**
 * Capture and analyze frame
 */
async function captureAndAnalyze() {
  // Prevent multiple simultaneous API calls
  if (isProcessing) {
    console.log("⏳ Already processing, skipping...");
    showNotification("กำลังประมวลผลอยู่ กรุณารอสักครู่...", "warning");
    return;
  }

  try {
    isProcessing = true;
    const startTime = Date.now();

    // Show loading with more details
    showLoadingWithStatus("กำลังถ่ายภาพ...");
    updateStatus("กำลังถ่ายภาพ...", "warning");

    console.log("🚀 Starting capture and analyze...");

    // Set a hard timeout to force completion
    const hardTimeout = setTimeout(() => {
      console.log("🛑 Hard timeout - forcing completion");
      if (isProcessing) {
        hideLoadingWithStatus();
        isProcessing = false;
        showNotification("การประมวลผลหมดเวลา - บังคับหยุด", "danger");
        updateStatus("หมดเวลา - ลองใหม่", "danger");
      }
    }, 10000); // 10 second hard limit

    // Create a smaller canvas for API processing
    const tempCanvas = document.createElement("canvas");
    const tempCtx = tempCanvas.getContext("2d");

    // Reduce size for faster processing (max 800px width)
    const maxWidth = 800;
    const scale = Math.min(1, maxWidth / canvas.width);
    tempCanvas.width = canvas.width * scale;
    tempCanvas.height = canvas.height * scale;

    // Draw scaled image
    tempCtx.drawImage(canvas, 0, 0, tempCanvas.width, tempCanvas.height);

    // Update loading status
    showLoadingWithStatus("กำลังประมวลผลภาพ...");

    // Get image data with lower quality for faster processing
    const imageData = tempCanvas.toDataURL("image/jpeg", 0.5);

    // Convert to blob
    const response = await fetch(imageData);
    const blob = await response.blob();

    // Update loading status
    showLoadingWithStatus("กำลังส่งข้อมูลไป API...");

    // Create form data
    const formData = new FormData();
    formData.append("file", blob, `capture_${Date.now()}.jpg`);
    formData.append("confidence", settings.confidence);
    formData.append("source", "webcam");

    // Send to API with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.log("⏰ API timeout after 8 seconds");
      controller.abort();
    }, 8000); // Reduced to 8 seconds

    updateStatus("กำลังส่งข้อมูลไป API...", "warning");

    // เลือก API endpoint ตามโหมด
    const apiEndpoint =
      detectionMode === "auto" ? "/api/detect-yolo" : "/api/detect";
    console.log(`📡 Using ${apiEndpoint} for ${detectionMode} mode`);

    const apiResponse = await fetch(apiEndpoint, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!apiResponse.ok) {
      throw new Error(`HTTP ${apiResponse.status}: ${apiResponse.statusText}`);
    }

    const result = await apiResponse.json();

    // Calculate processing time
    const processingTime = Date.now() - startTime;
    console.log(`⏱️ API processing time: ${processingTime}ms`);

    // Update statistics
    stats.apiCalls++;
    updateStatistics();

    // Handle API Rate Limit
    if (result.error && result.error.includes("Rate Limit")) {
      showDetectionInfo("Rate Limit - รอสักครู่", 0, "warning");
      showNotification("🚫 เรียกใช้ API บ่อยเกินไป - รอสักครู่", "warning");
      updateStatus("Rate Limit - รอสักครู่", "warning");

      // Increase auto interval temporarily
      if (detectionMode === "auto") {
        settings.autoInterval = Math.max(settings.autoInterval, 10);
        document.getElementById("autoInterval").value = settings.autoInterval;
        document.getElementById("intervalValue").textContent =
          settings.autoInterval;
      }

      hideLoadingWithStatus();
      isProcessing = false;
      return;
    }

    // Process result with better user feedback
    if (result.success && result.license_plate) {
      stats.detections++;

      console.log("✅ Detection successful:", result.license_plate);

      // แสดงกรอบ YOLO detection หากมี
      if (result.bbox && detectionMode === "auto") {
        drawBoundingBox(result.bbox, result.yolo_confidence);
        console.log(
          `📦 Drew bounding box: ${result.bbox}, confidence: ${result.yolo_confidence}`
        );
      }

      // Show success with detailed info
      const confidenceText = result.yolo_confidence
        ? `YOLO: ${(result.yolo_confidence * 100).toFixed(1)}% | API: ${(
            result.confidence * 100
          ).toFixed(1)}%`
        : `${(result.confidence * 100).toFixed(1)}%`;

      showDetectionInfo(
        result.license_plate,
        result.confidence || 0,
        "success"
      );
      showNotification(
        `🎯 พบป้ายทะเบียน: ${result.license_plate} (${confidenceText})`,
        "success"
      );

      addResult(canvas.toDataURL("image/jpeg", 0.8), result);
      updateStatus(`พบป้ายทะเบียน: ${result.license_plate}`, "success");

      console.log("✅ UI updated successfully");
    } else {
      console.log("⚠️ No detection found:", result);

      // แสดงกรอบ YOLO detection แม้ไม่มีการอ่านป้าย
      if (
        result.yolo_detections &&
        result.yolo_detections.length > 0 &&
        detectionMode === "auto"
      ) {
        result.yolo_detections.forEach((detection) => {
          drawBoundingBox(detection.bbox, detection.confidence, false);
        });
        console.log(
          `📦 Drew ${result.yolo_detections.length} YOLO detection boxes`
        );
      }

      // Show no detection found with clear message
      const errorMsg = result.error || "ไม่พบป้ายทะเบียนในภาพ";
      showDetectionInfo(errorMsg, 0, "warning");
      showNotification(
        `🔍 ${errorMsg} (ใช้เวลา ${(processingTime / 1000).toFixed(1)}s)`,
        "info"
      );
      updateStatus("ไม่พบป้ายทะเบียน - ลองถ่ายใหม่", "warning");
    }

    console.log("🔄 Hiding loading modal...");
    hideLoadingWithStatus();

    // บังคับซ่อน loading modal หากไม่หายภายใน 500ms
    setTimeout(() => {
      console.log("🔄 Force hiding loading modal with timeout...");
      const loadingModal = document.getElementById("loadingModal");
      if (loadingModal && loadingModal.style.display !== "none") {
        loadingModal.style.display = "none";
        document.body.classList.remove("modal-open");

        // ลบ backdrop ทุกอันที่ค้าง
        const backdrops = document.querySelectorAll(".modal-backdrop");
        backdrops.forEach((backdrop) => backdrop.remove());

        // Reset body styles
        document.body.style.overflow = "";
        document.body.style.paddingRight = "";
        document.body.style.marginRight = "";

        console.log("✅ Force hide completed");
      }
    }, 500);

    isProcessing = false;
    console.log("✅ Processing completed, isProcessing:", isProcessing);

    // เริ่ม animation frame ใหม่หากกล้องยังทำงานอยู่
    if (isRunning && !animationId) {
      console.log("🔄 Restarting animation frame after processing...");
      animationId = requestAnimationFrame(processFrame);
    }

    // Clear the hard timeout
    clearTimeout(hardTimeout);
  } catch (error) {
    console.error("Error in capture and analyze:", error);
    hideLoadingWithStatus();

    // บังคับซ่อน loading modal ในกรณี error
    setTimeout(() => {
      console.log("🔄 Force hiding loading modal after error...");
      const loadingModal = document.getElementById("loadingModal");
      if (loadingModal && loadingModal.style.display !== "none") {
        loadingModal.style.display = "none";
        document.body.classList.remove("modal-open");
        const backdrop = document.querySelector(".modal-backdrop");
        if (backdrop) backdrop.remove();
        console.log("✅ Force hide after error completed");
      }
    }, 300);

    isProcessing = false;

    // Handle different types of errors with better user feedback
    if (error.name === "AbortError") {
      showError("⏰ การประมวลผลใช้เวลานานเกินไป (Timeout 8 วินาที)");
      showDetectionInfo("Timeout", 0, "danger");
      showNotification("การประมวลผลช้าเกินไป - ลองใหม่อีกครั้ง", "warning");
      updateStatus("Timeout - ลองใหม่อีกครั้ง", "danger");
    } else if (
      error.message.includes("429") ||
      error.message.includes("rate limit")
    ) {
      showError("🚫 เรียกใช้ API บ่อยเกินไป กรุณารอสักครู่");
      showDetectionInfo("Rate Limit", 0, "warning");
      showNotification("เรียกใช้บ่อยเกินไป - รอ 1 นาที", "warning");
      updateStatus("Rate Limit - รอสักครู่", "warning");
      // Increase auto interval temporarily
      if (detectionMode === "auto") {
        settings.autoInterval = Math.max(settings.autoInterval, 10);
        document.getElementById("autoInterval").value = settings.autoInterval;
        document.getElementById("intervalValue").textContent =
          settings.autoInterval;
      }
    } else if (error.message.includes("fetch")) {
      showError("🌐 ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้");
      showDetectionInfo("Connection Error", 0, "danger");
      showNotification("ปัญหาการเชื่อมต่อ - ตรวจสอบอินเทอร์เน็ต", "danger");
      updateStatus("ไม่สามารถเชื่อมต่อได้", "danger");
    } else {
      showError("❌ เกิดข้อผิดพลาด: " + error.message);
      showDetectionInfo("ข้อผิดพลาด", 0, "danger");
      showNotification("เกิดข้อผิดพลาด - ลองใหม่อีกครั้ง", "danger");
      updateStatus("เกิดข้อผิดพลาด", "danger");
    }

    // Update statistics anyway
    stats.apiCalls++;
    updateStatistics();

    // เริ่ม animation frame ใหม่หากกล้องยังทำงานอยู่
    if (isRunning && !animationId) {
      console.log("🔄 Restarting animation frame after error...");
      animationId = requestAnimationFrame(processFrame);
    }

    // Clear the hard timeout
    clearTimeout(hardTimeout);
  }
}

/**
 * Add result to history
 */
function addResult(imageData, result) {
  const resultItem = {
    id: Date.now(),
    image: imageData,
    plate: result.license_plate,
    confidence: result.confidence || 0,
    timestamp: new Date().toLocaleString("th-TH"),
    raw_result: result,
  };

  sessionResults.unshift(resultItem);

  // Limit to 50 results
  if (sessionResults.length > 50) {
    sessionResults = sessionResults.slice(0, 50);
  }

  updateLatestResult(resultItem);
  updateResultsList();

  console.log("📋 Result added:", resultItem.plate);
}

/**
 * Update latest result display
 */
function updateLatestResult(result) {
  const latestResult = document.getElementById("latestResult");
  const latestImage = document.getElementById("latestImage");
  const latestPlate = document.getElementById("latestPlate");
  const latestConfidence = document.getElementById("latestConfidence");
  const latestTime = document.getElementById("latestTime");

  latestImage.src = result.image;
  latestPlate.textContent = result.plate;
  latestConfidence.style.width = `${result.confidence * 100}%`;
  latestTime.textContent = result.timestamp;

  latestResult.style.display = "block";
  latestResult.classList.add("fade-in-up");
}

/**
 * Update results list
 */
function updateResultsList() {
  const resultsList = document.getElementById("resultsList");

  if (sessionResults.length === 0) {
    resultsList.innerHTML = `
      <div class="empty-results">
        <i class="fas fa-camera"></i>
        <p>ยังไม่มีผลลัพธ์</p>
        <small>เริ่มกล้องเพื่อดูผลลัพธ์</small>
      </div>
    `;
    return;
  }

  resultsList.innerHTML = sessionResults
    .map(
      (result) => `
    <div class="result-item fade-in-up">
      <div class="result-content">
        <img src="${result.image}" alt="Capture" />
        <div class="result-text">
          <div class="result-plate">${result.plate}</div>
          <div class="result-time">${result.timestamp}</div>
        </div>
      </div>
    </div>
  `
    )
    .join("");
}

/**
 * Draw bounding box on canvas
 */
function drawBoundingBox(bbox, confidence, isSuccess = true) {
  if (!ctx || !bbox || bbox.length !== 4) return;

  const [x1, y1, x2, y2] = bbox;
  const width = x2 - x1;
  const height = y2 - y1;

  // Save current context
  ctx.save();

  // Set style based on success
  ctx.strokeStyle = isSuccess ? "#00ff00" : "#ffff00"; // Green for success, Yellow for detection only
  ctx.lineWidth = 3;
  ctx.fillStyle = isSuccess ? "rgba(0, 255, 0, 0.1)" : "rgba(255, 255, 0, 0.1)";

  // Draw rectangle
  ctx.strokeRect(x1, y1, width, height);
  ctx.fillRect(x1, y1, width, height);

  // Draw confidence text
  const text = `${(confidence * 100).toFixed(1)}%`;
  ctx.font = "16px Arial";
  ctx.fillStyle = isSuccess ? "#00ff00" : "#ffff00";
  ctx.strokeStyle = "#000000";
  ctx.lineWidth = 2;

  // Text background
  const textWidth = ctx.measureText(text).width;
  ctx.fillStyle = "rgba(0, 0, 0, 0.8)";
  ctx.fillRect(x1, y1 - 25, textWidth + 10, 25);

  // Text
  ctx.fillStyle = isSuccess ? "#00ff00" : "#ffff00";
  ctx.strokeText(text, x1 + 5, y1 - 8);
  ctx.fillText(text, x1 + 5, y1 - 8);

  // Restore context
  ctx.restore();

  // Clear box after 3 seconds
  setTimeout(() => {
    clearBoundingBoxes();
  }, 3000);
}

/**
 * Clear all bounding boxes by redrawing video frame
 */
function clearBoundingBoxes() {
  if (ctx && video && isRunning) {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  }
}

/**
 * Show detection info
 */
function showDetectionInfo(text, confidence, type = "info") {
  const detectionInfo = document.getElementById("detectionInfo");
  const detectionText = document.getElementById("detectionText");

  // Update text with confidence
  if (confidence > 0) {
    detectionText.textContent = `${text} (${(confidence * 100).toFixed(1)}%)`;
  } else {
    detectionText.textContent = text;
  }

  // Update styling based on type
  detectionInfo.className = `alert alert-${type} fade show`;
  detectionInfo.style.display = "block";

  // Add icon based on type
  const icon =
    type === "success"
      ? "🎯"
      : type === "warning"
      ? "🔍"
      : type === "danger"
      ? "❌"
      : "ℹ️";
  detectionText.textContent = `${icon} ${detectionText.textContent}`;

  // Auto hide after 8 seconds (increased from 5)
  setTimeout(() => {
    hideDetectionInfo();
  }, 8000);
}

/**
 * Hide detection info
 */
function hideDetectionInfo() {
  const detectionInfo = document.getElementById("detectionInfo");
  detectionInfo.style.display = "none";
}

/**
 * Update FPS counter
 */
function updateFPS() {
  fpsCounter++;
  const now = Date.now();

  if (now - lastFpsTime >= 1000) {
    stats.fps = fpsCounter;
    fpsCounter = 0;
    lastFpsTime = now;
    updateStatistics();
  }
}

/**
 * Update statistics display
 */
function updateStatistics() {
  document.getElementById("fpsDisplay").textContent = stats.fps;
  document.getElementById("detectionsCount").textContent = stats.detections;
  document.getElementById("apiCallsCount").textContent = stats.apiCalls;

  // Update status based on processing state
  if (isProcessing) {
    updateStatus("กำลังประมวลผล...", "warning");
    console.log("📊 Status: Processing...");
  } else if (isRunning) {
    updateStatus("กล้องทำงาน", "success");
    console.log("📊 Status: Camera running");
  }

  console.log(
    "📊 Stats updated - FPS:",
    stats.fps,
    "Detections:",
    stats.detections,
    "API Calls:",
    stats.apiCalls
  );
}

/**
 * Update status display
 */
function updateStatus(text, type) {
  const statusIcon = document.getElementById("statusIcon");
  const statusText = document.getElementById("statusText");

  statusIcon.className = `fas fa-circle text-${type}`;
  statusText.textContent = text;
}

/**
 * Update control buttons
 */
function updateControlButtons(isActive) {
  document.getElementById("startBtn").disabled = isActive;
  document.getElementById("stopBtn").disabled = !isActive;
  document.getElementById("captureBtn").disabled = !isActive;
}

/**
 * Update timestamp
 */
function updateTimestamp() {
  const timestamp = document.getElementById("timestamp");
  timestamp.textContent = new Date().toLocaleString("th-TH");
}

/**
 * Settings event handlers
 */
function updateConfidence(event) {
  settings.confidence = parseFloat(event.target.value);
  document.getElementById("confidenceValue").textContent = settings.confidence;
  saveSettings();
}

function updateIou(event) {
  settings.iou = parseFloat(event.target.value);
  document.getElementById("iouValue").textContent = settings.iou;
  saveSettings();
}

function updateInterval(event) {
  settings.autoInterval = parseInt(event.target.value);
  document.getElementById("intervalValue").textContent = settings.autoInterval;
  saveSettings();
}

function updateCamera(event) {
  settings.camera = parseInt(event.target.value);
  saveSettings();

  console.log("🎥 Camera changed to:", settings.camera);

  // Restart camera if running
  if (isRunning) {
    stopCamera();
    setTimeout(startCamera, 1000);
  }
}

function updateResolution(event) {
  settings.resolution = event.target.value;
  saveSettings();

  // Restart camera if running
  if (isRunning) {
    stopCamera();
    setTimeout(startCamera, 500);
  }
}

function updateDetectionMode(event) {
  detectionMode = event.target.value;

  const autoSettings = document.getElementById("autoSettings");
  const manualSettings = document.getElementById("manualSettings");

  if (detectionMode === "auto") {
    autoSettings.style.display = "block";
    manualSettings.style.display = "none";
  } else {
    autoSettings.style.display = "none";
    manualSettings.style.display = "block";
  }

  console.log("🎛️ Detection mode changed to:", detectionMode);
}

/**
 * Handle keyboard input
 */
function handleKeyPress(event) {
  if (event.key.toLowerCase() === "s" && detectionMode === "manual") {
    event.preventDefault();
    captureFrame();
  }
}

/**
 * Force stop processing (emergency)
 */
function forceStopProcessing() {
  console.log("🛑 Force stopping processing...");

  // หยุดการประมวลผล
  isProcessing = false;

  // หยุด animation frame
  if (animationId) {
    cancelAnimationFrame(animationId);
    animationId = null;
    console.log("🛑 Animation frame stopped");
  }

  // ปิด loading modal
  hideLoadingWithStatus();

  // ลบ backdrop ค้างทั้งหมด (Emergency)
  setTimeout(() => {
    clearAllBackdrops();
  }, 100);

  // อัปเดตสถานะ
  updateStatus("บังคับหยุดการประมวลผล - พร้อมใช้งานต่อ", "warning");
  showNotification("การประมวลผลถูกบังคับหยุด", "warning");

  // เริ่ม animation frame ใหม่หากกล้องยังทำงานอยู่
  if (isRunning && !animationId) {
    console.log("🔄 Restarting animation frame after force stop...");
    animationId = requestAnimationFrame(processFrame);
  }

  console.log("🛑 Force stop completed");
}

/**
 * Clear all modal backdrops (Emergency function)
 */
function clearAllBackdrops() {
  console.log("🚨 Emergency: Clearing all backdrops...");

  // ลบ backdrop ทุกประเภท
  const selectors = [
    ".modal-backdrop",
    ".modal-backdrop.fade",
    ".modal-backdrop.show",
    ".modal-backdrop.fade.show",
  ];

  let totalRemoved = 0;
  selectors.forEach((selector) => {
    const elements = document.querySelectorAll(selector);
    elements.forEach((element) => {
      element.remove();
      totalRemoved++;
    });
  });

  // Reset body state
  document.body.classList.remove("modal-open");
  document.body.style.overflow = "";
  document.body.style.paddingRight = "";
  document.body.style.marginRight = "";
  document.body.removeAttribute("data-bs-overflow");
  document.body.removeAttribute("data-bs-padding-right");

  // ซ่อน modal ทุกอันที่อาจจะติดค้าง
  const modals = document.querySelectorAll(".modal");
  modals.forEach((modal) => {
    modal.style.display = "none";
    modal.classList.remove("show");
    modal.setAttribute("aria-hidden", "true");
  });

  console.log(
    `🚨 Emergency clear completed - removed ${totalRemoved} elements`
  );
  showNotification(
    `ลบ backdrop ${totalRemoved} อัน - หน้าจอพร้อมใช้งาน`,
    "success"
  );
  updateStatus("ลบ backdrop สำเร็จ - พร้อมใช้งาน", "success");
}

/**
 * Show debug information
 */
function showDebugInfo() {
  const debugInfo = {
    isRunning: isRunning,
    isProcessing: isProcessing,
    detectionMode: detectionMode,
    stats: stats,
    settings: settings,
    sessionResults: sessionResults.length + " results",
    video: video
      ? {
          width: video.videoWidth,
          height: video.videoHeight,
          readyState: video.readyState,
        }
      : "No video",
    canvas: canvas
      ? {
          width: canvas.width,
          height: canvas.height,
        }
      : "No canvas",
  };

  console.log("🐛 Debug Info:", debugInfo);
  alert(
    "Debug info logged to console.\n\n" +
      "isProcessing: " +
      isProcessing +
      "\n" +
      "isRunning: " +
      isRunning +
      "\n" +
      "detectionMode: " +
      detectionMode +
      "\n" +
      "API Calls: " +
      stats.apiCalls +
      "\n" +
      "Detections: " +
      stats.detections
  );
}

/**
 * Export functions
 */
function exportJSON() {
  if (sessionResults.length === 0) {
    showError("ไม่มีข้อมูลสำหรับส่งออก");
    return;
  }

  const exportData = {
    session: {
      start_time: sessionResults[sessionResults.length - 1]?.timestamp,
      end_time: sessionResults[0]?.timestamp,
      total_results: sessionResults.length,
      settings: settings,
      statistics: stats,
    },
    results: sessionResults,
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: "application/json",
  });

  downloadFile(blob, `webcam_results_${Date.now()}.json`);
  showNotification("ส่งออก JSON สำเร็จ", "success");
}

function exportCSV() {
  if (sessionResults.length === 0) {
    showError("ไม่มีข้อมูลสำหรับส่งออก");
    return;
  }

  const headers = ["เวลา", "ป้ายทะเบียน", "ความเชื่อมั่น"];
  const rows = sessionResults.map((result) => [
    result.timestamp,
    result.plate,
    (result.confidence * 100).toFixed(2) + "%",
  ]);

  const csvContent = [headers, ...rows]
    .map((row) => row.map((cell) => `"${cell}"`).join(","))
    .join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  downloadFile(blob, `webcam_results_${Date.now()}.csv`);
  showNotification("ส่งออก CSV สำเร็จ", "success");
}

/**
 * Download file helper
 */
function downloadFile(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * UI Helper functions
 */
function showLoading() {
  const modal = new bootstrap.Modal(document.getElementById("loadingModal"));
  modal.show();
}

function showLoadingWithStatus(message) {
  console.log("🔄 showLoadingWithStatus() called with:", message);
  const modal = new bootstrap.Modal(document.getElementById("loadingModal"));
  const loadingText = document.getElementById("loadingText");
  if (loadingText) {
    loadingText.textContent = message;
  }
  modal.show();
  console.log("✅ Loading modal shown");

  // Auto-hide after 10 seconds as failsafe
  setTimeout(() => {
    if (isProcessing) {
      console.log("⚠️ Auto-hiding loading modal after 10 seconds");
      hideLoadingWithStatus();
      isProcessing = false;
      showNotification("การประมวลผลหมดเวลา - ลองใหม่", "warning");
    }
  }, 10000);
}

function hideLoading() {
  console.log("🔄 hideLoading() called");
  const modalElement = document.getElementById("loadingModal");
  const modal = bootstrap.Modal.getInstance(modalElement);

  if (modal) {
    console.log("🔄 Hiding modal instance...");
    modal.hide();
    console.log("✅ Modal.hide() completed");
  } else {
    console.log("⚠️ No modal instance found, trying to force hide");
    // Force hide modal by removing classes and attributes
    modalElement.classList.remove("show");
    modalElement.style.display = "none";
    modalElement.setAttribute("aria-hidden", "true");
    modalElement.removeAttribute("aria-modal");
    modalElement.removeAttribute("role");

    // Remove backdrop if exists
    const backdrop = document.querySelector(".modal-backdrop");
    if (backdrop) {
      backdrop.remove();
    }

    // Remove modal-open class from body
    document.body.classList.remove("modal-open");
    document.body.style.overflow = "";
    document.body.style.paddingRight = "";

    console.log("✅ Modal force hidden");
  }
}

function hideLoadingWithStatus() {
  console.log("🔄 hideLoadingWithStatus() called");

  // ทำหลายแบบพร้อมกัน
  hideLoading();

  // Direct force hide
  const loadingModal = document.getElementById("loadingModal");
  if (loadingModal) {
    loadingModal.style.display = "none";
    loadingModal.classList.remove("show");
    loadingModal.setAttribute("aria-hidden", "true");
    console.log("🔄 Direct style.display = 'none' applied");
  }

  // Remove ALL backdrops (อาจจะมีหลายอัน)
  const backdrops = document.querySelectorAll(".modal-backdrop");
  console.log(`🔄 Found ${backdrops.length} backdrop(s)`);
  backdrops.forEach((backdrop, index) => {
    backdrop.remove();
    console.log(`🔄 Backdrop ${index + 1} removed`);
  });

  // ลบ backdrop classes อื่นๆ ที่อาจจะค้าง
  const fadeBackdrops = document.querySelectorAll(".modal-backdrop.fade");
  fadeBackdrops.forEach((backdrop) => backdrop.remove());
  const showBackdrops = document.querySelectorAll(".modal-backdrop.show");
  showBackdrops.forEach((backdrop) => backdrop.remove());

  // Reset body - ลบทุก modal-related classes
  document.body.classList.remove("modal-open");
  document.body.style.overflow = "";
  document.body.style.paddingRight = "";
  document.body.style.marginRight = "";

  // ลบ attributes ที่อาจจะค้าง
  document.body.removeAttribute("data-bs-overflow");
  document.body.removeAttribute("data-bs-padding-right");

  console.log("🔄 Body classes and styles reset");

  // Reset loading text
  const loadingText = document.getElementById("loadingText");
  if (loadingText) {
    loadingText.textContent = "กำลังประมวลผล...";
  }

  console.log("✅ Loading modal hidden successfully");
}

function showError(message) {
  document.getElementById("errorMessage").textContent = message;
  const modal = new bootstrap.Modal(document.getElementById("errorModal"));
  modal.show();
}

function showNotification(message, type) {
  // Create notification element
  const notification = document.createElement("div");
  notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
  notification.style.cssText =
    "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";
  notification.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  document.body.appendChild(notification);

  // Auto remove after 3 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification);
    }
  }, 3000);
}

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
  if (isRunning) {
    stopCamera();
  }
});
