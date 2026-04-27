const state = {
    chats: [],
    messages: [],
    attachments: [],
    activeChatId: null,
    sending: false,
};

const elements = {
    newChatBtn: document.getElementById("newChatBtn"),
    chatList: document.getElementById("chatList"),
    chatTitle: document.getElementById("chatTitle"),
    chatMeta: document.getElementById("chatMeta"),
    statusPill: document.getElementById("statusPill"),
    messageFeed: document.getElementById("messageFeed"),
    messageTemplate: document.getElementById("messageTemplate"),
    messageInput: document.getElementById("messageInput"),
    sendBtn: document.getElementById("sendBtn"),
    useKnowledgeToggle: document.getElementById("useKnowledgeToggle"),
    fileInput: document.getElementById("fileInput"),
    dropZone: document.getElementById("dropZone"),
    attachmentsList: document.getElementById("attachmentsList"),
};

const ACTIVE_CHAT_KEY = "purchase-ai-chief-active-chat";

function setStatus(text, tone = "neutral") {
    elements.statusPill.textContent = text;
    elements.statusPill.classList.remove("error", "success");
    if (tone === "error") {
        elements.statusPill.classList.add("error");
    }
    if (tone === "success") {
        elements.statusPill.classList.add("success");
    }
}

function formatDateTime(isoString) {
    if (!isoString) {
        return "";
    }
    const date = new Date(isoString);
    if (Number.isNaN(date.getTime())) {
        return "";
    }
    return date.toLocaleString([], {
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function truncate(text, size = 58) {
    const clean = (text || "").trim();
    if (clean.length <= size) {
        return clean;
    }
    return `${clean.slice(0, size - 1)}...`;
}

async function api(path, options = {}) {
    const config = {
        method: options.method || "GET",
        headers: options.headers ? { ...options.headers } : {},
        body: options.body,
    };

    const isMultipart = config.body instanceof FormData;
    if (config.body && !isMultipart && !config.headers["Content-Type"]) {
        config.headers["Content-Type"] = "application/json";
    }

    const response = await fetch(path, config);
    const contentType = response.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const payload = isJson ? await response.json() : await response.text();

    if (!response.ok) {
        const detail = isJson ? payload.detail || JSON.stringify(payload) : payload;
        throw new Error(detail || `Request failed with ${response.status}`);
    }

    return payload;
}

function renderChats() {
    elements.chatList.innerHTML = "";

    if (!state.chats.length) {
        elements.chatList.innerHTML = '<div class="empty-state">No conversations yet. Start a new chat.</div>';
        return;
    }

    state.chats.forEach((chat, idx) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "chat-item";
        button.style.animationDelay = `${Math.min(idx * 0.04, 0.24)}s`;

        if (chat.id === state.activeChatId) {
            button.classList.add("active");
        }

        const title = truncate(chat.title || "New Purchase Session", 58);
        const meta = `${chat.message_count || 0} msgs - ${formatDateTime(chat.updated_at) || "just now"}`;

        const titleNode = document.createElement("p");
        titleNode.className = "chat-item-title";
        titleNode.textContent = title;

        const metaNode = document.createElement("p");
        metaNode.className = "chat-item-meta";
        metaNode.textContent = meta;

        button.append(titleNode, metaNode);

        button.addEventListener("click", () => {
            if (chat.id !== state.activeChatId) {
                void selectChat(chat.id);
            }
        });

        elements.chatList.appendChild(button);
    });
}

function renderHeader() {
    const active = state.chats.find((chat) => chat.id === state.activeChatId);
    if (!active) {
        elements.chatTitle.textContent = "Active Conversation";
        elements.chatMeta.textContent = "Use this assistant for costing, compliance, EXIM, vendor strategy, and purchase operations.";
        return;
    }

    elements.chatTitle.textContent = active.title || "New Purchase Session";
    elements.chatMeta.textContent = `${active.message_count || 0} messages - last updated ${
        formatDateTime(active.updated_at) || "just now"
    }`;
}

function createMessageNode(message) {
    const fragment = elements.messageTemplate.content.cloneNode(true);
    const row = fragment.querySelector(".message-row");
    const role = fragment.querySelector(".message-role");
    const time = fragment.querySelector(".message-time");
    const text = fragment.querySelector(".message-text");
    const card = fragment.querySelector(".message-card");

    const isUser = message.role === "user";

    if (isUser) {
        row.classList.add("user");
        role.textContent = "You";
    } else {
        role.textContent = "Purchase AI Chief";
    }

    if (message.loading) {
        card.classList.add("loading");
    }

    time.textContent = formatDateTime(message.created_at) || "";
    text.textContent = message.content || "";

    return fragment;
}

function renderMessages() {
    elements.messageFeed.innerHTML = "";

    if (!state.messages.length) {
        elements.messageFeed.innerHTML = `
            <div class="empty-state">
                Conversation is empty. Ask your first procurement question.
            </div>
        `;
        return;
    }

    state.messages.forEach((message) => {
        elements.messageFeed.appendChild(createMessageNode(message));
    });

    elements.messageFeed.scrollTop = elements.messageFeed.scrollHeight;
}

function renderAttachments() {
    elements.attachmentsList.innerHTML = "";

    if (!state.attachments.length) {
        elements.attachmentsList.innerHTML = '<div class="empty-state">No attachment uploaded for this chat.</div>';
        return;
    }

    state.attachments.forEach((item) => {
        const card = document.createElement("article");
        card.className = "attachment-item";

        const kb = Math.max(1, Math.round(item.char_count / 1024));

        const nameNode = document.createElement("p");
        nameNode.className = "attachment-name";
        nameNode.textContent = truncate(item.original_name, 80);

        const metaNode = document.createElement("p");
        metaNode.className = "attachment-meta";
        metaNode.textContent = `${kb} KB text index - ${formatDateTime(item.created_at) || "now"}`;

        card.append(nameNode, metaNode);

        elements.attachmentsList.appendChild(card);
    });
}

async function loadChats() {
    state.chats = await api("/api/chats");
    renderChats();
    renderHeader();
}

async function loadMessages(chatId) {
    state.messages = await api(`/api/chats/${chatId}/messages`);
    renderMessages();
}

async function loadAttachments(chatId) {
    state.attachments = await api(`/api/chats/${chatId}/attachments`);
    renderAttachments();
}

async function selectChat(chatId) {
    state.activeChatId = chatId;
    localStorage.setItem(ACTIVE_CHAT_KEY, chatId);

    renderChats();
    renderHeader();
    setStatus("Loading conversation...");

    try {
        await Promise.all([loadMessages(chatId), loadAttachments(chatId)]);
        setStatus("Ready", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

function addTemporaryMessage(role, content, loading = false) {
    state.messages.push({
        id: `temp-${Date.now()}-${Math.random().toString(16).slice(2)}`,
        role,
        content,
        loading,
        created_at: new Date().toISOString(),
    });
    renderMessages();
}

async function sendMessage() {
    if (!state.activeChatId || state.sending) {
        return;
    }

    const message = elements.messageInput.value.trim();
    if (!message) {
        return;
    }

    state.sending = true;
    elements.sendBtn.disabled = true;
    setStatus("Generating answer...");

    const chatId = state.activeChatId;
    elements.messageInput.value = "";

    addTemporaryMessage("user", message, false);
    addTemporaryMessage("assistant", "Working through your request...", true);

    try {
        await api(`/api/chats/${chatId}/messages`, {
            method: "POST",
            body: JSON.stringify({
                message,
                use_knowledge: elements.useKnowledgeToggle.checked,
            }),
        });

        await Promise.all([loadChats(), loadMessages(chatId)]);
        renderHeader();
        setStatus("Response ready", "success");
    } catch (error) {
        await loadMessages(chatId);
        addTemporaryMessage("assistant", `I hit an error: ${error.message}`, false);
        setStatus(error.message, "error");
    } finally {
        state.sending = false;
        elements.sendBtn.disabled = false;
    }
}

async function createNewChat() {
    setStatus("Creating new chat...");
    try {
        const chat = await api("/api/chats", { method: "POST" });
        await loadChats();
        await selectChat(chat.id);
        elements.messageInput.focus();
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function uploadFiles(files) {
    if (!state.activeChatId || !files.length) {
        return;
    }

    let successCount = 0;

    for (const file of files) {
        setStatus(`Uploading ${truncate(file.name, 28)}...`);

        const formData = new FormData();
        formData.append("file", file);

        try {
            await api(`/api/chats/${state.activeChatId}/attachments`, {
                method: "POST",
                body: formData,
            });
            successCount += 1;
        } catch (error) {
            setStatus(`${file.name}: ${error.message}`, "error");
        }
    }

    await loadAttachments(state.activeChatId);

    if (successCount > 0) {
        setStatus(`Uploaded ${successCount} file(s)`, "success");
    }
}

function bindEvents() {
    elements.newChatBtn.addEventListener("click", () => {
        void createNewChat();
    });

    elements.sendBtn.addEventListener("click", () => {
        void sendMessage();
    });

    elements.messageInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            void sendMessage();
        }
    });

    elements.fileInput.addEventListener("change", async (event) => {
        const files = Array.from(event.target.files || []);
        if (files.length) {
            await uploadFiles(files);
            elements.fileInput.value = "";
        }
    });

    ["dragenter", "dragover"].forEach((name) => {
        elements.dropZone.addEventListener(name, (event) => {
            event.preventDefault();
            event.stopPropagation();
            elements.dropZone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach((name) => {
        elements.dropZone.addEventListener(name, (event) => {
            event.preventDefault();
            event.stopPropagation();
            elements.dropZone.classList.remove("dragover");
        });
    });

    elements.dropZone.addEventListener("drop", (event) => {
        const files = Array.from(event.dataTransfer?.files || []);
        if (files.length) {
            void uploadFiles(files);
        }
    });
}

async function initialize() {
    bindEvents();

    try {
        await api("/api/health");
        setStatus("Connected", "success");
    } catch (error) {
        setStatus(`API unavailable: ${error.message}`, "error");
    }

    await loadChats();

    let activeChatId = localStorage.getItem(ACTIVE_CHAT_KEY);

    if (!state.chats.length) {
        const firstChat = await api("/api/chats", { method: "POST" });
        await loadChats();
        activeChatId = firstChat.id;
    }

    const exists = state.chats.some((chat) => chat.id === activeChatId);
    if (!exists) {
        activeChatId = state.chats[0]?.id || null;
    }

    if (activeChatId) {
        await selectChat(activeChatId);
    }

    elements.messageInput.focus();
}

void initialize();
