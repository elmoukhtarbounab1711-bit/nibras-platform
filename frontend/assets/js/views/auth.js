// نبراس — نافذتا الدخول والتسجيل (Modal) — متوافقة مع القانون 09-08
import { tr } from "../i18n.js";
import { api, session, refreshToken } from "../api.js";
import { el, esc, toast, openModal, closeModal } from "../ui.js";

function roleOptions() {
  const roles = [
    ["citizen", "مواطن"],
    ["student", "طالب قانون"],
    ["lawyer", "محامٍ"],
    ["notary", "موثق"],
    ["adoul", "عدل"],
    ["judicial_commissioner", "مفوض قضائي"],
    ["sworn_translator", "مترجم محلف"],
    ["judicial_expert", "خبير قضائي"],
    ["company", "شركة"],
    ["institution", "مؤسسة"],
  ];
  return roles.map(([v, label]) => el("option", { value: v, text: label }));
}

function formField(label, input, hint) {
  const children = [el("label", { text: label }), input];
  if (hint) children.push(el("div", { class: "small muted", style: "margin-top:3px", text: hint }));
  return el("div", { class: "field" }, children);
}

function passwordStrengthBar() {
  const bar = el("div", {
    style: "height:4px;border-radius:2px;background:var(--line,#e5e7eb);margin-top:6px;overflow:hidden",
  }, [
    el("div", { id: "pw-strength-fill", style: "height:100%;width:0%;transition:width .3s,background .3s" }),
  ]);
  const label = el("span", { id: "pw-strength-label", class: "small muted", text: "" });
  return el("div", {}, [bar, label]);
}

function checkPasswordStrength(pw) {
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[a-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;

  const fill = document.getElementById("pw-strength-fill");
  const lbl = document.getElementById("pw-strength-label");
  if (!fill || !lbl) return;

  const pct = Math.min(100, (score / 6) * 100);
  fill.style.width = pct + "%";
  if (score <= 2) {
    fill.style.background = "var(--danger,#dc2626)";
    lbl.textContent = "ضعيفة";
    lbl.style.color = "var(--danger,#dc2626)";
  } else if (score <= 4) {
    fill.style.background = "var(--warning,#f59e0b)";
    lbl.textContent = "متوسطة";
    lbl.style.color = "var(--warning,#f59e0b)";
  } else {
    fill.style.background = "var(--success,#16a34a)";
    lbl.textContent = "قوية";
    lbl.style.color = "var(--success,#16a34a)";
  }
}

export function openAuth(mode = "login") {
  openModal(authForm(mode));
}

export function authForm(mode = "login") {
  const isLogin = mode === "login";
  const heading = isLogin ? tr("loginTitle") : tr("registerTitle");
  const sub = isLogin ? tr("welcomeBack") : tr("createAccount");

  const email = el("input", { type: "email", required: true, placeholder: "name@example.com", autocomplete: "email" });
  const pass = el("input", { type: "password", required: true, placeholder: "••••••••", autocomplete: isLogin ? "current-password" : "new-password" });
  const fullName = el("input", { type: "text", required: true, placeholder: "الاسم الكامل", autocomplete: "name" });
  const roleSel = el("select", { required: true }, roleOptions());
  const confirmPass = el("input", { type: "password", required: true, placeholder: "••••••••", autocomplete: "new-password" });
  const errorBox = el("div", { class: "small muted", role: "alert" });

  // القانون 09-08: مربعات الموافقة
  const consentProcessing = el("input", { type: "checkbox", id: "consent-processing", required: true });
  const consentTerms = el("input", { type: "checkbox", id: "consent-terms", required: true });

  // تحقق بخطوتين (TOTP)
  const totpInput = el("input", { type: "text", inputmode: "numeric", pattern: "[0-9]{6}", placeholder: "000000", autocomplete: "one-time-code" });
  let requires2fa = false;

  const submit = el("button", { class: "btn btn-primary btn-block", type: "submit" },
    isLogin ? tr("login") : tr("register"));

  const switchBtn = el("button", { class: "btn btn-ghost btn-block" },
    isLogin ? tr("orRegister") : tr("orLogin"));

  // رابط سياسة الخصوصية
  const privacyLink = el("a", {
    href: "#",
    class: "small",
    style: "color:var(--primary,#1f3a93);text-decoration:underline;cursor:pointer",
    text: "سياسة الخصوصية",
    onclick: async (e) => {
      e.preventDefault();
      try {
        const data = await api.get("/api/auth/privacy-policy");
        openModal(el("div", { class: "card", style: "padding:2rem;max-width:600px;max-height:80vh;overflow-y:auto" }, [
          el("h2", { text: data.title }),
          el("p", { class: "small muted mb-16", text: `${data.legal_basis} — ${data.regulator}` }),
          ...data.sections.map(s => el("div", { class: "mb-16" }, [
            el("h3", { style: "margin-bottom:4px", text: s.title }),
            el("p", { class: "small", text: s.content }),
          ])),
          el("button", { class: "btn btn-ghost btn-block", onclick: () => closeModal(), text: "إغلاق" }),
        ]));
      } catch { /* تجاهل */ }
    },
  });

  const children = [
    el("h2", { text: heading }),
    el("p", { class: "muted small mb-16", text: sub }),
  ];

  if (!isLogin) {
    children.push(formField(tr("fullName"), fullName));
  }
  children.push(formField(tr("email"), email));
  children.push(formField(tr("password"), pass));
  if (!isLogin) {
    children.push(passwordStrengthBar());
    children.push(formField(tr("confirmPassword"), confirmPass));
    children.push(formField(tr("role"), roleSel));
    // القانون 09-08: الموافقات
    children.push(el("div", { class: "mb-16" }, [
      el("label", { class: "small", style: "display:flex;align-items:flex-start;gap:8px;cursor:pointer" }, [
        consentProcessing,
        el("span", { text: "أوافق على معالجة معطياتي الشخصية وفق " }),
        privacyLink,
      ]),
    ]));
    children.push(el("div", { class: "mb-16" }, [
      el("label", { class: "small", style: "display:flex;align-items:flex-start;gap:8px;cursor:pointer" }, [
        consentTerms,
        el("span", { text: "أقر بقراءةشروط الاستخدام وموافقتي عليها" }),
      ]),
    ]));
  }

  // حقل TOTP (يظهر عند الحاجة)
  const totpField = formField("رمز التحقق (TOTP)", totpInput, "أدخل الرمز من تطبيق المصادقة");
  totpField.style.display = "none";
  totpField.id = "totp-field";
  children.push(totpField);

  children.push(errorBox);
  children.push(submit);
  children.push(el("hr", { class: "divider" }));
  children.push(switchBtn);

  const form = el("form", {}, children);

  // تأثير الكتابة على قوة كلمة المرور
  if (!isLogin) {
    pass.addEventListener("input", () => checkPasswordStrength(pass.value));
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    submit.disabled = true;
    errorBox.textContent = "";

    if (isLogin) {
      try {
        const payload = {
          email: email.value.trim(),
          password: pass.value,
        };
        if (requires2fa) {
          payload.totp_code = totpInput.value.trim();
        }

        const data = await api.post("/api/auth/login", payload);

        if (data.requires_2fa) {
          requires2fa = true;
          const tf = document.getElementById("totp-field");
          if (tf) tf.style.display = "block";
          totpInput.focus();
          errorBox.textContent = "أدخل رمز التحقق من تطبيق المصادقة";
          errorBox.className = "small";
          errorBox.style.color = "var(--warning,#f59e0b)";
          return;
        }

        session.token = data.access_token;
        session.refresh = data.refresh_token;
        session.user = data.user;
        closeModal();
        document.dispatchEvent(new CustomEvent("nibras:auth"));
        toast(tr("welcomeBack"), "success");
        if (session.isAdmin && !location.hash.includes("/admin")) {
          window.location.hash = "#/admin";
        }
      } catch (err) {
        errorBox.textContent = err.message;
        errorBox.className = "small";
        errorBox.style.color = "var(--danger)";
      } finally {
        submit.disabled = false;
      }
    } else {
      // التسجيل
      if (pass.value !== confirmPass.value) {
        errorBox.textContent = "كلمتا المرور غير متطابقتين";
        errorBox.className = "small";
        errorBox.style.color = "var(--danger)";
        submit.disabled = false;
        return;
      }
      if (!consentProcessing.checked || !consentTerms.checked) {
        errorBox.textContent = "يجب الموافقة على شروط المعالجة والاستخدام";
        errorBox.className = "small";
        errorBox.style.color = "var(--danger)";
        submit.disabled = false;
        return;
      }

      try {
        const data = await api.post("/api/auth/register", {
          email: email.value.trim(),
          password: pass.value,
          full_name: fullName.value.trim(),
          role: roleSel.value,
          consent_data_processing: consentProcessing.checked,
          consent_terms: consentTerms.checked,
        });
        session.token = data.access_token;
        session.refresh = data.refresh_token;
        session.user = data.user;
        closeModal();
        document.dispatchEvent(new CustomEvent("nibras:auth"));
        toast("تم إنشاء حسابك بنجاح", "success");
        if (session.isAdmin && !location.hash.includes("/admin")) {
          window.location.hash = "#/admin";
        }
      } catch (err) {
        errorBox.textContent = err.message;
        errorBox.className = "small";
        errorBox.style.color = "var(--danger)";
      } finally {
        submit.disabled = false;
      }
    }
  });

  switchBtn.addEventListener("click", () => {
    openModal(authForm(isLogin ? "register" : "login"));
  });

  return form;
}

export async function logout() {
  try {
    if (session.refresh) {
      await api.post("/api/auth/logout", { refresh_token: session.refresh });
    }
  } catch { /* تجاهل أخطاء الخروج */ }
  session.clear();
  document.dispatchEvent(new CustomEvent("nibras:auth"));
  if (location.hash.startsWith("#/admin") || location.hash.startsWith("#/profile")) {
    window.location.hash = "#/home";
  } else {
    window.location.hash = location.hash || "#/home";
  }
  toast("تم تسجيل الخروج.");
}
