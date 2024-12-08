const videoElement = document.createElement('video');
const canvasElement = document.createElement('canvas');
const canvasCtx = canvasElement.getContext('2d');

let isRightWinkDetected = false;
let waveCount = 0;
let lastWaveTime = 0;
const gestureTimeout = 1500; // 1.5 seconds to complete both gestures
const waveCooldown = 500; // 500ms between waves

function setupGestureLogout() {
    // Style and add video/canvas elements
    videoElement.setAttribute('class', 'gesture-video');
    canvasElement.setAttribute('class', 'gesture-canvas');
    
    const gestureContainer = document.createElement('div');
    gestureContainer.id = 'gesture-container';
    gestureContainer.style.position = 'fixed';
    gestureContainer.style.bottom = '20px';
    gestureContainer.style.right = '20px';
    gestureContainer.style.width = '160px';
    gestureContainer.style.height = '120px';
    gestureContainer.style.zIndex = '1000';
    
    gestureContainer.appendChild(videoElement);
    gestureContainer.appendChild(canvasElement);
    document.body.appendChild(gestureContainer);

    // Initialize MediaPipe Holistic
    const holistic = new Holistic({
        locateFile: (file) => {
            return `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${file}`;
        }
    });

    holistic.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });

    holistic.onResults(onResults);

    const camera = new Camera(videoElement, {
        onFrame: async () => {
            await holistic.send({image: videoElement});
        },
        width: 160,
        height: 120
    });

    camera.start();
}

function onResults(results) {
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);

    // Check for right wink
    if (results.faceLandmarks) {
        const rightEyeUpper = results.faceLandmarks[159];
        const rightEyeLower = results.faceLandmarks[145];
        const eyeDistance = Math.abs(rightEyeUpper.y - rightEyeLower.y);
        
        if (eyeDistance < 0.02) {
            isRightWinkDetected = true;
            setTimeout(() => { isRightWinkDetected = false; }, gestureTimeout);
        }
    }

    // Check for wave gesture
    if (results.poseLandmarks) {
        const rightWrist = results.poseLandmarks[16];
        const rightShoulder = results.poseLandmarks[12];
        const currentTime = Date.now();
        
        // Detect wave motion (hand moving side to side above shoulder)
        if (rightWrist && rightShoulder && 
            rightWrist.y < rightShoulder.y && 
            currentTime - lastWaveTime > waveCooldown) {
            
            // Track wave count
            waveCount++;
            lastWaveTime = currentTime;
            
            // Reset wave count after timeout
            setTimeout(() => {
                if (waveCount > 0) waveCount--;
            }, gestureTimeout);
        }
    }

    // If right wink and two waves are detected within the timeout period
    if (isRightWinkDetected && waveCount >= 2) {
        handleLogoutGesture();
        // Reset counters
        waveCount = 0;
        isRightWinkDetected = false;
    }

    // Draw landmarks for visual feedback
    drawConnectors(canvasCtx, results.faceLandmarks, FACEMESH_TESSELATION,
        {color: '#C0C0C070', lineWidth: 1});
    drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS,
        {color: '#00FF00', lineWidth: 2});
    
    canvasCtx.restore();
}

function handleLogoutGesture() {
    // Reset gesture flags
    isRightWinkDetected = false;
    waveCount = 0;

    // Show confirmation modal
    const modal = document.getElementById('logout-confirm-modal');
    modal.classList.remove('hidden');
    
    let logoutTimer;

    // Allow cancellation
    const cancelButton = document.getElementById('cancel-logout');
    const modalContent = modal.querySelector('.relative');

    // Handle modal backdrop click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            clearTimeout(logoutTimer);
            modal.classList.add('hidden');
        }
    });

    // Handle cancel button click
    cancelButton.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        clearTimeout(logoutTimer);
        modal.classList.add('hidden');
    });

    // Auto logout after 3 seconds if not canceled
    logoutTimer = setTimeout(() => {
        // Use the dashboard URL as fallback if logoutUrl is not properly set
        const dashboardUrl = '/';
        window.location.href = logoutUrl || dashboardUrl;
    }, 3000);
} 