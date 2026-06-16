// ===== GLOBAL STATE =====
let latestAIResponse = null;
let latestTableData = null;
let latestDashboardData = null;
let latestQuestion = "";
let latestResponseText = "";
let isProcessing = false;
let currentChatId = localStorage.getItem("currentChatId") || null;
let uploadedFilePath = localStorage.getItem("filePath") || "";

// ===== INIT =====
document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("token");
  const path = window.location.pathname;

  // AUTH PAGE
  if (document.querySelector(".card")) {
    initAuthPage();
  }

  // DASHBOARD PAGE
  if (path.includes("dashboard")) {
    initDashboard(token);
  }
});

// ===== AUTH PAGE =====
function initAuthPage() {
  const loginTab = document.querySelector(".login");
  const registerTab = document.querySelector(".register");
  const card = document.getElementById("card");

  // ===== FLIP =====
  if (loginTab && registerTab && card) {
    loginTab.onclick = () => {
      card.classList.remove("flip");
    };

    registerTab.onclick = () => {
      card.classList.add("flip");
    };
  }

  // ===== REGISTER =====
  const registerBtn = document.getElementById("registerBtn");

  if (registerBtn) {
    registerBtn.onclick = async () => {
      try {
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
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            password,
            name,
          }),
        });

        if (!res.ok) {
          alert("Registration failed");
          return;
        }

        alert("Registered successfully");

        card.classList.remove("flip");
      } catch (err) {
        console.error(err);

        alert("Network error");
      }
    };
  }

  // ===== LOGIN =====
  const loginBtn = document.getElementById("loginBtn");

  if (loginBtn) {
    loginBtn.onclick = async () => {
      try {
        const email = document.getElementById("loginEmail").value.trim();
        const password = document.getElementById("loginPassword").value;

        if (!email || !password) {
          alert("Enter email and password");
          return;
        }

        const res = await fetch("http://127.0.0.1:8000/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            password,
          }),
        });

        const data = await res.json();

        if (res.ok) {
          localStorage.setItem("token", data.access_token);

          window.location.href = "dashboard.html";
        } else {
          alert(data.detail || "Login failed");
        }
      } catch (err) {
        console.error(err);

        alert("Network error");
      }
    };
  }
}

// ===== DASHBOARD =====
function initDashboard(token) {
  if (!token) {
    window.location.href = "index.html";
    return;
  }

  fetch("http://127.0.0.1:8000/dashboard", {
    headers: {
      Authorization: "Bearer " + token,
    },
  })
    .then((res) => res.json())
    .then((data) => {
      const heading = document.querySelector("h2");

      if (heading) {
        const email = data.message
          .replace("Welcome ", "")
          .replace("!", "");

        const name = email.split("@")[0];

        const hour = new Date().getHours();

        let greeting = "Hello";

        if (hour < 12) {
          greeting = "Good morning";
        } else if (hour < 18) {
          greeting = "Good afternoon";
        } else {
          greeting = "Good evening";
        }

        heading.innerText = `${greeting}, ${name} 👋`;
      }

      loadFiles();
      loadChats();

      if (currentChatId) {
        loadMessages(currentChatId);
      }

      if (uploadedFilePath) {
        const fileNameDisplay =
          document.getElementById("fileName");

        if (fileNameDisplay) {
          const name =
            uploadedFilePath.split("/").pop();

          fileNameDisplay.innerText =
            "📄 " + name;
        }
      }
    })
    .catch((err) => {
      console.error(err);
    });

  // ===== NEW CHAT =====
  const newChatBtn =
    document.querySelector(".new-chat");

  if (newChatBtn) {
    newChatBtn.onclick = () => {
      currentChatId = null;
      uploadedFilePath = "";

      localStorage.removeItem("currentChatId");
      localStorage.removeItem("filePath");

      const chatBox =
        document.getElementById("chatBox");

      if (chatBox) {
        chatBox.innerHTML = "";

        chatBox.innerHTML = `
          <div id="dashboardContainer" class="dashboard-container"></div>
          <div class="empty-state" id="emptyState">

            <h3>
              Upload a dataset and start asking questions
            </h3>

            <p>
              Try:
            </p>

            <div class="suggestions">

              <button onclick="useSuggestion(this)">
                Top 5 sales by region
              </button>

              <button onclick="useSuggestion(this)">
                Average revenue by month
              </button>

              <button onclick="useSuggestion(this)">
                Show revenue chart
              </button>

            </div>

          </div>
        `;
      }

      const fileName =
        document.getElementById("fileName");

      if (fileName) {
        fileName.innerText = "";
      }
    };
  }

  // ===== FILE INPUT =====
  const fileInput =
    document.getElementById("fileInput");

  if (fileInput) {
    fileInput.onchange = handleFileUpload;
  }

  // ===== UPLOAD BUTTON =====
  const uploadBtn =
    document.getElementById("uploadBtn");

  if (uploadBtn) {
    uploadBtn.onclick = () => {
      if (fileInput) {
        fileInput.click();
      }
    };
  }
}
// ===== FILE UPLOAD =====
async function handleFileUpload(e) {
  try {
    const token = localStorage.getItem("token");

    const file = e.target.files[0];

    if (!file) return;

    const fileNameDisplay =
      document.getElementById("fileName");

    if (fileNameDisplay) {
      fileNameDisplay.innerText =
        "Uploading: " + file.name;
    }

    let formData = new FormData();

    formData.append("file", file);

    const res = await fetch(
      "http://127.0.0.1:8000/upload",
      {
        method: "POST",
        headers: {
          Authorization: "Bearer " + token,
        },
        body: formData,
      }
    );

    const data = await res.json();

    if (res.ok) {
      uploadedFilePath = data.path;

      localStorage.setItem(
        "filePath",
        data.path
      );

      if (fileNameDisplay) {
        fileNameDisplay.innerText =
          "✅ " + file.name;

        const statsBox =
          document.getElementById(
            "datasetStats"
          );

        const infoRes = await fetch(
          `http://127.0.0.1:8000/dataset/info?file_path=${data.path}`
        );

        const info = await infoRes.json();

        statsBox.innerHTML = `
          <span>${info.rows} rows</span>
          <span>${info.columns} columns</span>
        `;
      }

      loadFiles();
    } else {
      if (fileNameDisplay) {
        fileNameDisplay.innerText =
          "❌ Upload failed";
      }
    }

    e.target.value = "";
  } catch (err) {
    console.error(err);

    alert("Upload failed");
  }
}

// ===== LOAD FILES =====
function loadFiles() {
  const token = localStorage.getItem("token");

  const fileList =
    document.getElementById("fileList");

  if (!fileList || !token) return;

  fetch("http://127.0.0.1:8000/files", {
    headers: {
      Authorization: "Bearer " + token,
    },
  })
    .then((res) => res.json())
    .then((files) => {
      fileList.innerHTML = "";

      files.forEach((file) => {
        const div =
          document.createElement("div");

        div.innerText = file.name;

        div.className = "file-item";

        div.onclick = () => {
          uploadedFilePath =
            file.path || "";

          localStorage.setItem(
            "filePath",
            uploadedFilePath
          );

          const fileNameDisplay =
            document.getElementById(
              "fileName"
            );

          if (fileNameDisplay) {
            fileNameDisplay.innerText =
              "📄 " + file.name;
          }
        };

        fileList.appendChild(div);
      });
    })
    .catch((err) => {
      console.error(err);
    });
}

// ===== LOAD CHATS =====
function loadChats() {
  const token = localStorage.getItem("token");

  fetch("http://127.0.0.1:8000/chat/list", {
    headers: {
      Authorization: "Bearer " + token,
    },
  })
    .then((res) => res.json())
    .then((chats) => {
      const history =
        document.querySelector(".chat-list");

      if (!history) return;

      history.innerHTML = "";

      chats.forEach((chat) => {
        const div =
          document.createElement("div");

        const deleteBtn =
          document.createElement("button");

        deleteBtn.innerHTML = "✕";

        deleteBtn.className =
          "delete-chat-btn";

        div.innerText = chat.title;

        div.className = "chat-item";

        div.onclick = () => {
          currentChatId = chat.id;

          uploadedFilePath =
            chat.file_path || "";

          localStorage.setItem(
            "currentChatId",
            currentChatId
          );

          localStorage.setItem(
            "filePath",
            uploadedFilePath
          );

          const fileNameDisplay =
            document.getElementById(
              "fileName"
            );

          if (
            fileNameDisplay &&
            uploadedFilePath
          ) {
            const name =
              uploadedFilePath
                .split("/")
                .pop();

            fileNameDisplay.innerText =
              "📄 " + name;
          }

          loadMessages(chat.id);
        };

        deleteBtn.onclick = async (e) => {
          e.stopPropagation();

          const confirmDelete =
            confirm("Delete this chat?");

          if (!confirmDelete) return;

          await fetch(
            `http://127.0.0.1:8000/chat/delete/${chat.id}`,
            {
              method: "DELETE",
              headers: {
                Authorization: "Bearer " + token,
              },
            }
          );

          if (
            currentChatId === chat.id
          ) {
            currentChatId = null;

            localStorage.removeItem(
              "currentChatId"
            );
          }

          loadChats();
        };

        div.appendChild(deleteBtn);

        history.appendChild(div);
      });
    })
    .catch((err) => {
      console.error(err);
    });
}
// ===== LOAD MESSAGES =====
function loadMessages(chatId) {
  fetch(
    `http://127.0.0.1:8000/chat/messages/${chatId}`
  )
    .then((res) => res.json())
    .then((messages) => {
      const chatBox =
        document.getElementById("chatBox");

      if (!chatBox) return;

      chatBox.innerHTML = `
        <div id="dashboardContainer" class="dashboard-container"></div>
      `;

      messages.forEach((msg) => {
        const div =
          document.createElement("div");

        div.className =
          msg.role === "user"
            ? "msg-user"
            : "msg-ai";

        // ===== MESSAGE RENDER =====
        try {

          const parsed =
            JSON.parse(msg.content);

          // ===== TABLE =====
          if (parsed.type === "table") {
            div.classList.add("table-msg");

            renderTable(
              {
                columns: parsed.columns,
                rows: parsed.rows,
              },
              div
            );

            if (parsed.summary) {

              const summary =
                document.createElement("p");

              summary.className =
                "ai-summary";

              summary.innerText =
                parsed.summary;

              div.appendChild(summary);
            }
          }

          // ===== CHART =====
          else if (parsed.type === "chart") {

            const canvas =
              document.createElement("canvas");

            canvas.width = 650;
            canvas.height = 350;

            div.appendChild(canvas);

            new Chart(
              canvas.getContext("2d"),
              {
                type: parsed.chart_type,

                data: {
                  labels: parsed.labels,

                  datasets: [
                    {
                      label: "Analytics",

                      data: parsed.values,

                      borderWidth: 2,

                      backgroundColor: parsed.labels.map(
                        (_, index) =>
                          `hsl(${index * 50}, 70%, 60%)`
                      ),

                      tension: 0.4,

                      fill: true,
                    },
                  ],
                },

                options: {
                  responsive: true,
                  maintainAspectRatio: false,

                  plugins: {
                    legend: {
                      labels: {
                        color: "white",
                      },
                    },
                  },
                },
              }
            );

            if (parsed.summary) {

              const summary =
                document.createElement("p");

              summary.className =
                "ai-summary";

              summary.innerText =
                parsed.summary;

              div.appendChild(summary);
            }
          }

          // ===== TEXT =====
          else {

            div.innerText =
              parsed.answer ||
              parsed.summary ||
              msg.content;
          }

        } catch {

          div.innerText = msg.content;
        }

        chatBox.appendChild(div);
      });

      chatBox.scrollTop =
        chatBox.scrollHeight;
    })
    .catch((err) => {
      console.error(err);
    });
}

// ===== SEND QUESTION =====
async function askQuestion() {
  if(isProcessing) return;
  isProcessing = true;
  
  try {
    const input =
      document.getElementById(
        "questionInput"
      );

    const chatBox =
      document.getElementById("chatBox");

    if (!input || !chatBox) {
      isProcessing = false;
      return;
    }

    if (!input || !chatBox) return;

    const question =
      input.value.trim();
      latestQuestion = question;

    if (!question) {
      isProcessing = false;
      return;
    }

    const fileToUse =
      getFileForCurrentChat();

    if (!fileToUse) {
      isProcessing = false;
      alert("Upload dataset first");
      return;
    }

    // ===== USER MESSAGE =====
    const userMsg =
      document.createElement("div");

    userMsg.className = "msg-user";

    userMsg.innerText = question;

    chatBox.appendChild(userMsg);

    // ===== LOADER =====
    const loader =
      document.createElement("div");

    loader.className = "msg-ai";

    loader.innerHTML =
      "<span class='loader'></span>";

    chatBox.appendChild(loader);
    if (
      question.toLowerCase().includes(
        "dashboard"
      )
    ) {

      loader.remove();

      await generateDashboard();

      input.value = "";

      isProcessing = false;

      return;
    }

    chatBox.scrollTop =
      chatBox.scrollHeight;

    // ===== CREATE CHAT =====
    if (!currentChatId) {
      const token =
        localStorage.getItem("token");

      const createRes =
        await fetch(
          "http://127.0.0.1:8000/chat/create",
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                "Bearer " + token,
            },

            body: JSON.stringify({
              title: question,
              file_path: fileToUse,
            }),
          }
        );

      const chat =
        await createRes.json();

      currentChatId = chat.id;

      localStorage.setItem(
        "currentChatId",
        currentChatId
      );

      loadChats();
    }

    // ===== SAVE USER MESSAGE =====
    await fetch(
      "http://127.0.0.1:8000/chat/message",
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          chat_id: currentChatId,
          role: "user",
          content: question,
        }),
      }
    );

    // ===== QUERY API =====
    const token =
      localStorage.getItem("token");

    const res = await fetch(
      "http://127.0.0.1:8000/query",
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          Authorization:
            "Bearer " + token,
        },

        body: JSON.stringify({
          question: question,
          file_path: fileToUse,
        }),
      }
    );

    let data;

    try {
      data = await res.json();
    } catch {
      loader.remove();

      const raw = await res.text();

      console.log(raw);

      isProcessing = false;
      alert(
        "Backend returned invalid JSON"
      );

      return;
    }

    latestAIResponse = data;

    loader.remove();

    console.log(
      "FULL RESPONSE:",
      data
    );

    // ===== AI MESSAGE =====
    const aiMsg =
      document.createElement("div");

    aiMsg.className = "msg-ai";

    let contentToSave = "";

    // ===== TABLE =====
    if (data.type === "table") {
      latestTableData = data;
      renderTable(
        {
          columns: data.columns,
          rows: data.rows,
        },
        aiMsg
      );

      if (data.summary) {
        const summary =
          document.createElement("p");

        summary.className =
          "ai-summary";

        summary.innerText =
          data.summary;

        aiMsg.appendChild(summary);
      }
            contentToSave = JSON.stringify({
        type: "table",
        columns: data.columns,
        rows: data.rows,
        summary: data.summary,
      });
    }

    // ===== CHART =====
    else if (data.type === "chart") {
      const canvas =
        document.createElement("canvas");

      canvas.width = 600;
      canvas.height = 300;

      aiMsg.appendChild(canvas);

      new Chart(
        canvas.getContext("2d"),
        {
          type: data.chart_type,

          data: {
            labels: data.labels,

            datasets: [
              {
                label: "Analytics",

                data: data.values,

                borderWidth: 2,

                backgroundColor: [
                  "rgba(251, 255, 197, 0.75)",
                  "rgba(0,229,255,0.75)",
                  "rgba(255, 185, 209, 0.75)",
                  "rgba(255, 225, 186, 0.75)",
                  "rgba(203, 255, 225, 0.75)",
                ],

                tension: 0.4,

                fill: true,
              },
            ],
          },

          options: {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
              legend: {
                labels: {
                  color: "white",
                },
              },
            },
          },
        }
      );

      if (data.summary) {
        const summary =
          document.createElement("p");

        summary.className =
          "ai-summary";

        summary.innerText =
          data.summary;

        aiMsg.appendChild(summary);
      }

      contentToSave =
        JSON.stringify({
          type: "chart",
          chart_type: data.chart_type,
          labels: data.labels,
          values: data.values,
          summary: data.summary,
        });
    }

    // ===== TEXT =====
    else {
      const responseText =
        data.answer ||
        data.summary ||
        "No response generated";

      latestResponseText = responseText;
      aiMsg.innerText = responseText;

      contentToSave =
        JSON.stringify({
          type: "text",
          answer: responseText,
        });
    }
    // ===== ACTION BUTTONS =====

    if (
      data.type === "chart" ||
      data.type === "table" ||
      data.type === "dashboard"
    ) {

      const actions =
        document.createElement("div");

      actions.className =
        "ai-actions";

      actions.innerHTML = `
        <button onclick="downloadChart(this)">
          Copy
        </button>
      `;

      aiMsg.appendChild(actions);
    }

    chatBox.appendChild(aiMsg);

    // ===== SAVE AI MESSAGE =====
    await fetch(
      "http://127.0.0.1:8000/chat/message",
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          chat_id: currentChatId,
          role: "ai",
          content: contentToSave,
        }),
      }
    );

    // ===== CLEAR INPUT =====
    input.value = "";

    chatBox.scrollTop =
      chatBox.scrollHeight;
  } catch (err) {

    console.error(err);

    alert("Query failed");

  } finally {

    isProcessing = false;
  }
}

// ===== ENTER KEY =====
const questionInput =
  document.getElementById(
    "questionInput"
  );

if (questionInput) {

  questionInput.addEventListener(
    "keydown",
    (e) => {

      if (e.key === "Enter") {

        e.preventDefault();

        if (
          questionInput.value.trim()
        ) {

          askQuestion();
        }
      }
    }
  );
}

// ===== SEND BUTTON =====
const sendBtn =
  document.getElementById("sendBtn");

if (sendBtn) {
  sendBtn.onclick = askQuestion;
}

// ===== GET FILE =====
function getFileForCurrentChat() {
  return uploadedFilePath;
}

// ===== TABLE RENDER =====
function renderTable(
  tableData,
  container
) {
  const wrapper =
    document.createElement("div");

  wrapper.className =
    "table-wrapper";

  const table =
    document.createElement("table");
  table.className = "data-table";

  const thead =
    document.createElement("thead");

  const tbody =
    document.createElement("tbody");
      // ===== HEADERS =====
  const headerRow =
    document.createElement("tr");

  tableData.columns.forEach((col) => {
    const th =
      document.createElement("th");

    th.innerText = col;

    headerRow.appendChild(th);
  });

  thead.appendChild(headerRow);

  // ===== ROWS =====
  tableData.rows.forEach((row) => {
    const tr =
      document.createElement("tr");

    row.forEach((cell) => {
      const td =
        document.createElement("td");

      td.innerText = cell;

      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });

  table.appendChild(thead);
  table.appendChild(tbody);

  wrapper.appendChild(table);

  container.appendChild(wrapper);
}

// ===== LOGOUT =====
function logout() {
  localStorage.removeItem("token");

  localStorage.removeItem(
    "currentChatId"
  );

  localStorage.removeItem(
    "filePath"
  );

  window.location.href =
    "index.html";
}

// ===== EXPORT EXCEL =====
const exportExcelBtn =
  document.getElementById(
    "exportExcelBtn"
  );

if (exportExcelBtn) {
  exportExcelBtn.onclick =
    async () => {
      try {
        if (!latestTableData) {
          alert("No report to export");
          return;
        }

        const res = await fetch(
          "http://127.0.0.1:8000/export/excel",
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              data: latestTableData.rows,
              summary: latestQuestion
            })
          }
        );

        const result =
          await res.json();

        const data =
        document.getElementById(
          "dashboardContainer"
        )

        window.open(
          "http://127.0.0.1:8000/" +
            result.file
        );

        showToast(
          "Excel export completed"
        );
      } catch (err) {
        console.error(err);

        alert("Excel export failed");
      }
    };
}

// ===== EXPORT PDF =====
const exportPdfBtn =
  document.getElementById(
    "exportPdfBtn"
  );

if (exportPdfBtn) {
  exportPdfBtn.onclick =
    async () => {
      try {
        if (!latestDashboardData) {
          alert("No report to export");
          return;
        }

        const res = await fetch(
          "http://127.0.0.1:8000/export/pdf",
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              data: latestDashboardData.kpis,
              summary: "Dashboard Analytics Report"
            }),
          }
        );

        const result =
          await res.json();

        window.open(
          "http://127.0.0.1:8000/" +
            result.file
        );

        showToast(
          "Export completed"
        );
      } catch (err) {
        console.error(err);

        alert("PDF export failed");
      }
    };
}

// ===== EXPORT PPT =====
const exportPptBtn =
  document.getElementById(
    "exportPptBtn"
  );

if (exportPptBtn) {
  exportPptBtn.onclick =
    async () => {
      try {
        if (!latestAIResponse) {
          alert("No report to export");
          return;
        }

        const res = await fetch(
          "http://127.0.0.1:8000/export/ppt",
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              data: [
                {
                  Question: latestQuestion,
                  Response: latestResponseText
                }
              ],
              summary: "AI Analytics Presentation"
            }),
          }
        );

        const result =
          await res.json();

        window.open(
          "http://127.0.0.1:8000/" +
            result.file
        );
      } catch (err) {
        console.error(err);

        alert("PPT export failed");
      }
    };
}
// ===== DOWNLOAD MENU =====
const downloadBtn =
  document.getElementById(
    "downloadBtn"
  );

const downloadMenu =
  document.getElementById(
    "downloadMenu"
  );

if (downloadBtn && downloadMenu) {
  downloadBtn.onclick = () => {
    downloadMenu.classList.toggle(
      "show"
    );
  };

  // ===== CLOSE MENU =====
  document.addEventListener(
    "click",
    (e) => {
      if (
        !downloadBtn.contains(
          e.target
        ) &&
        !downloadMenu.contains(
          e.target
        )
      ) {
        downloadMenu.classList.remove(
          "show"
        );
      }
    }
  );
}

// ===== THEME TOGGLE =====
window.toggleTheme =
  function () {
    document.body.classList.toggle(
      "light-mode"
    );

    const isLight =
      document.body.classList.contains(
        "light-mode"
      );

    localStorage.setItem(
      "theme",
      isLight ? "light" : "dark"
    );

    const logo =
      document.getElementById(
        "logoImage"
      );
  };

// ===== LOAD SAVED THEME =====
document.addEventListener(
  "DOMContentLoaded",
  () => {
    const savedTheme =
      localStorage.getItem("theme");

    if (savedTheme === "light") {
      const logo =
        document.getElementById(
          "logoImage"
        );

      if (logo) {
        logo.src =
          "images/logo-black.png";
      }

      document.body.classList.add(
        "light-mode"
      );
    }
  }
);

// ===== CLEAR HISTORY =====
const clearBtn =
  document.getElementById(
    "clearHistoryBtn"
  );

if (clearBtn) {
  clearBtn.onclick =
    async () => {
      const confirmDelete =
        confirm(
          "Clear all chat history?"
        );

      if (!confirmDelete) return;

      const token =
        localStorage.getItem("token");

      await fetch(
        "http://127.0.0.1:8000/chat/clear",
        {
          method: "DELETE",

          headers: {
            Authorization:
              "Bearer " + token,
          },
        }
      );

      localStorage.removeItem(
        "currentChatId"
      );

      const chatBox =
        document.getElementById(
          "chatBox"
        );

      if (chatBox) {
        chatBox.innerHTML = "";
      }

      loadChats();
    };
}

// ===== HISTORY TOGGLE =====
const historyHeader =
  document.querySelector(
    ".history p"
  );

const chatList =
  document.querySelector(
    ".chat-list"
  );

if (historyHeader && chatList) {
  historyHeader.onclick = () => {
    if (
      chatList.style.display ===
      "none"
    ) {
      chatList.style.display =
        "flex";
    } else {
      chatList.style.display =
        "none";
    }
  };
}

// ===== TYPE EFFECT =====
function typeText(
  element,
  text
) {
  let index = 0;

  element.innerText = "";

  const interval =
    setInterval(() => {
      element.innerText +=
        text[index];

      index++;

      if (index >= text.length) {
        clearInterval(interval);
      }
    }, 12);
}

// ===== TOAST =====
function showToast(message) {
  const toast =
    document.getElementById(
      "toast"
    );

  if (!toast) return;

  toast.innerText = message;

  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove(
      "show"
    );
  }, 2500);
}
// ===== SUGGESTION CLICK =====
window.useSuggestion =
  function (button) {
    const input =
      document.getElementById(
        "questionInput"
      );

    if (!input) return;

    input.value =
      button.innerText;

    input.focus();
  };

// ===== DRAG & DROP =====
document.addEventListener(
  "dragover",
  (e) => {
    e.preventDefault();

    document.body.classList.add(
      "drag-active"
    );
  }
);

document.addEventListener(
  "dragleave",
  () => {
    document.body.classList.remove(
      "drag-active"
    );
  }
);

document.addEventListener(
  "drop",
  async (e) => {
    e.preventDefault();

    document.body.classList.remove(
      "drag-active"
    );

    const files =
      e.dataTransfer.files;

    if (!files.length) return;

    const fileInput =
      document.getElementById(
        "fileInput"
      );

    fileInput.files = files;

    await handleFileUpload({
      target: fileInput,
    });
  }
);

// ===== COPY CHART =====
window.downloadChart =
  async function (button) {
    const container =
      button.closest(".msg-ai");

    const canvas =
      container.querySelector(
        "canvas"
      );

    // ===== COPY CHART IMAGE =====
    if (canvas) {
      canvas.toBlob(
        async (blob) => {
          try {
            await navigator.clipboard.write(
              [
                new ClipboardItem({
                  "image/png":
                    blob,
                }),
              ]
            );

            showToast(
              "Chart copied"
            );
          } catch (err) {
            console.error(err);

            showToast(
              "Copy failed"
            );
          }
        }
      );
    }

    // ===== COPY TEXT =====
    else {
      const text =
        button.getAttribute(
          "data-text"
        );

      navigator.clipboard.writeText(
        text
      );

      showToast("Copied");
    }
  };

// ===== GENERATE DASHBOARD =====
async function generateDashboard() {
  console.log("Dashboard started");
  try {
    const token =
      localStorage.getItem(
        "token"
      );

    const fileToUse =
      getFileForCurrentChat();

    if (!fileToUse) {
      alert(
        "Upload dataset first"
      );

      return;
    }

    const res = await fetch(
      `http://127.0.0.1:8000/generate-dashboard?file_path=${encodeURIComponent(
        fileToUse
      )}`,
      {
        headers: {
          Authorization:
            "Bearer " + token,
        },
      }
    );

    const data =
      await res.json();
      latestDashboardData = data;

    latestAIResponse = {
      type: "dashboard",
      data: data
    };
      
      if (!data.kpis) {
        showToast("Dashboard data invalid");
        return;
      }

    const container =
      document.getElementById(
        "dashboardContainer"
      );

    container.innerHTML = "";

    const emptyState =
      document.getElementById(
        "emptyState"
      );

    if (emptyState) {
      emptyState.style.display = "none";
    }

    container.style.display = "grid";
    // ===== KPI CARDS =====
    data.kpis.forEach((kpi) => {
      const card =
        document.createElement(
          "div"
        );

      card.className =
        "dashboard-card";

      card.innerHTML = `
        <h3>${kpi.title}</h3>

        <div class="kpi-value">
          ${kpi.value}
        </div>
      `;

      container.appendChild(card);
    });
        // ===== CHARTS =====
    data.charts.forEach((chart) => {

  try {

    const card =
      document.createElement("div");

    card.className =
      "dashboard-card";

    // WHITE CARD
    card.style.background = "white";

    const title =
      document.createElement("h3");

    title.innerText =
      chart.title;

    title.style.color = "#111";

    card.appendChild(title);

    const canvas =
      document.createElement("canvas");

    canvas.height = 250;

    card.appendChild(canvas);

    container.appendChild(card);

    new Chart(
      canvas.getContext("2d"),
      {
        type:
          chart.chart_type || "bar",

        data: {

          labels:
            chart.labels || [],

          datasets: [
            {
              label:
                chart.title || "Analytics",

              data:
                chart.values || [],

              borderWidth: 2,

              backgroundColor: [
                "#7c4dff",
                "#00e5ff",
                "#ff4081",
                "#ffab40",
                "#00c853",
              ],

              borderColor:
                "#7c4dff",

              tension: 0.4,

              fill: true,
            },
          ],
        },

        options: {
          responsive: true,

          maintainAspectRatio: false,

          plugins: {
            legend: {
              labels: {
                color: "#111",
              },
            },
          },

          scales: {
            x: {
              ticks: {
                color: "#111",
              },
            },

            y: {
              ticks: {
                color: "#111",
              },
            },
          },
        },
      }
    );

  } catch (err) {

    console.error(
      "Dashboard chart failed:",
      err
    );

  }

  });

// ===== INSIGHTS =====
const insightCard =
  document.createElement(
    "div"
  );

insightCard.className =
  "dashboard-card";

insightCard.style.background =
  "white";

insightCard.innerHTML = `
  <h3 style="color:#111;">
    AI Insights
  </h3>

  <div class="insight-list">

    ${(data.insights || [])
      .map(
        (i) =>
          `<div class="insight-item" style="color:#111;">${i}</div>`
      )
      .join("")}

  </div>
`;

container.appendChild(
  insightCard
);

showToast(
  "Dashboard generated"
);

} catch (err) {

  console.error(err);

  alert(err.message);

  showToast(
    "Dashboard failed"
  );

}
}