// Will be pushed to 449

const videoElement = document.createElement('video');
const canvasElement = document.createElement('canvas');
const canvasCtx = canvasElement.getContext('2d');

function setupFaceCaptcha() {
    // Style the video element
    videoElement.setAttribute('class', 'input_video');
    videoElement.style.width = '320px';
    videoElement.style.height = '240px';
    videoElement.style.marginBottom = '10px';
    // Add transform to mirror the video element
    videoElement.style.transform = 'scaleX(-1)';
    
    // Style the canvas element
    canvasElement.setAttribute('class', 'output_canvas');
    canvasElement.style.width = '320px';
    canvasElement.style.height = '240px';
    canvasElement.style.marginBottom = '20px';
    canvasElement.width = 320;
    canvasElement.height = 240;
    // Add transform to mirror the canvas element
    canvasElement.style.transform = 'scaleX(-1)';
    
    // Create a container div for better organization
    const mediaContainer = document.createElement('div');
    mediaContainer.style.position = 'relative';
    mediaContainer.style.marginBottom = '20px';
    
    // Add elements to the captcha container
    const captchaContainer = document.getElementById('face-captcha-container');
    mediaContainer.appendChild(videoElement);
    mediaContainer.appendChild(canvasElement);
    captchaContainer.appendChild(mediaContainer);

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
        height: 240,
        mirrored: true
    });

    camera.start();

    // Update the instruction text
    const instructionText = captchaContainer.querySelector('p');
    instructionText.textContent = 'Smile to verify you\'re human';
}

function onResults(results) {
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    canvasCtx.scale(-1, 1);
    canvasCtx.translate(-canvasElement.width, 0);
    
    if (results.multiFaceLandmarks) {
        for (const landmarks of results.multiFaceLandmarks) {
            // Mouth landmarks
            const upperLipCenter = landmarks[13];
            const lowerLipCenter = landmarks[14];
            const leftMouthCorner = landmarks[61];
            const rightMouthCorner = landmarks[291];
            
            // Calculate mouth measurements
            const mouthVerticalOpening = Math.abs(upperLipCenter.y - lowerLipCenter.y);
            const mouthWidth = Math.abs(leftMouthCorner.x - rightMouthCorner.x);
            const mouthCornerHeight = (leftMouthCorner.y + rightMouthCorner.y) / 2;
            
            // Calculate smile ratio
            const smileRatio = mouthWidth / mouthVerticalOpening;
            const cornerLift = upperLipCenter.y - mouthCornerHeight;
            
            // Detect smile with more lenient thresholds
            if (smileRatio > 3.3 && // Reduced from 4.0 to 3.0
                cornerLift > 0.015) { // Reduced from 0.02 to 0.01
                handleSmileDetected();
            }
            
            // Draw face mesh
            drawConnectors(canvasCtx, landmarks, FACEMESH_TESSELATION,
                {color: '#C0C0C070', lineWidth: 1});
        }
    }
    canvasCtx.restore();
}

function handleSmileDetected() {
    // Mark reCAPTCHA as solved
    document.getElementById('captcha-solved').value = 'true';
    
    // Show success message
    const messageElement = document.getElementById('captcha-message');
    messageElement.textContent = 'Smile detected! CAPTCHA solved.';
    messageElement.classList.remove('text-red-500');
    messageElement.classList.add('text-green-500');
} 