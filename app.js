// Base URL for your FastAPI backend
const BACKEND_URL = "http://127.0.0.1:8000";

let sessionId = null;
let cluesFound = 0;
let currentLocation = "The Great Hall";
let isProcessing = false;

// --- DOM References ---
const messagesContainer = document.getElementById("messages");
const locationSpan = document.getElementById("location");
const cluesSpan = document.getElementById("clues");
const submitBtn = document.getElementById("submitBtn");
const actionInput = document.getElementById("actionInput");

// --- Utility Functions ---

/**
 * Adds a new message element to the chat history.
 * @param {string} speaker - The name of the speaker (e.g., 'Professor Dumbledore', 'You').
 * @param {string} text - The dialogue or narrative text.
 * @param {string} avatarType - The type for styling ('purple', 'blue', 'brown', 'green').
 */
function addMessage(speaker, text, avatarType) {
    const message = document.createElement("div");
    message.className = "message";
    
    const avatarIcons = {
        purple: "🧙‍♂️",
        blue: "👤",
        brown: "📖",
        green: "🗣️",
        system: "🤖"
    };
    
    message.innerHTML = `
        <div class="avatar avatar-${avatarType}">${avatarIcons[avatarType] || '👤'}</div>
        <div class="message-content">
            <div class="speaker">${speaker}</div>
            <div class="text">${text}</div>
        </div>
    `;
    
    messagesContainer.appendChild(message);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Updates the visual status bar based on the backend state.
 * @param {object} state - The state object received from the backend.
 */
function updateStatus(state) {
    currentLocation = state.location;
    cluesFound = state.clues_found;
    
    locationSpan.textContent = state.location;
    cluesSpan.textContent = state.clues_found;
}

/**
 * Renders the full timeline from the backend state.
 * @param {Array<object>} timeline - The array of message objects.
 */
function renderTimeline(timeline) {
    messagesContainer.innerHTML = ''; // Clear existing messages
    timeline.forEach(m => addMessage(m.speaker, m.text, m.avatar_type));
}

// --- API Interaction ---

/**
 * Initializes a new game session with the backend.
 */
async function startNewSession() {
    try {
        isProcessing = true;
        submitBtn.disabled = true;
        
        // Use a system message while waiting for the first Dumbledore message
        addMessage("System", "Connecting to Hogwarts Network...", "system");
        
        const response = await fetch(`${BACKEND_URL}/session/start`, { method: "POST" });
        const data = await response.json();
        
        if (response.ok) {
            sessionId = data.session_id;
            // Clear the temporary system message
            messagesContainer.innerHTML = ''; 
            updateStatus(data.state);
            renderTimeline(data.state.timeline);
            console.log("Session started:", sessionId);
        } else {
            addMessage("System Error", `Failed to start session: ${data.detail || response.statusText}`, "system");
            throw new Error(data.detail || response.statusText);
        }
    } catch (error) {
        addMessage("System Error", `A fatal error occurred: ${error.message}. Check the backend is running.`, "system");
        console.error("Start Session Error:", error);
    } finally {
        isProcessing = false;
        submitBtn.disabled = false;
    }
}

/**
 * Submits the player's action to the backend API.
 */
async function submitAction() {
    if (!sessionId || !actionInput.value.trim() || isProcessing) return;
    
    const playerAction = actionInput.value.trim();
    
    addMessage("You", playerAction, "blue");
    actionInput.value = "";
    isProcessing = true;
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`${BACKEND_URL}/session/action`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId, text: playerAction })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // The backend returns an array of reply messages (one or more)
            data.reply.forEach(m => addMessage(m.speaker, m.text, m.avatar_type));
            
            // Update the state (location, clues, etc.)
            updateStatus(data.state);
        } else {
            // Handle HTTP errors
            const errorMessage = data.detail || `Error: ${response.status} ${response.statusText}`;
            addMessage("System Error", `Action failed: ${errorMessage}`, "system");
            console.error("Action Error:", errorMessage);
        }
    } catch (error) {
        addMessage("System Error", `Could not reach the server: ${error.message}.`, "system");
        console.error("Fetch Error:", error);
    } finally {
        isProcessing = false;
        submitBtn.disabled = false;
        actionInput.focus();
    }
}

// --- Event Listeners and Initialization ---

function handleKeyPress(e) {
    if (e.key === "Enter") submitAction();
}

function resetGame() {
    // Reload the page to reset the entire frontend and start a new backend session
    window.location.reload();
}

document.addEventListener("DOMContentLoaded", () => {
    // Attach event listeners
    submitBtn.addEventListener("click", submitAction);
    document.getElementById("newGameBtn").addEventListener("click", resetGame);
    actionInput.addEventListener("keypress", handleKeyPress);
    
    // Start the game session when the page loads
    startNewSession();
});

