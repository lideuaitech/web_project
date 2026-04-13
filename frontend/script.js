document.addEventListener("DOMContentLoaded", () => {

  // ===== CARD FLIP =====
  const card = document.getElementById("card");

  if (card) {
    const registerTab = document.querySelector(".register");
    const loginTab = document.querySelector(".login");

    if (registerTab) {
      registerTab.onclick = () => {
        card.classList.add("flip");
      };
    }

    if (loginTab) {
      loginTab.onclick = () => {
        card.classList.remove("flip");
      };
    }
  }


  // ===== REGISTER =====
  const registerBtn = document.getElementById("registerBtn");

  if (registerBtn) {
    registerBtn.onclick = async () => {

      const name = document.getElementById("regName").value.trim();
      const email = document.getElementById("regEmail").value.trim();
      const password = document.getElementById("regPassword").value;
      const confirm = document.getElementById("confirmPassword").value;

      if (!name) {
        alert("Enter username");
        return;
      }

      if (!email || !password || !confirm) {
        alert("Please fill all fields");
        return;
      }

      if (password !== confirm) {
        alert("Passwords do not match");
        return;
      }

      try {
        const res = await fetch("http://127.0.0.1:8000/signup", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            email,
            password,
            name
          })
        });

        const data = await res.json();

        if (res.ok) {
          alert("✅ Registered successfully");
          if (card) card.classList.remove("flip");
        } else {
          alert(data.detail || "Registration failed");
        }

      } catch (err) {
        console.log(err);
        alert("Server error");
      }
    };
  }


  // ===== LOGIN =====
  const loginBtn = document.getElementById("loginBtn");

  if (loginBtn) {
    loginBtn.onclick = async () => {

      const email = document.getElementById("loginEmail").value.trim();
      const password = document.getElementById("loginPassword").value;

      if (!email || !password) {
        alert("Enter email & password");
        return;
      }

      try {
        const res = await fetch("http://127.0.0.1:8000/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            email,
            password
          })
        });

        const data = await res.json();

        if (res.ok && data.access_token) {

          // SAVE TOKEN
          localStorage.setItem("token", data.access_token);

          window.location.href = "dashboard.html";

        } else {
          alert(data.detail || "Login failed");
        }

      } catch (err) {
        console.log(err);
        alert("Server error");
      }
    };
  }


  // ===== DASHBOARD AUTH =====
  if (window.location.pathname.includes("dashboard")) {

    const token = localStorage.getItem("token");

    if (!token) {
      alert("Please login first");
      window.location.href = "login.html";
      return;
    }

    fetch("http://127.0.0.1:8000/dashboard", {
      method: "GET",
      headers: {
        "Authorization": "Bearer " + token
      }
    })
    .then(res => {
      if (!res.ok) throw new Error("Unauthorized");
      return res.json();
    })
    .then(data => {
      const heading = document.querySelector("h2");
      if (heading && data.message) {
        heading.innerText = data.message;
      }
    })
    .catch(() => {
      alert("Session expired. Please login again.");
      localStorage.removeItem("token");
      window.location.href = "login.html";
    });
  }


  // ===== LOGOUT =====
  window.logout = function () {
    localStorage.removeItem("token");
    window.location.href = "login.html";
  };


  // ===== FILE UPLOAD =====
  window.openFile = function () {
    const fileInput = document.getElementById("fileInput");
    if (fileInput) fileInput.click();
  };

  document.addEventListener("change", (e) => {
    if (e.target.id === "fileInput") {
      const file = e.target.files[0];
      if (file) {
        alert("File selected: " + file.name);
      }
    }
  });


  // ===== DARK MODE =====
  const toggle = document.getElementById("brightnessToggle");
  const overlay = document.getElementById("overlay");

  if (toggle && overlay) {
    let darkMode = localStorage.getItem("darkMode") === "true";

    if (darkMode) {
      overlay.style.opacity = "0.4";
      toggle.classList.add("active");
    }

    toggle.onclick = () => {
      darkMode = !darkMode;

      toggle.classList.toggle("active");
      overlay.style.opacity = darkMode ? "0.4" : "0";

      localStorage.setItem("darkMode", darkMode);
    };
  }


  // ===== ICONS =====
  if (window.lucide) {
    lucide.createIcons();
  }

});