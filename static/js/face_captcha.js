const videoElement = document.createElement('video');
const canvasElement = document.createElement('canvas');
const canvasCtx = canvasElement.getContext('2d');

function setupFaceCaptcha() {
    // Style the video element
    videoElement.setAttribute('class', 'input_video');
    canvasElement.setAttribute('class', 'output_canvas');
    
    // Add elements to the captcha container
    const captchaContainer = document.getElementById('face-captcha-container');
    captchaContainer.appendChild(videoElement);
    captchaContainer.appendChild(canvasElement);

    const faceMesh = new FaceMesh({
        locateFile: (file) => {
            return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
        }
    });

    faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });

    faceMesh.onResults(onResults);

    const camera = new Camera(videoElement, {
        onFrame: async () => {
            await faceMesh.send({image: videoElement});
        },
        width: 320,
        height: 240
    });

    camera.start();
}

function onResults(results) {
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    if (results.multiFaceLandmarks) {
        for (const landmarks of results.multiFaceLandmarks) {
            // Check for left eye wink
            const leftEyeUpper = landmarks[159]; // Upper left eye landmark
            const leftEyeLower = landmarks[145]; // Lower left eye landmark
            
            const eyeDistance = Math.abs(leftEyeUpper.y - leftEyeLower.y);
            
            if (eyeDistance < 0.02) { // Threshold for wink detection
                handleWinkDetected();
            }
            
            // Draw face mesh
            drawConnectors(canvasCtx, landmarks, FACEMESH_TESSELATION,
                {color: '#C0C0C070', lineWidth: 1});
        }
    }
    canvasCtx.restore();
}

function handleWinkDetected() {
    // Mark reCAPTCHA as solved
    document.getElementById('captcha-solved').value = 'true';
    
    // Show success message
    const messageElement = document.getElementById('captcha-message');
    messageElement.textContent = 'Wink detected! CAPTCHA solved.';
    messageElement.classList.remove('text-red-500');
    messageElement.classList.add('text-green-500');
} 