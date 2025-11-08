/**
 * Progressive Web App functionality
 */

// Register service worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('Service Worker registered:', registration);
        
        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker available
              showUpdateNotification();
            }
          });
        });
      })
      .catch((error) => {
        console.error('Service Worker registration failed:', error);
      });
  });
}

// Install prompt
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  showInstallButton();
});

// Show install button
function showInstallButton() {
  // Check if already installed
  if (window.matchMedia('(display-mode: standalone)').matches) {
    return; // Already installed
  }

  // Create install button if it doesn't exist
  let installBtn = document.getElementById('pwa-install-btn');
  if (!installBtn) {
    installBtn = document.createElement('button');
    installBtn.id = 'pwa-install-btn';
    installBtn.className = 'pwa-install-btn';
    installBtn.innerHTML = '📱 Install App';
    installBtn.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      color: white;
      border: none;
      border-radius: 25px;
      padding: 12px 24px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
      z-index: 10000;
      transition: all 0.3s ease;
    `;
    
    installBtn.addEventListener('mouseenter', () => {
      installBtn.style.transform = 'translateY(-2px)';
      installBtn.style.boxShadow = '0 6px 16px rgba(99, 102, 241, 0.5)';
    });
    
    installBtn.addEventListener('mouseleave', () => {
      installBtn.style.transform = 'translateY(0)';
      installBtn.style.boxShadow = '0 4px 12px rgba(99, 102, 241, 0.4)';
    });
    
    installBtn.addEventListener('click', installApp);
    document.body.appendChild(installBtn);
  }
}

// Install app
async function installApp() {
  if (!deferredPrompt) {
    return;
  }

  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  
  if (outcome === 'accepted') {
    console.log('User accepted the install prompt');
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
      installBtn.remove();
    }
  }
  
  deferredPrompt = null;
}

// Show update notification
function showUpdateNotification() {
  const notification = document.createElement('div');
  notification.className = 'pwa-update-notification';
  notification.innerHTML = `
    <div style="display: flex; align-items: center; gap: 12px;">
      <span>🔄 New version available!</span>
      <button onclick="updateApp()" style="
        background: #6366f1;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 12px;
        cursor: pointer;
        font-size: 12px;
        font-weight: 600;
      ">Update</button>
      <button onclick="this.parentElement.parentElement.remove()" style="
        background: transparent;
        color: #cbd5e1;
        border: none;
        cursor: pointer;
        font-size: 18px;
        padding: 0;
        width: 24px;
        height: 24px;
      ">×</button>
    </div>
  `;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 16px;
    color: #f1f5f9;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 10001;
    animation: slideIn 0.3s ease;
  `;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 10000);
}

// Update app
function updateApp() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      registrations.forEach((registration) => {
        registration.update();
      });
    });
    window.location.reload();
  }
}

// Check if app is installed
function isPWAInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone ||
         document.referrer.includes('android-app://');
}

// Online/Offline status
window.addEventListener('online', () => {
  console.log('App is online');
  showNotification('✅ Back online!', 'success');
});

window.addEventListener('offline', () => {
  console.log('App is offline');
  showNotification('⚠️ You are offline. Some features may be limited.', 'warning');
});

// Show notification helper
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: ${type === 'success' ? '#10b981' : type === 'warning' ? '#f59e0b' : '#6366f1'};
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 10002;
    animation: slideDown 0.3s ease;
  `;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideUp 0.3s ease';
    setTimeout(() => {
      if (notification.parentElement) {
        notification.remove();
      }
    }, 300);
  }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideDown {
    from {
      transform: translateX(-50%) translateY(-100%);
      opacity: 0;
    }
    to {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }
  }
  
  @keyframes slideUp {
    from {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }
    to {
      transform: translateX(-50%) translateY(-100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// Export for global use
window.updateApp = updateApp;

