const videoElement = document.createElement('video');
const canvasElement = document.createElement('canvas');
const canvasCtx = canvasElement.getContext('2d');

let isRightWinkDetected = false;
let palmHoldStartTime = 0;
const gestureTimeout = 1500; // 1.5 seconds to hold palm
const palmThreshold = 0.2; // Threshold for detecting open palm

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

    // Check for open palm and hold
    if (results.rightHandLandmarks) {
        const landmarks = results.rightHandLandmarks;
        
        // Calculate distances between fingertips and palm base
        const palmBase = landmarks[0];
        const thumbTip = landmarks[4];
        const indexTip = landmarks[8];
        const middleTip = landmarks[12];
        const ringTip = landmarks[16];
        const pinkyTip = landmarks[20];
        
        // Check if fingers are spread (open palm)
        const isOpenPalm = checkOpenPalm(palmBase, thumbTip, indexTip, middleTip, ringTip, pinkyTip);

        if (isOpenPalm) {
            if (palmHoldStartTime === 0) {
                palmHoldStartTime = Date.now();
            } else if (Date.now() - palmHoldStartTime >= gestureTimeout && isRightWinkDetected) {
                handleLogoutGesture();
                palmHoldStartTime = 0;
                isRightWinkDetected = false;
            }
        } else {
            palmHoldStartTime = 0;
        }

        // Visual feedback for palm detection
        if (palmHoldStartTime > 0) {
            const holdProgress = Math.min((Date.now() - palmHoldStartTime) / gestureTimeout, 1);
            drawPalmFeedback(holdProgress);
        }
    } else {
        palmHoldStartTime = 0;
    }

    // Draw landmarks for visual feedback
    drawConnectors(canvasCtx, results.faceLandmarks, FACEMESH_TESSELATION,
        {color: '#C0C0C070', lineWidth: 1});
    if (results.rightHandLandmarks) {
        drawConnectors(canvasCtx, results.rightHandLandmarks, HAND_CONNECTIONS,
            {color: '#00FF00', lineWidth: 2});
    }
    
    canvasCtx.restore();
}

function checkOpenPalm(palmBase, thumbTip, indexTip, middleTip, ringTip, pinkyTip) {
    // Calculate average finger spread
    const fingerTips = [thumbTip, indexTip, middleTip, ringTip, pinkyTip];
    let totalSpread = 0;
    
    for (let i = 0; i < fingerTips.length - 1; i++) {
        const spread = Math.sqrt(
            Math.pow(fingerTips[i].x - fingerTips[i + 1].x, 2) +
            Math.pow(fingerTips[i].y - fingerTips[i + 1].y, 2)
        );
        totalSpread += spread;
    }
    
    const avgSpread = totalSpread / 4;
    
    // Check if fingers are raised (y position lower than palm base)
    const fingersRaised = fingerTips.every(tip => tip.y < palmBase.y);
    
    return avgSpread > palmThreshold && fingersRaised;
}

function drawPalmFeedback(progress) {
    const centerX = canvasElement.width / 2;
    const centerY = canvasElement.height - 30;
    
    canvasCtx.beginPath();
    canvasCtx.strokeStyle = '#00FF00';
    canvasCtx.lineWidth = 3;
    canvasCtx.arc(centerX, centerY, 15, 0, Math.PI * 2 * progress);
    canvasCtx.stroke();
}

function handleLogoutGesture() {
    // Reset gesture flags
    isRightWinkDetected = false;
    palmHoldStartTime = 0;

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