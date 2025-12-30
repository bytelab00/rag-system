const UPLOAD_URL = "/api/ingestion/upload";
const QUERY_URL = "/api/query/query";

const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const uploadBtn = document.getElementById("uploadBtn");
const chatContainer = document.getElementById("chatContainer");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");

let hasUploadedDocument = false;
let uploadedFileName = "";

/* File selection */
fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        uploadedFileName = fileInput.files[0].name;
        fileName.textContent = uploadedFileName;
        uploadBtn.disabled = false;
    }
});

/* Upload */
uploadBtn.addEventListener("click", async () => {
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    uploadBtn.textContent = "Uploading...";
    uploadBtn.disabled = true;

    try {
        const res = await fetch(UPLOAD_URL, {
            method: "POST",
            body: formData
        });

        if (!res.ok) throw new Error();

        hasUploadedDocument = true;
        questionInput.disabled = false;
        sendBtn.disabled = false;

        fileName.textContent = `Uploaded: ${uploadedFileName}`;
    } catch {
        fileName.textContent = "Upload failed";
    } finally {
        uploadBtn.textContent = "Upload";
    }
});

/* Send question */
sendBtn.addEventListener("click", sendQuestion);
questionInput.addEventListener("keydown", e => {
    if (e.key === "Enter") sendQuestion();
});

async function sendQuestion() {
    const question = questionInput.value.trim();
    if (!question || !hasUploadedDocument) return;

    removeEmptyState();
    addMessage(question, "user");

    questionInput.value = "";
    questionInput.disabled = true;
    sendBtn.disabled = true;

    try {
        const res = await fetch(QUERY_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, top_k: 3 })
        });

        const data = await res.json();
        addMessage(data.answer || "No response.", "assistant");
    } catch {
        addMessage("Server error.", "assistant");
    } finally {
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    }
}

/* Helpers */
function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.className = `message ${sender}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = sender === "user" ? "U" : "AI";

    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = text;

    msg.appendChild(avatar);
    msg.appendChild(content);
    chatContainer.appendChild(msg);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeEmptyState() {
    const empty = chatContainer.querySelector(".empty-state");
    if (empty) empty.remove();
}
