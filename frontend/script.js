// ===== GLOBAL STATE =====
let currentChatId = null;
let uploadedFilePath = localStorage.getItem("filePath") || "";
let selectedFileElement = null;

// ===== LOAD FILES =====
function loadFiles() {
  const token = localStorage.getItem("token");
  const fileList = document.getElementById("fileList");

  if (!fileList || !token) return;

  fetch("http://127.0.0.1:8000/files", {
    headers: {
      "Authorization": "Bearer " + token
    }
  })
  .then(res => res.json())
  .then(files => {
    fileList.innerHTML = "";

    files.forEach(file => {
      const div = document.createElement("div");
      div.innerText = file.name;
      div.className = "file-item";

      if (file.path === uploadedFilePath) {
        div.classList.add("active");
        selectedFileElement = div;
      }

      div.onclick = () => {
        uploadedFilePath = file.path;
        localStorage.setItem("filePath", file.path);

        if (selectedFileElement) {
          selectedFileElement.classList.remove("active");
        }

        div.classList.add("active");
        selectedFileElement = div;
      };

      fileList.appendChild(div);
    });
  });
}

// ===== LOAD FILES =====
function loadFiles() {
  const token = localStorage.getItem("token");

  fetch("http://127.0.0.1:8000/files", {
    headers: { "Authorization": "Bearer " + token }
  })
  .then(res => res.json())
  .then(files => {
    const list = document.getElementById("fileList");
    list.innerHTML = "";

    files.forEach(f => {
      const div = document.createElement("div");
      div.innerText = f.file_name;

      div.onclick = () => {
        uploadedFilePath = f.file_path;
        localStorage.setItem("filePath", f.file_path);
      };

      list.appendChild(div);
    });
  });
}

// ===== LOAD CHATS =====
function loadChats() {
  const token = localStorage.getItem("token");

  fetch("http://127.0.0.1:8000/chat/list", {
    headers: { "Authorization": "Bearer " + token }
  })
  .then(res => res.json())
  .then(chats => {
    const history = document.querySelector(".history");
    history.innerHTML = "";

    chats.forEach(c => {
      const div = document.createElement("div");
      div.innerText = c.title;

      div.onclick = () => {
        currentChatId = c.id;
        loadMessages(c.id);
      };

      history.appendChild(div);
    });
  });
}

// ===== LOAD MESSAGES =====
function loadMessages(id) {
  const token = localStorage.getItem("token");

  fetch(`http://127.0.0.1:8000/chat/messages?chat_id=${id}`, {
    headers: { "Authorization": "Bearer " + token }
  })
  .then(res => res.json())
  .then(msgs => {
    const box = document.getElementById("chatBox");
    box.innerHTML = "";

    msgs.forEach(m => {
      const d = document.createElement("div");
      d.innerText = m.content;
      d.className = m.role === "user" ? "msg-user" : "msg-ai";
      box.appendChild(d);
    });
  });
}

// ===== ASK =====
window.askQuestion = async function () {
  const token = localStorage.getItem("token");
  const q = document.getElementById("questionInput").value;

  const res = await fetch(
    `http://127.0.0.1:8000/query?file_path=${uploadedFilePath}&question=${encodeURIComponent(q)}${currentChatId ? "&chat_id="+currentChatId : ""}`,
    { headers: { "Authorization": "Bearer " + token } }
  );

  const data = await res.json();

  currentChatId = data.chat_id;

  loadChats();
  loadMessages(currentChatId);
};

// ===== INIT =====
document.addEventListener("DOMContentLoaded", () => {

  const token = localStorage.getItem("token");

  // ===== CARD FLIP =====
  const card = document.getElementById("card");
  if (card) {
    const registerTab = document.querySelector(".register");
    const loginTab = document.querySelector(".login");

    if (registerTab) registerTab.onclick = () => card.classList.add("flip");
    if (loginTab) loginTab.onclick = () => card.classList.remove("flip");
  }

  // ===== REGISTER =====
  const registerBtn = document.getElementById("registerBtn");
  if (registerBtn) {
    registerBtn.onclick = async () => {
      const name = document.getElementById("regName").value.trim();
      const email = document.getElementById("regEmail").value.trim();
      const password = document.getElementById("regPassword").value;
      const confirm = document.getElementById("confirmPassword").value;

      if (!name || !email || !password || !confirm) {
        alert("Please fill all fields");
        return;
      }

      if (password !== confirm) {
        alert("Passwords do not match");
        return;
      }

      const res = await fetch("http://127.0.0.1:8000/signup", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({email, password, name})
      });

      if (res.ok) {
        alert("Registered successfully");
        card.classList.remove("flip");
      }
    };
  }

  // ===== LOGIN =====
  const loginBtn = document.getElementById("loginBtn");
  if (loginBtn) {
    loginBtn.onclick = async () => {
      const email = document.getElementById("loginEmail").value.trim();
      const password = document.getElementById("loginPassword").value;

      const res = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({email, password})
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem("token", data.access_token);
        window.location.href = "dashboard.html";
      } else {
        alert("Login failed");
      }
    };
  }

  // ===== DASHBOARD =====
  if (window.location.pathname.includes("dashboard")) {

    if (!token) {
      window.location.href = "index.html";
      return;
    }

    fetch("http://127.0.0.1:8000/dashboard", {
      headers: {"Authorization": "Bearer " + token}
    })
    .then(res => res.json())
    .then(data => {
      document.querySelector("h2").innerText = data.message;

      loadFiles();
      loadChats();   
    });


    // ===== OPEN FILE PICKER =====
    const uploadBtn = document.querySelector(".icon-btn"); // 

    if (uploadBtn) {
      uploadBtn.addEventListener("click", () => {
        document.getElementById("fileInput").click();
      });
    }

    // ===== NEW CHAT =====
    const newChatBtn = document.querySelector(".new-chat");

    if (newChatBtn) {
      newChatBtn.onclick = async () => {
        if (!uploadedFilePath) {
          alert("Select file first");
          return;
        }

        const res = await fetch(`http://127.0.0.1:8000/chat/create?file_path=${uploadedFilePath}`, {
          method: "POST",
          headers: {"Authorization": "Bearer " + token}
        });

        const data = await res.json();

        currentChatId = data.chat_id;

        document.getElementById("chatBox").innerHTML = "";

        loadChats();
      };
    }

    // ===== FILE UPLOAD =====
    const fileInput = document.getElementById("fileInput");

    if (fileInput) {
      fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const fileNameDisplay = document.getElementById("fileName");

        fileNameDisplay.innerText = "Uploading: " + file.name;

        let formData = new FormData();
        formData.append("file", file);

        const res = await fetch("http://127.0.0.1:8000/upload", {
          method: "POST",
          headers: {"Authorization": "Bearer " + token},
          body: formData
        });

        const data = await res.json();

        if (res.ok) {
          uploadedFilePath = data.path;
          localStorage.setItem("filePath", data.path);

          fileNameDisplay.innerText = "✅ " + file.name;
          loadFiles();
        } else {
          fileNameDisplay.innerText = "❌ Upload failed";
        }
      };
    }
  }
});

// ===== ASK QUESTION =====
window.askQuestion = async function () {
  const questionInput = document.getElementById("questionInput");
  const question = questionInput.value.trim();
  const chatBox = document.getElementById("chatBox");
  const token = localStorage.getItem("token");

  if (!currentChatId) {
    alert("Create a chat first");
    return;
  }

  const userMsg = document.createElement("div");
  userMsg.className = "msg-user";
  userMsg.innerText = question;
  chatBox.appendChild(userMsg);

  // SAVE USER MESSAGE
  await fetch(`http://127.0.0.1:8000/chat/message?chat_id=${currentChatId}&role=user&content=${encodeURIComponent(question)}`, {
    method: "POST"
  });

  const res = await fetch(
    `http://127.0.0.1:8000/query?file_path=${uploadedFilePath}&question=${encodeURIComponent(question)}`,
    { headers: {"Authorization": "Bearer " + token} }
  );

  const data = await res.json();

  const aiMsg = document.createElement("div");
  aiMsg.className = "msg-ai";
  aiMsg.innerText = data.answer || data.error;

  chatBox.appendChild(aiMsg);

  // SAVE AI MESSAGE
  await fetch(`http://127.0.0.1:8000/chat/message?chat_id=${currentChatId}&role=ai&content=${encodeURIComponent(aiMsg.innerText)}`, {
    method: "POST"
  });

  chatBox.scrollTop = chatBox.scrollHeight;
};

function logout() {
  // Clear any stored data (important if you're using login/session)
  localStorage.clear();
  sessionStorage.clear();

  // Redirect to login page
  window.location.href = "index.html";
}
