/**
 * ========================================
 * 🚗 License Plate Reader - History Page JavaScript
 * ========================================
 */

// Global Variables
let fileModal;

/**
 * Initialize the history page
 */
document.addEventListener("DOMContentLoaded", function () {
  initializeHistoryPage();
  console.log("📋 History page initialized");
});

/**
 * Initialize history page functionality
 */
function initializeHistoryPage() {
  // Initialize Bootstrap modal
  const modalElement = document.getElementById("fileModal");
  if (modalElement) {
    fileModal = new bootstrap.Modal(modalElement);
  }

  // Initialize search functionality
  initializeSearch();

  // Add loading animation to file cards
  animateFileCards();
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("input", debounce(searchFiles, 300));
  }
}

/**
 * Animate file cards on load
 */
function animateFileCards() {
  const fileCards = document.querySelectorAll(".file-card");
  fileCards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
  });
}

/**
 * View file in modal
 */
function viewFile(filename) {
  try {
    // Update modal image source
    const modalImage = document.getElementById("modalImage");
    if (modalImage) {
      modalImage.src = `/static/uploads/${filename}`;
      modalImage.alt = filename;

      // Update modal title
      const modalTitle = document.querySelector(".modal-title");
      if (modalTitle) {
        modalTitle.textContent = `ดูไฟล์: ${getDisplayFilename(filename)}`;
      }

      // Show modal
      if (fileModal) {
        fileModal.show();
      }

      console.log("👁️ Viewing file:", filename);
    }
  } catch (error) {
    console.error("❌ Error viewing file:", error);
    showAlert("เกิดข้อผิดพลาดในการแสดงไฟล์", "error");
  }
}

/**
 * Delete file (placeholder functionality)
 */
function deleteFile(filename) {
  const displayName = getDisplayFilename(filename);

  if (confirm(`คุณต้องการลบไฟล์ "${displayName}" หรือไม่?`)) {
    // TODO: Implement actual delete functionality
    // This would require a DELETE endpoint in the Flask app

    showAlert("ฟีเจอร์ลบไฟล์ยังไม่พร้อมใช้งาน", "info");
    console.log("🗑️ Delete requested for:", filename);

    // Placeholder animation for future implementation
    animateFileRemoval(filename);
  }
}

/**
 * Search files functionality
 */
function searchFiles() {
  const searchInput = document.getElementById("searchInput");
  if (!searchInput) return;

  const searchTerm = searchInput.value.toLowerCase().trim();
  const fileCards = document.querySelectorAll(".file-card");
  let visibleCount = 0;

  fileCards.forEach((card) => {
    const fileName = card.querySelector(".file-name");
    if (fileName) {
      const fileNameText = fileName.textContent.toLowerCase();
      const cardContainer = card.parentElement;

      if (searchTerm === "" || fileNameText.includes(searchTerm)) {
        cardContainer.style.display = "block";
        card.style.animation = "fadeInUp 0.3s ease-out";
        visibleCount++;
      } else {
        cardContainer.style.display = "none";
      }
    }
  });

  // Show/hide empty state
  toggleEmptyState(visibleCount === 0 && searchTerm !== "");

  console.log(`🔍 Search: "${searchTerm}" - ${visibleCount} results`);
}

/**
 * Toggle empty state display
 */
function toggleEmptyState(show) {
  let emptyState = document.getElementById("searchEmptyState");

  if (show && !emptyState) {
    // Create empty state element
    emptyState = document.createElement("div");
    emptyState.id = "searchEmptyState";
    emptyState.className = "empty-state";
    emptyState.innerHTML = `
            <i class="fas fa-search"></i>
            <h3>ไม่พบผลการค้นหา</h3>
            <p>ลองเปลี่ยนคำค้นหาและลองใหม่อีกครั้ง</p>
        `;

    // Insert after file grid
    const container = document.querySelector(".row");
    if (container) {
      container.parentNode.insertBefore(emptyState, container.nextSibling);
    }
  } else if (!show && emptyState) {
    emptyState.remove();
  }
}

/**
 * Get display filename (remove timestamp prefix)
 */
function getDisplayFilename(filename) {
  return filename.split("_").slice(1).join("_") || filename;
}

/**
 * Animate file removal (placeholder)
 */
function animateFileRemoval(filename) {
  const fileCards = document.querySelectorAll(".file-card");
  fileCards.forEach((card) => {
    const cardFilename = card.querySelector(".file-name").textContent;
    if (cardFilename.includes(getDisplayFilename(filename))) {
      card.style.transition = "all 0.3s ease";
      card.style.transform = "translateX(-100%)";
      card.style.opacity = "0";
    }
  });
}

/**
 * Show alert message
 */
function showAlert(message, type = "info") {
  // Create alert element
  const alert = document.createElement("div");
  alert.className = `alert alert-${type} alert-dismissible fade show`;
  alert.style.position = "fixed";
  alert.style.top = "20px";
  alert.style.right = "20px";
  alert.style.zIndex = "9999";
  alert.style.minWidth = "300px";

  alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  document.body.appendChild(alert);

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (alert.parentNode) {
      alert.remove();
    }
  }, 5000);
}

/**
 * Debounce function for search input
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

/**
 * Format date for display
 */
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString("th-TH", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Refresh page data
 */
function refreshPage() {
  window.location.reload();
}

/**
 * Go back to main page
 */
function goToMainPage() {
  window.location.href = "/";
}

/**
 * Download file (future implementation)
 */
function downloadFile(filename) {
  // TODO: Implement download functionality
  console.log("💾 Download requested for:", filename);
  showAlert("ฟีเจอร์ดาวน์โหลดยังไม่พร้อมใช้งาน", "info");
}

/**
 * Share file (future implementation)
 */
function shareFile(filename) {
  // TODO: Implement share functionality
  console.log("📤 Share requested for:", filename);
  showAlert("ฟีเจอร์แชร์ยังไม่พร้อมใช้งาน", "info");
}

// Export functions for global access
window.viewFile = viewFile;
window.deleteFile = deleteFile;
window.searchFiles = searchFiles;
window.refreshPage = refreshPage;
window.goToMainPage = goToMainPage;
window.downloadFile = downloadFile;
window.shareFile = shareFile;
