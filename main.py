# server.py - WebRTC Video Call Server
from aiohttp import web
import json
import uuid
from collections import defaultdict
# Store room information
rooms = defaultdict(lambda: {'participants': [], 'offers': {}, 'answers': {}, 'ice_candidates': defaultdict(list)})
MAX_PARTICIPANTS = 2
async def index(request):
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Video Call</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 1200px;
            width: 100%;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }
        .content {
            padding: 30px;
        }
        .lobby {
            text-align: center;
        }
        .input-group {
            margin: 20px 0;
        }
        .input-group label {
            display: block;
            margin-bottom: 10px;
            font-weight: 600;
            color: #333;
            font-size: 1.1em;
        }
        .input-group input {
            width: 100%;
            max-width: 400px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        .input-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .button-group {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
            margin: 20px 0;
        }
        button {
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }
        .btn-secondary:hover:not(:disabled) {
            background: #e0e0e0;
        }
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        .btn-danger:hover:not(:disabled) {
            background: #dc2626;
        }
        .room-info {
            background: #f9fafb;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .room-id-display {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin: 15px 0;
            flex-wrap: wrap;
        }
        .room-id-text {
            font-family: 'Courier New', monospace;
            font-size: 1.2em;
            font-weight: bold;
            color: #667eea;
            padding: 10px 20px;
            background: white;
            border-radius: 8px;
            border: 2px solid #667eea;
        }
        .video-container {
            display: none;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        .video-container.active {
            display: grid;
        }
        .video-wrapper {
            position: relative;
            background: #000;
            border-radius: 15px;
            overflow: hidden;
            aspect-ratio: 16/9;
        }
        video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .video-label {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 8px 15px;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 600;
        }
        .controls {
            display: none;
            justify-content: center;
            gap: 15px;
            margin: 20px 0;
        }
        .controls.active {
            display: flex;
        }
        .control-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            border: none;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 24px;
        }
        .control-btn.mic {
            background: #10b981;
            color: white;
        }
        .control-btn.mic.off {
            background: #ef4444;
        }
        .control-btn.video {
            background: #3b82f6;
            color: white;
        }
        .control-btn.video.off {
            background: #ef4444;
        }
        .control-btn.hangup {
            background: #ef4444;
            color: white;
        }
        .control-btn:hover {
            transform: scale(1.1);
        }
        .status {
            text-align: center;
            padding: 15px;
            margin: 20px 0;
            border-radius: 10px;
            font-weight: 600;
        }
        .status.info {
            background: #dbeafe;
            color: #1e40af;
        }
        .status.success {
            background: #d1fae5;
            color: #065f46;
        }
        .status.error {
            background: #fee2e2;
            color: #991b1b;
        }
        .status.warning {
            background: #fef3c7;
            color: #92400e;
        }
        .encryption-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #10b981;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin: 10px 0;
        }
        .participants-count {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #3b82f6;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin: 10px;
        }
        .permission-prompt {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }
        .permission-prompt h3 {
            color: #856404;
            margin-bottom: 10px;
        }
        .permission-prompt p {
            color: #856404;
            margin-bottom: 15px;
        }
        .permission-instructions {
            background: #e8f5e8;
            border: 1px solid #c3e6c3;
            border-radius: 8px;
            padding: 12px;
            margin: 10px 0;
            font-size: 0.95em;
            color: #155724;
        }
        .secure-context-note {
            background: #e7f3ff;
            border: 1px solid #b3d9ff;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            font-size: 0.95em;
            color: #0066cc;
        }
        .access-tip {
            background: #fff8e1;
            border: 1px solid #ffcc02;
            border-radius: 8px;
            padding: 12px;
            margin: 10px 0;
            font-size: 0.95em;
            color: #e65100;
        }
        @media (max-width: 768px) {
            .video-container {
                grid-template-columns: 1fr;
            }
            .button-group {
                flex-direction: column;
            }
            button {
                width: 100%;
                justify-content: center;
            }
        }
        .hidden {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Secure Video Call</h1>
            <p>End-to-End Encrypted Video Streaming</p>
        </div>
        <div class="content">
            <div id="lobby" class="lobby">
                <div id="permissionSection" class="permission-prompt">
                    <h3>📹🔊 Grant Permissions First</h3>
                    <p>Before joining a room, please allow access to your <strong>camera and microphone</strong>. This ensures a secure and private video call using Google's STUN servers for connection.</p>
                    <div class="permission-instructions">
                        <strong>What to expect:</strong> When you click "Allow", your browser will show a popup asking for permission to use your camera and microphone. Please select "Allow while visiting the site" or "Allow this time" for <strong>both</strong> camera and microphone.
                    </div>
                    <div id="accessTip" class="access-tip hidden">
                        <strong>💡 Quick Fix for Local Access:</strong> If you're seeing errors, try accessing the app via <code>http://127.0.0.1:9080</code> or <code>http://localhost:9080</code> instead of <code>0.0.0.0</code> or your local IP. This enables camera/mic permissions without HTTPS.
                    </div>
                    <div id="secureContextNote" class="secure-context-note hidden">
                        <strong>🔒 Secure Context Required:</strong> For camera/microphone access, this page must be loaded over <strong>HTTPS</strong> or from <strong>localhost/127.0.0.1</strong>. If accessing remotely (e.g., via local IP), set up HTTPS or use a tunneling tool like ngrok.
                    </div>
                    <button class="btn-primary" id="grantPermissionsBtn" onclick="requestPermissions()">
                        🎥 Allow Camera & Microphone
                    </button>
                    <div id="permissionStatus" class="status hidden"></div>
                </div>
                <div class="input-group">
                    <label for="roomInput">Enter Room ID to Join or Create New Room</label>
                    <input type="text" id="roomInput" placeholder="Enter room ID or leave empty to create">
                </div>
                <div class="button-group">
                    <button class="btn-primary" id="createRoomBtn" onclick="createRoom()" disabled>
                        ➕ Create New Room
                    </button>
                    <button class="btn-primary" id="joinRoomBtn" onclick="joinRoom()" disabled>
                        🚪 Join Room
                    </button>
                </div>
                <div id="statusMessage" class="status hidden"></div>
            </div>
            <div id="callInterface" class="hidden">
                <div class="room-info">
                    <div class="encryption-badge">
                        🔐 End-to-End Encrypted
                    </div>
                    <span class="participants-count" id="participantsCount">
                        👥 Participants: 0/2
                    </span>
                    <div class="room-id-display">
                        <span>Room ID:</span>
                        <span class="room-id-text" id="displayRoomId"></span>
                        <button class="btn-secondary" onclick="copyRoomId()">
                            📋 Copy
                        </button>
                    </div>
                    <p style="margin-top: 10px; color: #666; font-size: 0.9em;">Share this Room ID with another person to start the call</p>
                </div>
                <div id="videoContainer" class="video-container">
                    <div class="video-wrapper">
                        <video id="localVideo" autoplay muted playsinline></video>
                        <div class="video-label">You</div>
                    </div>
                    <div class="video-wrapper">
                        <video id="remoteVideo" autoplay playsinline></video>
                        <div class="video-label">Remote User</div>
                    </div>
                </div>
                <div id="controls" class="controls">
                    <button class="control-btn mic" id="micBtn" onclick="toggleMic()">
                        🎤
                    </button>
                    <button class="control-btn video" id="videoBtn" onclick="toggleVideo()">
                        📹
                    </button>
                    <button class="control-btn hangup" onclick="hangup()">
                        📞
                    </button>
                </div>
                <div id="callStatus" class="status info">
                    Waiting for another participant...
                </div>
            </div>
        </div>
    </div>
    <script>
        let localStream;
        let peerConnection;
        let currentRoomId;
        let ws;
        let isInitiator = false;
        let permissionsGranted = false;
        const config = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                { urls: 'stun:stun2.l.google.com:19302' }
            ]
        };
        function showStatus(message, type) {
            type = type || 'info';
            const statusEl = document.getElementById('statusMessage');
            statusEl.textContent = message;
            statusEl.className = 'status ' + type;
            statusEl.classList.remove('hidden');
        }
        function showPermissionStatus(message, type) {
            type = type || 'info';
            const statusEl = document.getElementById('permissionStatus');
            statusEl.textContent = message;
            statusEl.className = 'status ' + type;
            statusEl.classList.remove('hidden');
        }
        function showCallStatus(message, type) {
            type = type || 'info';
            const statusEl = document.getElementById('callStatus');
            statusEl.textContent = message;
            statusEl.className = 'status ' + type;
        }
        function enableJoinButtons() {
            document.getElementById('createRoomBtn').disabled = false;
            document.getElementById('joinRoomBtn').disabled = false;
        }
        function checkSecureContext() {
            const hostname = location.hostname;
            const isSecure = location.protocol === 'https:' || hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1';
            if (!isSecure) {
                document.getElementById('secureContextNote').classList.remove('hidden');
                // Show access tip for common local issues
                if (location.protocol === 'http:' && (hostname.match(/^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)/) || hostname === '0.0.0.0')) {
                    document.getElementById('accessTip').classList.remove('hidden');
                }
                return false;
            }
            return true;
        }
        async function requestPermissions() {
            if (!checkSecureContext()) {
                showPermissionStatus('❌ Secure context required: Access via HTTPS, localhost, or 127.0.0.1 only. See the note below for details.', 'error');
                document.getElementById('grantPermissionsBtn').disabled = false;
                document.getElementById('grantPermissionsBtn').textContent = '🎥 Allow Camera & Microphone';
                return;
            }
            const grantBtn = document.getElementById('grantPermissionsBtn');
            grantBtn.disabled = true;
            grantBtn.textContent = 'Requesting permissions...';
            try {
                // Test getUserMedia availability first
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    throw new Error('getUserMedia is not supported. This usually means you need a secure context (HTTPS/localhost) or a modern browser (Chrome 2025+, Firefox 2025+).');
                }
                localStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 1280, height: 720 },
                    audio: true
                });
                // Temporarily attach to a hidden video element to test
                const tempVideo = document.createElement('video');
                tempVideo.style.display = 'none';
                tempVideo.srcObject = localStream;
                document.body.appendChild(tempVideo);
                tempVideo.onloadedmetadata = () => {
                    document.body.removeChild(tempVideo);
                    permissionsGranted = true;
                    showPermissionStatus('✅ Permissions granted for camera and microphone! You can now join a room.', 'success');
                    enableJoinButtons();
                    // Hide the permission section after success
                    setTimeout(() => {
                        document.getElementById('permissionSection').classList.add('hidden');
                    }, 2000);
                };
            } catch (err) {
                console.error('Permission error:', err);
                let errorMsg = '❌ Failed to access camera/microphone: ';
                if (err.name === 'NotAllowedError') {
                    errorMsg += 'Permission denied. Please allow access to BOTH camera and microphone in the browser popup, then try again.';
                } else if (err.name === 'NotFoundError') {
                    errorMsg += 'No camera or microphone found. Please connect a device.';
                } else if (err.name === 'NotReadableError') {
                    errorMsg += 'Camera or microphone is being used by another application. Please close other apps.';
                } else if (err.message.includes('getUserMedia')) {
                    errorMsg += 'Secure context or browser support issue. Try http://127.0.0.1:9080 in Chrome/Firefox.';
                } else {
                    errorMsg += err.message + '. Please check your browser settings.';
                }
                showPermissionStatus(errorMsg, 'error');
                grantBtn.disabled = false;
                grantBtn.textContent = '🎥 Allow Camera & Microphone';
            }
        }
        function generateRoomId() {
            return 'room-' + Math.random().toString(36).substr(2, 9);
        }
        function createRoom() {
            const roomId = generateRoomId();
            document.getElementById('roomInput').value = roomId;
            joinRoom();
        }
        async function joinRoom() {
            if (!permissionsGranted) {
                showStatus('Please grant camera and microphone permissions first by clicking the "Allow" button above!', 'warning');
                document.getElementById('permissionSection').classList.remove('hidden');
                document.getElementById('grantPermissionsBtn').scrollIntoView({ behavior: 'smooth' });
                return;
            }
            let roomId = document.getElementById('roomInput').value.trim();
            if (!roomId) {
                roomId = generateRoomId();
                document.getElementById('roomInput').value = roomId;
            }
            currentRoomId = roomId;
            try {
                // Re-attach stream since we already have it (no new permission prompt)
                document.getElementById('localVideo').srcObject = localStream;
                connectWebSocket();
                document.getElementById('lobby').classList.add('hidden');
                document.getElementById('callInterface').classList.remove('hidden');
                document.getElementById('displayRoomId').textContent = roomId;
                document.getElementById('videoContainer').classList.add('active');
                document.getElementById('controls').classList.add('active');
            } catch (err) {
                showStatus('Failed to start call: ' + err.message, 'error');
            }
        }
        function connectWebSocket() {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(wsProtocol + '//' + window.location.host + '/ws/' + currentRoomId);
            ws.onopen = function() {
                console.log('WebSocket connected to room:', currentRoomId);
                showCallStatus('Connected to room. Waiting for another participant...', 'info');
            };
            ws.onmessage = async function(event) {
                const data = JSON.parse(event.data);
                console.log('Received:', data.type);
                switch(data.type) {
                    case 'room_joined':
                        updateParticipants(data.participants);
                        if (data.participants === 2 && !peerConnection) {
                            isInitiator = data.isInitiator;
                            if (isInitiator) {
                                showCallStatus('Another participant joined. Establishing connection...', 'info');
                                setTimeout(function() { createOffer(); }, 1000);
                            } else {
                                showCallStatus('Waiting for call to connect...', 'info');
                            }
                        } else if (data.participants === 1) {
                            showCallStatus('Waiting for another participant to join...', 'info');
                        }
                        break;
                    case 'room_full':
                        showCallStatus('Room is full (max 2 participants)', 'error');
                        setTimeout(hangup, 3000);
                        break;
                    case 'participant_left':
                        updateParticipants(data.participants);
                        showCallStatus('Other participant left the call', 'warning');
                        if (peerConnection) {
                            peerConnection.close();
                            peerConnection = null;
                            document.getElementById('remoteVideo').srcObject = null;
                        }
                        break;
                    case 'offer':
                        await handleOffer(data.offer);
                        break;
                    case 'answer':
                        await handleAnswer(data.answer);
                        break;
                    case 'ice_candidate':
                        await handleIceCandidate(data.candidate);
                        break;
                }
            };
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                showCallStatus('Connection error', 'error');
            };
            ws.onclose = function() {
                console.log('WebSocket closed');
                showCallStatus('Disconnected from server', 'warning');
            };
        }
        function updateParticipants(count) {
            document.getElementById('participantsCount').textContent = '👥 Participants: ' + count + '/2';
        }
        async function createOffer() {
            if (!peerConnection) {
                createPeerConnection();
            }
            try {
                const offer = await peerConnection.createOffer();
                await peerConnection.setLocalDescription(offer);
                ws.send(JSON.stringify({
                    type: 'offer',
                    offer: offer
                }));
                console.log('Offer sent');
            } catch (err) {
                console.error('Error creating offer:', err);
                showCallStatus('Error establishing connection', 'error');
            }
        }
        async function handleOffer(offer) {
            if (!peerConnection) {
                createPeerConnection();
            }
            try {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                ws.send(JSON.stringify({
                    type: 'answer',
                    answer: answer
                }));
                console.log('Answer sent');
            } catch (err) {
                console.error('Error handling offer:', err);
                showCallStatus('Error establishing connection', 'error');
            }
        }
        async function handleAnswer(answer) {
            try {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
                console.log('Answer received and set');
            } catch (err) {
                console.error('Error handling answer:', err);
            }
        }
        async function handleIceCandidate(candidate) {
            try {
                if (peerConnection && candidate) {
                    await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
                    console.log('ICE candidate added');
                }
            } catch (err) {
                console.error('Error handling ICE candidate:', err);
            }
        }
        function createPeerConnection() {
            peerConnection = new RTCPeerConnection(config);
            localStream.getTracks().forEach(function(track) {
                peerConnection.addTrack(track, localStream);
            });
            peerConnection.ontrack = function(event) {
                console.log('Received remote track');
                document.getElementById('remoteVideo').srcObject = event.streams[0];
                showCallStatus('✅ Call connected successfully!', 'success');
            };
            peerConnection.onicecandidate = function(event) {
                if (event.candidate) {
                    ws.send(JSON.stringify({
                        type: 'ice_candidate',
                        candidate: event.candidate
                    }));
                }
            };
            peerConnection.onconnectionstatechange = function() {
                console.log('Connection state:', peerConnection.connectionState);
                switch(peerConnection.connectionState) {
                    case 'connected':
                        showCallStatus('✅ Call connected!', 'success');
                        break;
                    case 'disconnected':
                        showCallStatus('Connection lost', 'warning');
                        break;
                    case 'failed':
                        showCallStatus('Connection failed. Please try again.', 'error');
                        break;
                    case 'connecting':
                        showCallStatus('Connecting...', 'info');
                        break;
                }
            };
            peerConnection.oniceconnectionstatechange = function() {
                console.log('ICE connection state:', peerConnection.iceConnectionState);
            };
        }
        function toggleMic() {
            const audioTrack = localStream.getAudioTracks()[0];
            if (audioTrack) {
                audioTrack.enabled = !audioTrack.enabled;
                const btn = document.getElementById('micBtn');
                btn.classList.toggle('off');
                btn.textContent = audioTrack.enabled ? '🎤' : '🔇';
            }
        }
        function toggleVideo() {
            const videoTrack = localStream.getVideoTracks()[0];
            if (videoTrack) {
                videoTrack.enabled = !videoTrack.enabled;
                const btn = document.getElementById('videoBtn');
                btn.classList.toggle('off');
                btn.textContent = videoTrack.enabled ? '📹' : '📹❌';
            }
        }
        function copyRoomId() {
            navigator.clipboard.writeText(currentRoomId).then(function() {
                showCallStatus('✅ Room ID copied! Share it with another person to join.', 'success');
                setTimeout(function() {
                    const count = document.getElementById('participantsCount').textContent;
                    if (count.includes('1/2')) {
                        showCallStatus('Waiting for another participant...', 'info');
                    }
                }, 2000);
            });
        }
        function hangup() {
            if (localStream) {
                localStream.getTracks().forEach(function(track) {
                    track.stop();
                });
                localStream = null;
            }
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }
            if (ws) {
                ws.close();
                ws = null;
            }
            permissionsGranted = false;
            document.getElementById('lobby').classList.remove('hidden');
            document.getElementById('callInterface').classList.add('hidden');
            document.getElementById('videoContainer').classList.remove('active');
            document.getElementById('controls').classList.remove('active');
            document.getElementById('statusMessage').classList.add('hidden');
            document.getElementById('permissionSection').classList.remove('hidden');
            document.getElementById('createRoomBtn').disabled = true;
            document.getElementById('joinRoomBtn').disabled = true;
            document.getElementById('grantPermissionsBtn').disabled = false;
            document.getElementById('grantPermissionsBtn').textContent = '🎥 Allow Camera & Microphone';
            document.getElementById('permissionStatus').classList.add('hidden');
            document.getElementById('secureContextNote').classList.add('hidden');
            document.getElementById('accessTip').classList.add('hidden');
            document.getElementById('roomInput').value = '';
            document.getElementById('remoteVideo').srcObject = null;
            currentRoomId = null;
        }
        // Show permission prompt on load
        window.onload = function() {
            document.getElementById('permissionSection').classList.remove('hidden');
            if (!checkSecureContext()) {
                showPermissionStatus('⚠️ Warning: This page requires a secure context (HTTPS or localhost/127.0.0.1) for camera/microphone access. See notes below.', 'warning');
            }
        };
    </script>
</body>
</html>
    """
    return web.Response(text=html, content_type='text/html')
async def websocket_handler(request):
    room_id = request.match_info['room_id']
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    room = rooms[room_id]
    if len(room['participants']) >= MAX_PARTICIPANTS:
        await ws.send_json({'type': 'room_full'})
        await ws.close()
        return ws
    client_id = str(uuid.uuid4())
    room['participants'].append({'id': client_id, 'ws': ws})
    is_initiator = len(room['participants']) == 2
    print(f"Client joined room {room_id}. Total participants: {len(room['participants'])}")
    await ws.send_json({
        'type': 'room_joined',
        'participants': len(room['participants']),
        'isInitiator': is_initiator
    })
    for participant in room['participants']:
        if participant['id'] != client_id:
            try:
                await participant['ws'].send_json({
                    'type': 'room_joined',
                    'participants': len(room['participants']),
                    'isInitiator': False
                })
            except Exception as e:
                print(f"Error notifying participant: {e}")
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                for participant in room['participants']:
                    if participant['id'] != client_id:
                        try:
                            await participant['ws'].send_json(data)
                        except Exception as e:
                            print(f"Error forwarding message: {e}")
            elif msg.type == web.WSMsgType.ERROR:
                print(f'WebSocket error: {ws.exception()}')
    finally:
        room['participants'] = [p for p in room['participants'] if p['id'] != client_id]
        print(f"Client left room {room_id}. Remaining participants: {len(room['participants'])}")
        for participant in room['participants']:
            try:
                await participant['ws'].send_json({
                    'type': 'participant_left',
                    'participants': len(room['participants'])
                })
            except Exception as e:
                print(f"Error notifying participant: {e}")
        if len(room['participants']) == 0:
            del rooms[room_id]
            print(f"Room {room_id} deleted")
    return ws
app = web.Application()
app.router.add_get('/meeting', index)
app.router.add_get('/ws/{room_id}', websocket_handler)
if __name__ == '__main__':
    print('Server starting on http://127.0.0.1:9080 (recommended for local testing)')
    print('💡 For camera/mic access, use http://127.0.0.1:9080 or http://localhost:9080 in your browser.')
    print('   Avoid 0.0.0.0 or local IPs over HTTP—use ngrok for HTTPS tunneling if needed.')
    web.run_app(app, host='0.0.0.0', port=9080)













# # server.py - WebRTC Video Call Server with End-to-End Encryption
# from aiohttp import web
# import asyncio
# import json
# import uuid
# from collections import defaultdict

# # Store room information
# rooms = defaultdict(lambda: {'participants': [], 'offers': {}, 'answers': {}, 'ice_candidates': defaultdict(list)})
# MAX_PARTICIPANTS = 2

# async def index(request):
#     html = '''
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Secure Video Call</title>
#     <style>
#         * {
#             margin: 0;
#             padding: 0;
#             box-sizing: border-box;
#         }

#         body {
#             font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             min-height: 100vh;
#             display: flex;
#             justify-content: center;
#             align-items: center;
#             padding: 20px;
#         }

#         .container {
#             background: white;
#             border-radius: 20px;
#             box-shadow: 0 20px 60px rgba(0,0,0,0.3);
#             max-width: 1200px;
#             width: 100%;
#             overflow: hidden;
#         }

#         .header {
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             color: white;
#             padding: 30px;
#             text-align: center;
#         }

#         .header h1 {
#             font-size: 2em;
#             margin-bottom: 10px;
#         }

#         .header p {
#             opacity: 0.9;
#             font-size: 1.1em;
#         }

#         .content {
#             padding: 30px;
#         }

#         .lobby {
#             text-align: center;
#         }

#         .input-group {
#             margin: 20px 0;
#         }

#         .input-group label {
#             display: block;
#             margin-bottom: 10px;
#             font-weight: 600;
#             color: #333;
#             font-size: 1.1em;
#         }

#         .input-group input {
#             width: 100%;
#             max-width: 400px;
#             padding: 15px;
#             border: 2px solid #e0e0e0;
#             border-radius: 10px;
#             font-size: 1em;
#             transition: border-color 0.3s;
#         }

#         .input-group input:focus {
#             outline: none;
#             border-color: #667eea;
#         }

#         .button-group {
#             display: flex;
#             gap: 15px;
#             justify-content: center;
#             flex-wrap: wrap;
#             margin: 20px 0;
#         }

#         button {
#             padding: 15px 30px;
#             border: none;
#             border-radius: 10px;
#             font-size: 1em;
#             font-weight: 600;
#             cursor: pointer;
#             transition: all 0.3s;
#             display: flex;
#             align-items: center;
#             gap: 8px;
#         }

#         .btn-primary {
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             color: white;
#         }

#         .btn-primary:hover {
#             transform: translateY(-2px);
#             box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
#         }

#         .btn-secondary {
#             background: #f0f0f0;
#             color: #333;
#         }

#         .btn-secondary:hover {
#             background: #e0e0e0;
#         }

#         .btn-danger {
#             background: #ef4444;
#             color: white;
#         }

#         .btn-danger:hover {
#             background: #dc2626;
#         }

#         .room-info {
#             background: #f9fafb;
#             padding: 20px;
#             border-radius: 10px;
#             margin: 20px 0;
#         }

#         .room-id-display {
#             display: flex;
#             align-items: center;
#             justify-content: center;
#             gap: 10px;
#             margin: 15px 0;
#         }

#         .room-id-text {
#             font-family: 'Courier New', monospace;
#             font-size: 1.2em;
#             font-weight: bold;
#             color: #667eea;
#             padding: 10px 20px;
#             background: white;
#             border-radius: 8px;
#             border: 2px solid #667eea;
#         }

#         .video-container {
#             display: none;
#             grid-template-columns: 1fr 1fr;
#             gap: 20px;
#             margin: 20px 0;
#         }

#         .video-container.active {
#             display: grid;
#         }

#         .video-wrapper {
#             position: relative;
#             background: #000;
#             border-radius: 15px;
#             overflow: hidden;
#             aspect-ratio: 16/9;
#         }

#         video {
#             width: 100%;
#             height: 100%;
#             object-fit: cover;
#         }

#         .video-label {
#             position: absolute;
#             top: 10px;
#             left: 10px;
#             background: rgba(0,0,0,0.7);
#             color: white;
#             padding: 8px 15px;
#             border-radius: 8px;
#             font-size: 0.9em;
#             font-weight: 600;
#         }

#         .controls {
#             display: none;
#             justify-content: center;
#             gap: 15px;
#             margin: 20px 0;
#         }

#         .controls.active {
#             display: flex;
#         }

#         .control-btn {
#             width: 60px;
#             height: 60px;
#             border-radius: 50%;
#             display: flex;
#             align-items: center;
#             justify-content: center;
#             border: none;
#             cursor: pointer;
#             transition: all 0.3s;
#         }

#         .control-btn.mic {
#             background: #10b981;
#             color: white;
#         }

#         .control-btn.mic.off {
#             background: #ef4444;
#         }

#         .control-btn.video {
#             background: #3b82f6;
#             color: white;
#         }

#         .control-btn.video.off {
#             background: #ef4444;
#         }

#         .control-btn.hangup {
#             background: #ef4444;
#             color: white;
#         }

#         .control-btn:hover {
#             transform: scale(1.1);
#         }

#         .status {
#             text-align: center;
#             padding: 15px;
#             margin: 20px 0;
#             border-radius: 10px;
#             font-weight: 600;
#         }

#         .status.info {
#             background: #dbeafe;
#             color: #1e40af;
#         }

#         .status.success {
#             background: #d1fae5;
#             color: #065f46;
#         }

#         .status.error {
#             background: #fee2e2;
#             color: #991b1b;
#         }

#         .status.warning {
#             background: #fef3c7;
#             color: #92400e;
#         }

#         .encryption-badge {
#             display: inline-flex;
#             align-items: center;
#             gap: 8px;
#             background: #10b981;
#             color: white;
#             padding: 8px 16px;
#             border-radius: 20px;
#             font-size: 0.9em;
#             font-weight: 600;
#             margin: 10px 0;
#         }

#         .participants-count {
#             display: inline-flex;
#             align-items: center;
#             gap: 8px;
#             background: #3b82f6;
#             color: white;
#             padding: 8px 16px;
#             border-radius: 20px;
#             font-size: 0.9em;
#             font-weight: 600;
#             margin: 10px;
#         }

#         @media (max-width: 768px) {
#             .video-container {
#                 grid-template-columns: 1fr;
#             }

#             .button-group {
#                 flex-direction: column;
#             }

#             button {
#                 width: 100%;
#                 justify-content: center;
#             }
#         }

#         .hidden {
#             display: none !important;
#         }
#     </style>
# </head>
# <body>
#     <div class="container">
#         <div class="header">
#             <h1>🔒 Secure Video Call</h1>
#             <p>End-to-End Encrypted Video Streaming</p>
#         </div>

#         <div class="content">
#             <div id="lobby" class="lobby">
#                 <div class="input-group">
#                     <label for="roomInput">Enter Room ID or Create New Room</label>
#                     <input type="text" id="roomInput" placeholder="room-xxxxx">
#                 </div>

#                 <div class="button-group">
#                     <button class="btn-primary" onclick="createRoom()">
#                         ➕ Create New Room
#                     </button>
#                     <button class="btn-primary" onclick="joinRoom()">
#                         🚪 Join Room
#                     </button>
#                 </div>

#                 <div id="statusMessage" class="status hidden"></div>
#             </div>

#             <div id="callInterface" class="hidden">
#                 <div class="room-info">
#                     <div class="encryption-badge">
#                         🔐 End-to-End Encrypted
#                     </div>
#                     <span class="participants-count" id="participantsCount">
#                         👥 Participants: 0/2
#                     </span>
                    
#                     <div class="room-id-display">
#                         <span>Room ID:</span>
#                         <span class="room-id-text" id="displayRoomId"></span>
#                         <button class="btn-secondary" onclick="copyRoomId()">
#                             📋 Copy
#                         </button>
#                     </div>
#                 </div>

#                 <div id="videoContainer" class="video-container">
#                     <div class="video-wrapper">
#                         <video id="localVideo" autoplay muted playsinline></video>
#                         <div class="video-label">You</div>
#                     </div>
#                     <div class="video-wrapper">
#                         <video id="remoteVideo" autoplay playsinline></video>
#                         <div class="video-label">Remote</div>
#                     </div>
#                 </div>

#                 <div id="controls" class="controls">
#                     <button class="control-btn mic" id="micBtn" onclick="toggleMic()">
#                         🎤
#                     </button>
#                     <button class="control-btn video" id="videoBtn" onclick="toggleVideo()">
#                         📹
#                     </button>
#                     <button class="control-btn hangup" onclick="hangup()">
#                         📞
#                     </button>
#                 </div>

#                 <div id="callStatus" class="status info">
#                     Waiting for connection...
#                 </div>
#             </div>
#         </div>
#     </div>

#     <script>
#         let localStream;
#         let peerConnection;
#         let currentRoomId;
#         let ws;
#         let isInitiator = false;

#         const config = {
#             iceServers: [
#                 { urls: 'stun:stun.l.google.com:19302' },
#                 { urls: 'stun:stun1.l.google.com:19302' }
#             ]
#         };

#         function showStatus(message, type = 'info') {
#             const statusEl = document.getElementById('statusMessage');
#             statusEl.textContent = message;
#             statusEl.className = `status ${type}`;
#             statusEl.classList.remove('hidden');
#         }

#         function showCallStatus(message, type = 'info') {
#             const statusEl = document.getElementById('callStatus');
#             statusEl.textContent = message;
#             statusEl.className = `status ${type}`;
#         }

#         function createRoom() {
#             const roomId = 'room-' + Math.random().toString(36).substr(2, 9);
#             document.getElementById('roomInput').value = roomId;
#             joinRoom();
#         }

#         async function joinRoom() {
#             const roomId = document.getElementById('roomInput').value.trim();
#             if (!roomId) {
#                 showStatus('Please enter a room ID', 'error');
#                 return;
#             }

#             currentRoomId = roomId;
            
#             try {
#                 localStream = await navigator.mediaDevices.getUserMedia({
#                     video: { width: 1280, height: 720 },
#                     audio: true
#                 });

#                 document.getElementById('localVideo').srcObject = localStream;
                
#                 connectWebSocket();
                
#                 document.getElementById('lobby').classList.add('hidden');
#                 document.getElementById('callInterface').classList.remove('hidden');
#                 document.getElementById('displayRoomId').textContent = roomId;
#                 document.getElementById('videoContainer').classList.add('active');
#                 document.getElementById('controls').classList.add('active');
                
#             } catch (err) {
#                 showStatus('Failed to access camera/microphone: ' + err.message, 'error');
#             }
#         }

#         function connectWebSocket() {
#             ws = new WebSocket(`ws://${window.location.host}/ws/${currentRoomId}`);
            
#             ws.onopen = () => {
#                 console.log('WebSocket connected');
#                 showCallStatus('Connected to room', 'success');
#             };

#             ws.onmessage = async (event) => {
#                 const data = JSON.parse(event.data);
#                 console.log('Received:', data.type);

#                 switch(data.type) {
#                     case 'room_joined':
#                         updateParticipants(data.participants);
#                         if (data.participants === 2 && !peerConnection) {
#                             isInitiator = data.isInitiator;
#                             if (isInitiator) {
#                                 await createOffer();
#                             }
#                         }
#                         break;
                    
#                     case 'room_full':
#                         showCallStatus('Room is full (max 2 participants)', 'error');
#                         setTimeout(hangup, 2000);
#                         break;

#                     case 'participant_left':
#                         updateParticipants(data.participants);
#                         showCallStatus('Participant left', 'warning');
#                         if (peerConnection) {
#                             peerConnection.close();
#                             peerConnection = null;
#                             document.getElementById('remoteVideo').srcObject = null;
#                         }
#                         break;

#                     case 'offer':
#                         await handleOffer(data.offer);
#                         break;

#                     case 'answer':
#                         await handleAnswer(data.answer);
#                         break;

#                     case 'ice_candidate':
#                         await handleIceCandidate(data.candidate);
#                         break;
#                 }
#             };

#             ws.onerror = (error) => {
#                 console.error('WebSocket error:', error);
#                 showCallStatus('Connection error', 'error');
#             };

#             ws.onclose = () => {
#                 console.log('WebSocket closed');
#                 showCallStatus('Disconnected', 'warning');
#             };
#         }

#         function updateParticipants(count) {
#             document.getElementById('participantsCount').textContent = `👥 Participants: ${count}/2`;
#         }

#         async function createOffer() {
#             if (!peerConnection) {
#                 createPeerConnection();
#             }

#             try {
#                 const offer = await peerConnection.createOffer();
#                 await peerConnection.setLocalDescription(offer);
                
#                 ws.send(JSON.stringify({
#                     type: 'offer',
#                     offer: offer
#                 }));
                
#                 showCallStatus('Calling...', 'info');
#             } catch (err) {
#                 console.error('Error creating offer:', err);
#             }
#         }

#         async function handleOffer(offer) {
#             if (!peerConnection) {
#                 createPeerConnection();
#             }

#             try {
#                 await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
#                 const answer = await peerConnection.createAnswer();
#                 await peerConnection.setLocalDescription(answer);
                
#                 ws.send(JSON.stringify({
#                     type: 'answer',
#                     answer: answer
#                 }));
                
#                 showCallStatus('Connected', 'success');
#             } catch (err) {
#                 console.error('Error handling offer:', err);
#             }
#         }

#         async function handleAnswer(answer) {
#             try {
#                 await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
#                 showCallStatus('Connected', 'success');
#             } catch (err) {
#                 console.error('Error handling answer:', err);
#             }
#         }

#         async function handleIceCandidate(candidate) {
#             try {
#                 if (peerConnection && candidate) {
#                     await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
#                 }
#             } catch (err) {
#                 console.error('Error handling ICE candidate:', err);
#             }
#         }

#         function createPeerConnection() {
#             peerConnection = new RTCPeerConnection(config);

#             localStream.getTracks().forEach(track => {
#                 peerConnection.addTrack(track, localStream);
#             });

#             peerConnection.ontrack = (event) => {
#                 console.log('Received remote track');
#                 document.getElementById('remoteVideo').srcObject = event.streams[0];
#                 showCallStatus('Call connected', 'success');
#             };

#             peerConnection.onicecandidate = (event) => {
#                 if (event.candidate) {
#                     ws.send(JSON.stringify({
#                         type: 'ice_candidate',
#                         candidate: event.candidate
#                     }));
#                 }
#             };

#             peerConnection.onconnectionstatechange = () => {
#                 console.log('Connection state:', peerConnection.connectionState);
#                 if (peerConnection.connectionState === 'failed') {
#                     showCallStatus('Connection failed', 'error');
#                 }
#             };
#         }

#         function toggleMic() {
#             const audioTrack = localStream.getAudioTracks()[0];
#             if (audioTrack) {
#                 audioTrack.enabled = !audioTrack.enabled;
#                 const btn = document.getElementById('micBtn');
#                 btn.classList.toggle('off');
#                 btn.textContent = audioTrack.enabled ? '🎤' : '🔇';
#             }
#         }

#         function toggleVideo() {
#             const videoTrack = localStream.getVideoTracks()[0];
#             if (videoTrack) {
#                 videoTrack.enabled = !videoTrack.enabled;
#                 const btn = document.getElementById('videoBtn');
#                 btn.classList.toggle('off');
#                 btn.textContent = videoTrack.enabled ? '📹' : '📹❌';
#             }
#         }

#         function copyRoomId() {
#             navigator.clipboard.writeText(currentRoomId);
#             showCallStatus('Room ID copied to clipboard', 'success');
#         }

#         function hangup() {
#             if (localStream) {
#                 localStream.getTracks().forEach(track => track.stop());
#             }
            
#             if (peerConnection) {
#                 peerConnection.close();
#             }
            
#             if (ws) {
#                 ws.close();
#             }

#             document.getElementById('lobby').classList.remove('hidden');
#             document.getElementById('callInterface').classList.add('hidden');
#             document.getElementById('videoContainer').classList.remove('active');
#             document.getElementById('controls').classList.remove('active');
            
#             document.getElementById('roomInput').value = '';
#             localStream = null;
#             peerConnection = null;
#             currentRoomId = null;
#         }
#     </script>
# </body>
# </html>
#     '''
#     return web.Response(text=html, content_type='text/html')

# async def websocket_handler(request):
#     room_id = request.match_info['room_id']
#     ws = web.WebSocketResponse()
#     await ws.prepare(request)

#     room = rooms[room_id]
    
#     # Check if room is full
#     if len(room['participants']) >= MAX_PARTICIPANTS:
#         await ws.send_json({'type': 'room_full'})
#         await ws.close()
#         return ws

#     # Add participant
#     client_id = str(uuid.uuid4())
#     room['participants'].append({'id': client_id, 'ws': ws})
    
#     is_initiator = len(room['participants']) == 1
    
#     # Notify client they joined
#     await ws.send_json({
#         'type': 'room_joined',
#         'participants': len(room['participants']),
#         'isInitiator': is_initiator
#     })

#     # Notify all participants
#     for participant in room['participants']:
#         if participant['id'] != client_id:
#             try:
#                 await participant['ws'].send_json({
#                     'type': 'room_joined',
#                     'participants': len(room['participants']),
#                     'isInitiator': False
#                 })
#             except:
#                 pass

#     try:
#         async for msg in ws:
#             if msg.type == web.WSMsgType.TEXT:
#                 data = json.loads(msg.data)
                
#                 # Forward signaling messages to other participant
#                 for participant in room['participants']:
#                     if participant['id'] != client_id:
#                         try:
#                             await participant['ws'].send_json(data)
#                         except:
#                             pass
                            
#             elif msg.type == web.WSMsgType.ERROR:
#                 print(f'WebSocket error: {ws.exception()}')
#     finally:
#         # Remove participant
#         room['participants'] = [p for p in room['participants'] if p['id'] != client_id]
        
#         # Notify remaining participants
#         for participant in room['participants']:
#             try:
#                 await participant['ws'].send_json({
#                     'type': 'participant_left',
#                     'participants': len(room['participants'])
#                 })
#             except:
#                 pass
        
#         # Clean up empty rooms
#         if len(room['participants']) == 0:
#             del rooms[room_id]

#     return ws

# app = web.Application()
# app.router.add_get('/', index)
# app.router.add_get('/ws/{room_id}', websocket_handler)

# if __name__ == '__main__':
#     print('🚀 Server starting on http://localhost:8080')
#     print('📹 Open browser and create/join rooms with unique IDs')
#     print('🔒 End-to-End encrypted WebRTC connections')
#     print('👥 Maximum 2 participants per room')
#     web.run_app(app, host='0.0.0.0', port=9080)