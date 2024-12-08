const videoElement = document.createElement('video');
const canvasElement = document.createElement('canvas');
const canvasCtx = canvasElement.getContext('2d');

let isRightWinkDetected = false;
let isLeftHandRaised = false;
const gestureTimeout = 1500; // 1.5 seconds to complete both gestures

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

    // Check for raised left hand
    if (results.poseLandmarks) {
        const leftWrist = results.poseLandmarks[15];
        const leftShoulder = results.poseLandmarks[11];
        
        if (leftWrist && leftShoulder && leftWrist.y < leftShoulder.y) {
            isLeftHandRaised = true;
            setTimeout(() => { isLeftHandRaised = false; }, gestureTimeout);
        }
    }

    // If both gestures are detected within the timeout period
    if (isRightWinkDetected && isLeftHandRaised) {
        handleLogoutGesture();
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
    isLeftHandRaised = false;

    // Show confirmation modal
    const modal = document.getElementById('logout-confirm-modal');
    modal.classList.remove('hidden');
    
    // Auto logout after 3 seconds if not canceled
    const logoutTimer = setTimeout(() => {
        window.location.href = logoutUrl;
    }, 3000);

    // Allow cancellation
    document.getElementById('cancel-logout').onclick = () => {
        clearTimeout(logoutTimer);
        modal.classList.add('hidden');
    };
} 