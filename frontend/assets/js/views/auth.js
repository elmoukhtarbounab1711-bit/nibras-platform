// نبراس — نافذتا الدخول والتسجيل (Modal)
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

function formField(label, input) {
  return el("div", { class: "field" }, [el("label", { text: label }), input]);
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

  const submit = el("button", { class: "btn btn-primary btn-block", type: "submit" },
    isLogin ? tr("login") : tr("register"));

  const switchBtn = el("button", { class: "btn btn-ghost btn-block" },
    isLogin ? tr("orRegister") : tr("orLogin"));

  const form = el("form", {}, [
    el("h2", { text: heading }),
    el("p", { class: "muted small mb-16", text: sub }),
    formField(tr("fullName"), fullName),
    formField(tr("email"), email),
    formField(tr("password"), pass),
    ...(isLogin ? [] : [formField(tr("confirmPassword"), confirmPass), formField(tr("role"), roleSel)]),
    errorBox,
    submit,
    el("hr", { class: "divider" }),
    switchBtn,
  ]);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    submit.disabled = true;
    errorBox.textContent = "";
    try {
      const payload = {
        email: email.value.trim(),
        password: pass.value,
        full_name: isLogin ? undefined : fullName.value.trim(),
        role: isLogin ? undefined : roleSel.value,
      };
      const data = await api.post(isLogin ? "/api/auth/login" : "/api/auth/register", payload);
      session.token = data.access_token;
      session.refresh = data.refresh_token;
      session.user = data.user;
      closeModal();
      document.dispatchEvent(new CustomEvent("nibras:auth"));
      toast(isLogin ? tr("welcomeBack") : "تم إنشاء حسابك بنجاح", "success");
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
