const videoElement = document.createElement('video');
const canvasElement = document.createElement('canvas');
const canvasCtx = canvasElement.getContext('2d');

let previousWristX = null;
let waveCount = 0;
let lastWaveTime = 0;
let waveDirection = null;
let lastWaveDirection = null;
const waveThreshold = 0.03; // Made even more sensitive

function setupGestureLogout() {
    // Create a wrapper div for both camera and canvas
    const gestureWrapper = document.createElement('div');
    gestureWrapper.style.display = 'flex';
    gestureWrapper.style.gap = '10px';
    gestureWrapper.style.position = 'fixed';
    gestureWrapper.style.top = '20px';
    gestureWrapper.style.right = '20px';
    gestureWrapper.style.zIndex = '1000';

    // Camera container
    const cameraContainer = document.createElement('div');
    cameraContainer.id = 'camera-container';
    cameraContainer.style.width = '160px';
    cameraContainer.style.height = '140px';
    cameraContainer.style.background = 'rgba(0, 0, 0, 0.5)';
    cameraContainer.style.borderRadius = '8px';
    cameraContainer.style.padding = '10px';

    // Canvas container
    const canvasContainer = document.createElement('div');
    canvasContainer.id = 'canvas-container';
    canvasContainer.style.width = '160px';
    canvasContainer.style.height = '140px';
    canvasContainer.style.background = 'rgba(0, 0, 0, 0.5)';
    canvasContainer.style.borderRadius = '8px';
    canvasContainer.style.padding = '10px';

    // Style video and canvas
    videoElement.setAttribute('class', 'gesture-video');
    canvasElement.setAttribute('class', 'gesture-canvas');
    
    // Add labels
    const cameraLabel = document.createElement('div');
    cameraLabel.textContent = 'Wave Hand to Logout';
    cameraLabel.style.color = '#fff';
    cameraLabel.style.textAlign = 'center';
    cameraLabel.style.marginBottom = '5px';

    const canvasLabel = document.createElement('div');
    canvasLabel.textContent = 'Hand Detection';
    canvasLabel.style.color = '#fff';
    canvasLabel.style.textAlign = 'center';
    canvasLabel.style.marginBottom = '5px';

    // Assemble the components
    cameraContainer.appendChild(cameraLabel);
    cameraContainer.appendChild(videoElement);
    
    canvasContainer.appendChild(canvasLabel);
    canvasContainer.appendChild(canvasElement);
    
    gestureWrapper.appendChild(cameraContainer);
    gestureWrapper.appendChild(canvasContainer);
    document.body.appendChild(gestureWrapper);

    // Debug popup div
    const debugPopup = document.createElement('div');
    debugPopup.id = 'debug-popup';
    debugPopup.style.position = 'fixed';
    debugPopup.style.bottom = '20px';
    debugPopup.style.right = '20px';
    debugPopup.style.background = 'rgba(0, 0, 0, 0.8)';
    debugPopup.style.color = '#fff';
    debugPopup.style.padding = '10px';
    debugPopup.style.borderRadius = '5px';
    debugPopup.style.zIndex = '1001';
    debugPopup.style.display = 'none';
    document.body.appendChild(debugPopup);

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

// Debug function
function showDebug(message) {
    const debugPopup = document.getElementById('debug-popup');
    debugPopup.textContent = message;
    debugPopup.style.display = 'block';
    setTimeout(() => {
        debugPopup.style.display = 'none';
    }, 3000);
}

// Update the onResults function to use debug popup
function onResults(results) {
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);

    if (results.rightHandLandmarks) {
        const landmarks = results.rightHandLandmarks;
        const wrist = landmarks[0];

        // Draw hand landmarks
        drawConnectors(canvasCtx, results.rightHandLandmarks, HAND_CONNECTIONS,
            {color: '#00FF00', lineWidth: 2});

        // Check for waving motion
        if (previousWristX !== null) {
            const waveMovement = wrist.x - previousWristX;
            const currentTime = Date.now();
            
            // Determine wave direction
            if (Math.abs(waveMovement) > waveThreshold) {
                const currentDirection = waveMovement > 0 ? 'right' : 'left';
                
                // Detect direction change
                if (lastWaveDirection && currentDirection !== lastWaveDirection) {
                    if (currentTime - lastWaveTime > 100) {
                        waveCount++;
                        lastWaveTime = currentTime;
                        showDebug(`Wave ${waveCount} detected! Wave ${3-waveCount} more times to logout`);
                    }
                }
                lastWaveDirection = currentDirection;
            }

            // Draw wave progress
            drawWaveProgress(waveCount);
            
            // Check if enough waves detected
            if (waveCount >= 3) {
                showDebug('Wave gesture complete! Logging out...');
                handleLogoutGesture();
                waveCount = 0; // Reset count
            }
        }
        
        previousWristX = wrist.x;
        
    } else {
        // Reset detection if hand is lost
        previousWristX = null;
        lastWaveDirection = null;
        if (Date.now() - lastWaveTime > 1500) {
            if (waveCount > 0) {
                showDebug('Wave count reset');
            }
            waveCount = 0;
        }
    }
    
    canvasCtx.restore();
}

function drawWaveProgress(count) {
    const centerX = canvasElement.width / 2;
    const centerY = 30;
    
    // Draw background circles
    for (let i = 0; i < 3; i++) {
        canvasCtx.beginPath();
        canvasCtx.strokeStyle = i < count ? '#00FF00' : '#ffffff50';
        canvasCtx.lineWidth = 4;
        canvasCtx.arc(centerX + (i - 1) * 25, centerY, 8, 0, Math.PI * 2);
        canvasCtx.stroke();
    }
    
    // Add text
    canvasCtx.fillStyle = '#ffffff';
    canvasCtx.font = '14px Arial';
    canvasCtx.textAlign = 'center';
    canvasCtx.fillText(`Wave: ${count}/3`, centerX, centerY + 25);
}

// Update handleLogoutGesture to use debug popup
function handleLogoutGesture() {
    showDebug('Attempting logout...');
    
    // Force logout with a small delay
    setTimeout(() => {
        showDebug('Redirecting to logout URL...');
        console.log('Redirecting to /logout/');
        try {
            window.location.href = '/logout/';
        } catch (error) {
            console.error('Logout error:', error);
            showDebug('Error during logout: ' + error.message);
        }
    }, 1000);
}

// Add CSS
const style = document.createElement('style');
style.textContent = `
    .gesture-video, .gesture-canvas {
        width: 100%;
        height: 120px;
        border-radius: 4px;
    }
`;
document.head.appendChild(style); 