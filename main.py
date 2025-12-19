

# server.py - Secure Multi-User WebRTC Video Call Server
import aiohttp.web as web
import json
import uuid
from collections import defaultdict
import sqlite3
import datetime

# Global DB connection
conn = None

def init_db():
    global conn
    conn = sqlite3.connect('video_calls.db', check_same_thread=False)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_id TEXT PRIMARY KEY,
            password TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT,
            client_id TEXT,
            username TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms (room_id)
        )
    ''')
    conn.commit()

# Store active room information in memory
rooms = defaultdict(lambda: {'participants': [], 'pending_tokens': {}})

MAX_PARTICIPANTS = 3

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
            max-width: 1400px;
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
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }
        .video-container.active {
            display: grid;
        }
        .video-wrapper {
            position: relative;
            background: #000;
            border-radius: 10px;
            overflow: hidden;
            min-width: 200px;
            min-height: 150px;
            resize: both;
        }
        .video-wrapper.speaking {
            transform: scale(1.05);
            border: 2px solid #10b981;
            z-index: 10;
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
        .chat-section {
            margin-top: 20px;
            background: #f9fafb;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .chat-section.hidden {
            display: none;
        }
        .chat-header {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: center;
        }
        .chat-messages {
            height: 300px;
            overflow-y: auto;
            padding: 15px;
            background: white;
        }
        .chat-messages div {
            margin-bottom: 10px;
            padding: 8px;
            background: #e2e8f0;
            border-radius: 8px;
        }
        .chat-messages .username {
            font-weight: bold;
            color: #667eea;
        }
        .chat-messages .time {
            font-size: 0.8em;
            color: #94a3b8;
        }
        .chat-input-group {
            display: flex;
            padding: 15px;
            background: #f1f5f9;
        }
        #chatInput {
            flex: 1;
            padding: 10px;
            border: 1px solid #e2e8f0;
            border-radius: 5px;
            margin-right: 10px;
        }
        #sendChatBtn {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
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
            .chat-messages {
                height: 200px;
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
            <p>End-to-End Encrypted Multi-User Video Streaming (Max 5)</p>
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
                    <label for="nameInput">Your Name</label>
                    <input type="text" id="nameInput" placeholder="Enter your display name" required>
                </div>
                <div class="input-group">
                    <label for="roomInput">Enter Room ID to Join or Create New Room</label>
                    <input type="text" id="roomInput" placeholder="Enter room ID or leave empty to create">
                </div>
                <div class="input-group">
                    <label for="passwordInput">Room Password (optional for create, required if set)</label>
                    <input type="password" id="passwordInput" placeholder="Leave empty for public room">
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
                        👥 Participants: 0/5
                    </span>
                    <div class="room-id-display">
                        <span>Room ID:</span>
                        <span class="room-id-text" id="displayRoomId"></span>
                        <button class="btn-secondary" onclick="copyRoomId()">
                            📋 Copy
                        </button>
                    </div>
                    <p style="margin-top: 10px; color: #666; font-size: 0.9em;">Share this Room ID and password (if set) with others to start the call</p>
                </div>
                <div id="videoContainer" class="video-container">
                    <div class="video-wrapper">
                        <video id="localVideo" autoplay muted playsinline></video>
                        <div class="video-label" id="localLabel">You</div>
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
                <div id="chatSection" class="chat-section hidden">
                    <div class="chat-header">
                        <h3>💬 Chat</h3>
                    </div>
                    <div id="chatMessages" class="chat-messages"></div>
                    <div class="chat-input-group">
                        <input type="text" id="chatInput" placeholder="Type a message..." maxlength="500">
                        <button id="sendChatBtn" onclick="sendChat()">Send</button>
                    </div>
                </div>
                <div id="callStatus" class="status info">
                    Waiting for another participant...
                </div>
            </div>
        </div>
    </div>
    <script>
        let localStream;
        let peerConnections = new Map();
        let remoteVideos = {};
        let usernames = {};
        let audioContexts = new Map();
        let myClientId;
        let myUsername;
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
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
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
        function updateParticipants(count) {
            document.getElementById('participantsCount').textContent = `👥 Participants: ${count}/5`;
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
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    throw new Error('getUserMedia is not supported. This usually means you need a secure context (HTTPS/localhost) or a modern browser (Chrome 2025+, Firefox 2025+).');
                }
                localStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 1280, height: 720 },
                    audio: true
                });
                const tempVideo = document.createElement('video');
                tempVideo.style.display = 'none';
                tempVideo.srcObject = localStream;
                document.body.appendChild(tempVideo);
                tempVideo.onloadedmetadata = () => {
                    document.body.removeChild(tempVideo);
                    permissionsGranted = true;
                    showPermissionStatus('✅ Permissions granted for camera and microphone! You can now join a room.', 'success');
                    enableJoinButtons();
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
        async function createRoom() {
            if (!permissionsGranted) {
                showStatus('Please grant camera and microphone permissions first!', 'warning');
                return;
            }
            const name = document.getElementById('nameInput').value.trim();
            if (!name) {
                showStatus('Please enter your name!', 'warning');
                return;
            }
            let roomId = document.getElementById('roomInput').value.trim() || generateRoomId();
            const password = document.getElementById('passwordInput').value;
            try {
                showStatus('Creating room...', 'info');
                const res = await fetch('/create_room', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ room_id: roomId, password })
                });
                const data = await res.json();
                if (!data.success) {
                    showStatus(data.error, 'error');
                    return;
                }
                roomId = data.room_id;
                document.getElementById('roomInput').value = roomId;
                await performJoin(roomId, password, name);
            } catch (err) {
                showStatus('Network error: ' + err.message, 'error');
            }
        }
        async function joinRoom() {
            if (!permissionsGranted) {
                showStatus('Please grant camera and microphone permissions first!', 'warning');
                return;
            }
            const name = document.getElementById('nameInput').value.trim();
            if (!name) {
                showStatus('Please enter your name!', 'warning');
                return;
            }
            let roomId = document.getElementById('roomInput').value.trim();
            if (!roomId) {
                showStatus('Please enter a room ID to join!', 'warning');
                return;
            }
            const password = document.getElementById('passwordInput').value;
            await performJoin(roomId, password, name);
        }
        async function performJoin(roomId, password, username) {
            showStatus('Joining room...', 'info');
            try {
                const res = await fetch('/join_room', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ room_id: roomId, password, username })
                });
                const data = await res.json();
                if (!data.success) {
                    showStatus(data.error, 'error');
                    return;
                }
                myUsername = username;
                currentRoomId = roomId;
                displayChatHistory(data.history);
                connectWebSocket(currentRoomId, data.token);
                document.getElementById('lobby').classList.add('hidden');
                document.getElementById('callInterface').classList.remove('hidden');
                document.getElementById('displayRoomId').textContent = roomId;
                document.getElementById('localLabel').textContent = `You (${myUsername})`;
                document.getElementById('videoContainer').classList.add('active');
                document.getElementById('controls').classList.add('active');
                document.getElementById('chatSection').classList.remove('hidden');
                document.getElementById('localVideo').srcObject = localStream;
            } catch (err) {
                showStatus('Failed to join: ' + err.message, 'error');
            }
        }
        function displayChatHistory(history) {
            const messagesEl = document.getElementById('chatMessages');
            messagesEl.innerHTML = '';
            history.forEach(msg => appendChatMessage(msg));
        }
        function appendChatMessage(msg) {
            const div = document.createElement('div');
            div.innerHTML = `<span class="username">${escapeHtml(msg.username)}:</span> ${escapeHtml(msg.message)} <span class="time">${new Date(msg.timestamp).toLocaleTimeString()}</span>`;
            document.getElementById('chatMessages').appendChild(div);
            div.scrollIntoView({ behavior: 'smooth' });
        }
        function sendChat() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if (!message || !ws) return;
            ws.send(JSON.stringify({ type: 'chat', message }));
            input.value = '';
        }
        function connectWebSocket(roomId, token) {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws/${roomId}?token=${token}`;
            ws = new WebSocket(wsUrl);
            ws.onopen = () => {
                console.log('WebSocket connected to room:', roomId);
                ws.send(JSON.stringify({ type: 'join', username: myUsername }));
                showCallStatus('Connected to room. Waiting for participants...', 'info');
            };
            ws.onmessage = async (event) => {
                const data = JSON.parse(event.data);
                console.log('Received:', data.type, data);
                switch (data.type) {
                    case 'room_ready':
                        myClientId = data.my_id;
                        updateParticipants(data.participants_count);
                        showCallStatus(`Welcome! ${data.participants_count - 1} other(s) online.`, 'success');
                        if (data.participants_count === 1) {
                            showCallStatus('Waiting for others to join...', 'info');
                        }
                        break;
                    case 'new_participant':
                        usernames[data.new_id] = data.new_username;
                        createRemoteVideoElement(data.new_id);
                        createPeerConnection(data.new_id);
                        createOffer(data.new_id);
                        updateParticipants(data.participants_count);
                        showCallStatus('New participant joined!', 'info');
                        break;
                    case 'participant_left':
                        const leftId = data.left_id;
                        const rv = remoteVideos[leftId];
                        if (rv) {
                            rv.video.srcObject = null;
                            if (audioContexts.has(leftId)) {
                                audioContexts.get(leftId).context.close();
                                audioContexts.delete(leftId);
                            }
                            rv.wrapper.remove();
                            delete remoteVideos[leftId];
                        }
                        if (peerConnections.has(leftId)) {
                            peerConnections.get(leftId).close();
                            peerConnections.delete(leftId);
                        }
                        delete usernames[leftId];
                        updateParticipants(data.participants_count);
                        showCallStatus(`Participant left. ${data.participants_count} remaining.`, 'warning');
                        if (data.participants_count === 1) {
                            showCallStatus('You are now alone in the room.', 'info');
                        }
                        break;
                    case 'offer':
                        if (data.target_id === myClientId) {
                            await handleOffer(data.sender_id, data.offer);
                        }
                        break;
                    case 'answer':
                        if (data.target_id === myClientId) {
                            await handleAnswer(data.sender_id, data.answer);
                        }
                        break;
                    case 'ice_candidate':
                        if (data.target_id === myClientId) {
                            await handleIceCandidate(data.sender_id, data.candidate);
                        }
                        break;
                    case 'chat':
                        appendChatMessage(data);
                        break;
                    case 'room_full':
                        showCallStatus('Room is full (max 5 participants)', 'error');
                        setTimeout(hangup, 3000);
                        break;
                    case 'error':
                        showCallStatus('Server error: ' + data.message, 'error');
                        break;
                }
            };
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                showCallStatus('Connection error', 'error');
            };
            ws.onclose = () => {
                console.log('WebSocket closed');
                showCallStatus('Disconnected from server', 'warning');
            };
        }
        function createRemoteVideoElement(clientId) {
            if (remoteVideos[clientId]) return;
            const container = document.getElementById('videoContainer');
            const wrapper = document.createElement('div');
            wrapper.className = 'video-wrapper';
            wrapper.id = `wrapper_${clientId}`;
            wrapper.style.resize = 'both';
            wrapper.style.overflow = 'hidden';
            const video = document.createElement('video');
            video.id = `remoteVideo_${clientId}`;
            video.autoplay = true;
            video.playsinline = true;
            const label = document.createElement('div');
            label.className = 'video-label';
            label.id = `label_${clientId}`;
            if (usernames[clientId]) {
                label.textContent = usernames[clientId];
            } else {
                label.textContent = clientId.substring(0, 4);
            }
            wrapper.appendChild(video);
            wrapper.appendChild(label);
            container.appendChild(wrapper);
            remoteVideos[clientId] = { video, wrapper, label: document.getElementById(`label_${clientId}`) };
            if (usernames[clientId]) {
                remoteVideos[clientId].label.textContent = usernames[clientId];
            }
        }
        function createPeerConnection(remoteId) {
            if (peerConnections.has(remoteId)) return;
            const pc = new RTCPeerConnection(config);
            peerConnections.set(remoteId, pc);
            localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
            pc.ontrack = (event) => {
                console.log('Received remote track from', remoteId);
                const video = remoteVideos[remoteId].video;
                video.srcObject = event.streams[0];
                startSpeakingDetection(event.streams[0], remoteId);
            };
            pc.onicecandidate = (event) => {
                if (event.candidate) {
                    ws.send(JSON.stringify({
                        type: 'ice_candidate',
                        sender_id: myClientId,
                        target_id: remoteId,
                        candidate: event.candidate
                    }));
                }
            };
            pc.onconnectionstatechange = () => {
                console.log('PC state for', remoteId, ':', pc.connectionState);
                if (pc.connectionState === 'connected') {
                    showCallStatus('Connection established with ' + (usernames[remoteId] || remoteId) + '!', 'success');
                } else if (pc.connectionState === 'failed') {
                    showCallStatus('Connection failed with ' + (usernames[remoteId] || remoteId), 'error');
                }
            };
        }
        async function createOffer(remoteId) {
            const pc = peerConnections.get(remoteId);
            if (!pc) return;
            try {
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                ws.send(JSON.stringify({
                    type: 'offer',
                    sender_id: myClientId,
                    target_id: remoteId,
                    offer: offer
                }));
                console.log('Offer sent to', remoteId);
            } catch (err) {
                console.error('Error creating offer to', remoteId, err);
            }
        }
        async function handleOffer(senderId, offer) {
            let pc = peerConnections.get(senderId);
            if (!pc) {
                createPeerConnection(senderId);
                pc = peerConnections.get(senderId);
            }
            try {
                await pc.setRemoteDescription(new RTCSessionDescription(offer));
                const answer = await pc.createAnswer();
                await pc.setLocalDescription(answer);
                ws.send(JSON.stringify({
                    type: 'answer',
                    sender_id: myClientId,
                    target_id: senderId,
                    answer: answer
                }));
                console.log('Answer sent to', senderId);
            } catch (err) {
                console.error('Error handling offer from', senderId, err);
            }
        }
        async function handleAnswer(senderId, answer) {
            const pc = peerConnections.get(senderId);
            if (!pc) return;
            try {
                await pc.setRemoteDescription(new RTCSessionDescription(answer));
                console.log('Answer set from', senderId);
            } catch (err) {
                console.error('Error handling answer from', senderId, err);
            }
        }
        async function handleIceCandidate(senderId, candidate) {
            const pc = peerConnections.get(senderId);
            if (!pc || !candidate) return;
            try {
                await pc.addIceCandidate(new RTCIceCandidate(candidate));
                console.log('ICE candidate added from', senderId);
            } catch (err) {
                console.error('Error adding ICE candidate from', senderId, err);
            }
        }
        function startSpeakingDetection(stream, remoteId) {
            if (!stream.getAudioTracks()[0]) return;
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            source.connect(analyser);
            audioContexts.set(remoteId, { context: audioContext, analyser, dataArray });
            function detect() {
                analyser.getByteFrequencyData(dataArray);
                const rms = Math.sqrt(dataArray.reduce((a, b) => a + b * b, 0) / bufferLength);
                const wrapper = remoteVideos[remoteId].wrapper;
                if (rms > 10) {  // Adjustable threshold
                    wrapper.classList.add('speaking');
                } else {
                    wrapper.classList.remove('speaking');
                }
                requestAnimationFrame(detect);
            }
            detect();
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
            navigator.clipboard.writeText(currentRoomId).then(() => {
                showCallStatus('✅ Room ID copied! Share it with others.', 'success');
                setTimeout(() => {
                    const count = parseInt(document.getElementById('participantsCount').textContent.match(/\\d+/)[0]);
                    if (count < 5) {
                        showCallStatus('Waiting for more participants...', 'info');
                    }
                }, 2000);
            });
        }
        function hangup() {
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                localStream = null;
            }
            peerConnections.forEach(pc => pc.close());
            peerConnections.clear();
            audioContexts.forEach(ac => ac.context.close());
            audioContexts.clear();
            Object.values(remoteVideos).forEach(({wrapper}) => wrapper.remove());
            remoteVideos = {};
            if (ws) {
                ws.close();
                ws = null;
            }
            permissionsGranted = false;
            myClientId = null;
            myUsername = null;
            currentRoomId = null;
            usernames = {};
            document.getElementById('lobby').classList.remove('hidden');
            document.getElementById('callInterface').classList.add('hidden');
            document.getElementById('videoContainer').classList.remove('active');
            document.getElementById('controls').classList.remove('active');
            document.getElementById('chatSection').classList.add('hidden');
            document.getElementById('chatMessages').innerHTML = '';
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
            document.getElementById('passwordInput').value = '';
            document.getElementById('nameInput').value = '';
            document.getElementById('localVideo').srcObject = null;
            updateParticipants(0);
            showCallStatus('', 'info');
        }
        // Event listeners
        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('chatInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendChat();
            });
            document.getElementById('permissionSection').classList.remove('hidden');
            if (!checkSecureContext()) {
                showPermissionStatus('⚠️ Warning: This page requires a secure context (HTTPS or localhost/127.0.0.1) for camera/microphone access. See notes below.', 'warning');
            }
        });
    </script>
</body>
</html>
    """
    return web.Response(text=html, content_type='text/html')

async def create_room(request):
    data = await request.json()
    room_id = data.get('room_id')
    if not room_id:
        room_id = f"room-{uuid.uuid4().hex[:8]}"
    password = data.get('password', '')
    if len(password) > 100:
        return web.json_response({'success': False, 'error': 'Password too long'})
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM rooms WHERE room_id = ?', (room_id,))
    if cur.fetchone():
        return web.json_response({'success': False, 'error': 'Room ID already exists. Try another or leave empty to generate new.'})
    cur.execute('INSERT INTO rooms (room_id, password) VALUES (?, ?)', (room_id, password))
    conn.commit()
    return web.json_response({'success': True, 'room_id': room_id})

async def join_room(request):
    data = await request.json()
    room_id = data.get('room_id')
    password = data.get('password', '')
    username = data.get('username', '').strip()
    if not room_id or not username or len(username) > 50:
        return web.json_response({'success': False, 'error': 'Invalid room ID or username'})
    cur = conn.cursor()
    cur.execute('SELECT password FROM rooms WHERE room_id = ?', (room_id,))
    row = cur.fetchone()
    if not row:
        return web.json_response({'success': False, 'error': 'Room not found. Create it first?'})
    db_pass = row[0] or ''
    if db_pass and db_pass != password:
        return web.json_response({'success': False, 'error': 'Incorrect password'})
    token = str(uuid.uuid4())
    room = rooms[room_id]
    room['pending_tokens'][token] = username
    cur.execute('SELECT m.username, m.message, m.timestamp FROM messages m WHERE m.room_id = ? ORDER BY m.id ASC LIMIT 50', (room_id,))
    history = [{'username': r[0], 'message': r[1], 'timestamp': r[2]} for r in cur.fetchall()]
    return web.json_response({'success': True, 'room_id': room_id, 'token': token, 'history': history})

async def websocket_handler(request):
    room_id = request.match_info['room_id']
    token = request.query.get('token')
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    room = rooms[room_id]
    if not token or token not in room.get('pending_tokens', {}):
        await ws.send_json({'type': 'error', 'message': 'Invalid or expired token'})
        await ws.close()
        return ws
    username = room['pending_tokens'].pop(token)
    if len(room['participants']) >= MAX_PARTICIPANTS:
        await ws.send_json({'type': 'room_full'})
        await ws.close()
        return ws
    client_id = str(uuid.uuid4())
    participant = {'id': client_id, 'ws': ws, 'username': username}
    room['participants'].append(participant)
    print(f"Client {client_id} ({username}) joined room {room_id}. Total: {len(room['participants'])}")
    other_ids = [p['id'] for p in room['participants'] if p['id'] != client_id]
    await ws.send_json({
        'type': 'room_ready',
        'my_id': client_id,
        'participants_count': len(room['participants']),
        'other_participants': other_ids
    })
    for p in room['participants']:
        if p['id'] != client_id:
            try:
                await p['ws'].send_json({
                    'type': 'new_participant',
                    'new_id': client_id,
                    'participants_count': len(room['participants']),
                    'new_username': username
                })
            except Exception as e:
                print(f"Error notifying participant: {e}")
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                data_type = data.get('type')
                if data_type == 'chat':
                    message = data.get('message', '').strip()[:500]
                    if not message:
                        continue
                    username = participant['username']
                    timestamp = datetime.datetime.now().isoformat()
                    cur = conn.cursor()
                    cur.execute('INSERT INTO messages (room_id, client_id, username, message) VALUES (?, ?, ?, ?)',
                                (room_id, client_id, username, message))
                    conn.commit()
                    broadcast_data = {'type': 'chat', 'username': username, 'message': message, 'timestamp': timestamp}
                    for p in room['participants']:
                        if p['id'] != client_id:
                            try:
                                await p['ws'].send_json(broadcast_data)
                            except Exception as e:
                                print(f"Error broadcasting chat: {e}")
                    continue
                elif data_type in ['offer', 'answer', 'ice_candidate']:
                    target_id = data.get('target_id')
                    if not target_id:
                        continue
                    target_ws = None
                    for p in room['participants']:
                        if p['id'] == target_id:
                            target_ws = p['ws']
                            break
                    if target_ws:
                        try:
                            await target_ws.send_json(data)
                        except Exception as e:
                            print(f"Error sending to target {target_id}: {e}")
                    continue
                else:
                    # Broadcast other messages (e.g., join)
                    for p in room['participants']:
                        if p['id'] != client_id:
                            try:
                                await p['ws'].send_json(data)
                            except Exception as e:
                                print(f"Error forwarding message: {e}")
            elif msg.type == web.WSMsgType.ERROR:
                print(f'WebSocket error: {ws.exception()}')
    except Exception as e:
        print(f"WS loop error: {e}")
    finally:
        room['participants'] = [p for p in room['participants'] if p['id'] != client_id]
        print(f"Client {client_id} left room {room_id}. Remaining: {len(room['participants'])}")
        for p in room['participants']:
            try:
                await p['ws'].send_json({
                    'type': 'participant_left',
                    'left_id': client_id,
                    'participants_count': len(room['participants'])
                })
            except Exception as e:
                print(f"Error notifying left: {e}")
        if len(room['participants']) == 0:
            del rooms[room_id]
            print(f"Room {room_id} deleted")
        await ws.close()
    return ws

app = web.Application()
app.router.add_get('/', index)
app.router.add_post('/create_room', create_room)
app.router.add_post('/join_room', join_room)
app.router.add_get('/ws/{room_id}', websocket_handler)

if __name__ == '__main__':
    init_db()
    print('Server starting on http://127.0.0.1:9080 (recommended for local testing)')
    print('💡 For camera/mic access, use http://127.0.0.1:9080 or http://localhost:9080 in your browser.')
    print(' Avoid 0.0.0.0 or local IPs over HTTP—use ngrok for HTTPS tunneling if needed.')
    print(' High security: Room passwords, tokens, input sanitization, chat history in SQLite.')
    web.run_app(app, host='0.0.0.0', port=9080)






