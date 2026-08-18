// نبراس — إدارة مكتبة الباحث (لوحة الإدارة): قائمة + إضافة/تعديل/حذف + رفع ملفات
import {
  el, api, t, head, panel, body, badge, confirmDialog,
  openModal, closeModal, toast, emptyState, skeleton,
  input, select, field, kpi,
} from "../ui.js";
import { session } from "../../api.js";

const BOOK_TYPES = [
  ["thesis", "أطروحة دكتوراه"], ["dissertation", "رسالة ماستر"],
  ["book", "كتاب"], ["article", "بحث علمي"], ["research", "بحث"],
];

const LEGAL_CATEGORIES = [
  ["civil", "المدني"], ["criminal", "الجنائي"], ["labor", "الشغل"],
  ["personal_status", "الأحوال الشخصية"], ["administrative", "الإداري"],
  ["constitutional", "الدستوري"], ["commercial", "التجاري"], ["general", "عام"],
];

export function researchAdminView() {
  const container = el("div", { class: "flex-col", style: "gap:16px" });

  const statsRow = el("div", { class: "adm-kpi-row" });
  const tbody = el("tbody", {});
  const searchIn = input({ placeholder: t("search") });
  const catFilter = select({}, [
    el("option", { value: "", text: "الكل" }),
    ...LEGAL_CATEGORIES.map(([k, v]) => el("option", { value: k, text: v })),
  ]);
  const typeFilter = select({}, [
    el("option", { value: "", text: "الكل" }),
    ...BOOK_TYPES.map(([k, v]) => el("option", { value: k, text: v })),
  ]);

  async function loadStats() {
    try {
      const s = await api.get("/api/research/stats");
      statsRow.replaceChildren(
        kpi({ icon: "book", label: t("researchBookCount") || "كتاب", value: s.total || 0, tone: "gold" }),
        kpi({ icon: "layers", label: "بالتصنيف", value: Object.keys(s.by_category || {}).length, tone: "info" }),
        kpi({ icon: "tag", label: "بالنوع", value: Object.keys(s.by_type || {}).length, tone: "green" }),
      );
    } catch (e) { /* ignore */ }
  }

  async function draw() {
    tbody.replaceChildren(el("tr", {}, el("td", { colspan: 8 }, skeleton(2, 60))));
    const params = new URLSearchParams();
    if (searchIn.value.trim()) params.set("q", searchIn.value.trim());
    if (catFilter.value) params.set("category", catFilter.value);
    if (typeFilter.value) params.set("type", typeFilter.value);

    let data = { books: [], total: 0 };
    try { data = await api.get(`/api/admin/research/books?${params.toString()}`); }
    catch (e) { data = { books: [], total: 0 }; }

    const books = data.books || [];
    tbody.replaceChildren(books.length
      ? books.map((b) => el("tr", {}, [
          el("td", { text: `#${b.id}` }),
          el("td", {}, [
            el("div", { class: "flex", style: "gap:8px;align-items:center" }, [
              b.cover_image
                ? el("img", { src: `/api/research/books/${b.id}/cover`, style: "width:40px;height:56px;object-fit:cover;border-radius:4px" })
                : el("div", { style: "width:40px;height:56px;background:var(--surface-2,#f3f4f6);border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:11px;color:var(--ink-3,#999)", text: "PDF" }),
              el("strong", { text: b.title || "—" }),
            ]),
          ]),
          el("td", { text: b.author || "—" }),
          el("td", { text: getBookTypeLabel(b.book_type) }),
          el("td", { text: getCatLabel(b.legal_category) }),
          el("td", { text: b.year ? String(b.year) : "—" }),
          el("td", { text: b.file_name || (b.file_path ? "مرفق" : "—") }),
          el("td", {}, [
            el("div", { class: "flex", style: "gap:6px" }, [
              el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => bookModal(b, draw) }),
              el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
                if (!(await confirmDialog({ title: t("deleteConfirm"), text: b.title }))) return;
                try { await api.del(`/api/admin/research/books/${b.id}`); toast(t("deleted"), "success"); draw(); }
                catch (e) { toast(e.message, "error"); }
              } }),
            ]),
          ]),
        ]))
      : [el("tr", {}, el("td", { colspan: 8 }, emptyState(t("empty") || "لا نتائج")))]
    );
  }

  const toolbar = el("div", { class: "flex", style: "gap:8px;align-items:center;flex-wrap:wrap" }, [
    searchIn, catFilter, typeFilter,
    el("button", { class: "btn btn-ghost btn-sm", text: "بحث", onclick: draw }),
    el("button", {
      class: "btn btn-primary btn-sm", text: t("researchAddBook") || "إضافة كتاب",
      style: "margin-inline-start:auto",
      onclick: () => bookModal(null, draw),
    }),
  ]);

  const table = el("div", { class: "adm-tbl-wrap" }, [
    el("table", { class: "adm-tbl" }, [
      el("thead", {}, el("tr", {}, [
        el("th", { text: "#" }),
        el("th", { text: t("researchTitle") || "العنوان" }),
        el("th", { text: t("researchAuthor") || "المؤلف" }),
        el("th", { text: t("researchBookType") || "النوع" }),
        el("th", { text: t("researchLegalCategory") || "التصنيف" }),
        el("th", { text: t("researchYear") || "السنة" }),
        el("th", { text: "الملف" }),
        el("th", { text: t("actions") || "إجراءات" }),
      ])),
      tbody,
    ]),
  ]);

  container.replaceChildren(
    head(t("researchLibrary") || "مكتبة الباحث"),
    panel([statsRow, toolbar, body([table])]),
  );
  loadStats();
  draw();
  return container;
}

function getBookTypeLabel(key) {
  return BOOK_TYPES.find(([k]) => k === key)?.[1] || key;
}

function getCatLabel(key) {
  return LEGAL_CATEGORIES.find(([k]) => k === key)?.[1] || key;
}

function bookModal(book, onDone) {
  const isEdit = !!book;

  const titleIn = input({ value: book?.title || "", placeholder: "عنوان الكتاب" });
  const authorIn = input({ value: book?.author || "", placeholder: "المؤلف" });
  const typeIn = select({ value: book?.book_type || "book" }, BOOK_TYPES.map(([k, v]) => el("option", { value: k, text: v })));
  const catIn = select({ value: book?.legal_category || "general" }, LEGAL_CATEGORIES.map(([k, v]) => el("option", { value: k, text: v })));
  const yearIn = input({ value: book?.year || "", placeholder: "2024", type: "number" });
  const pagesIn = input({ value: book?.pages || "", placeholder: "عدد الصفحات", type: "number" });
  const langIn = select({ value: book?.language || "ar" }, [["ar", "عربية"], ["en", "إنجليزية"], ["fr", "فرنسية"]].map(([k, v]) => el("option", { value: k, text: v })));
  const descIn = el("textarea", { rows: 3, placeholder: "وصف الكتاب...", text: book?.description || "" });
  const sourceIn = input({ value: book?.source_name || "", placeholder: "مثال: جامعة القاهرة" });
  const sourceUrlIn = input({ value: book?.source_url || "", placeholder: "https://..." });

  // عناصر الرفع
  const coverPreview = el("div", { id: "cover-preview", style: "margin-bottom:8px" }, [
    book?.cover_image
      ? el("img", { src: `/api/research/books/${book.id}/cover`, style: "width:120px;height:170px;object-fit:cover;border-radius:8px;border:2px solid var(--line,#e5e7eb)" })
      : null,
  ]);
  const coverInput = el("input", {
    type: "file",
    accept: "image/jpeg,image/png,image/webp",
    class: "input",
    style: "font-size:0.85rem",
  });
  const coverHint = el("div", { class: "text-muted", style: "font-size:0.75rem;margin-top:4px", text: "PNG/JPG — حد أقصى 5 MB" });

  const fileInfo = el("div", { style: "margin-bottom:8px" }, [
    book?.file_name
      ? el("div", { class: "flex", style: "gap:6px;align-items:center;font-size:0.85rem" }, [
          el("span", { class: "badge-pill badge-green", text: "مرفق" }),
          el("span", { text: book.file_name }),
        ])
      : book?.source_url
        ? el("div", { class: "text-muted", style: "font-size:0.85rem" }, [
            el("span", { text: "رابط المصدر: " }),
            el("a", { href: book.source_url, target: "_blank", text: book.source_name || "رابط" }),
          ])
        : null,
  ]);
  const fileInput = el("input", {
    type: "file",
    accept: ".pdf",
    class: "input",
    style: "font-size:0.85rem",
  });
  const fileHint = el("div", { class: "text-muted", style: "font-size:0.75rem;margin-top:4px", text: "PDF فقط — حد أقصى 50 MB" });

  const form = el("form", { class: "flex-col", style: "gap:14px" });

  // قسم المعلومات الأساسية
  form.append(
    el("div", { class: "text-muted", style: "font-weight:700;border-bottom:1px solid var(--line,#e5e7eb);padding-bottom:6px;margin-top:4px", text: "المعلومات الأساسية" }),
    field("العنوان *", titleIn),
    field("المؤلف", authorIn),
    el("div", { class: "flex", style: "gap:12px" }, [
      field("النوع", typeIn),
      field("التصنيف القانوني", catIn),
    ]),
    el("div", { class: "flex", style: "gap:12px" }, [
      field("السنة", yearIn),
      field("اللغة", langIn),
      field("الصفحات", pagesIn),
    ]),
    field("الوصف", descIn),
    el("div", { class: "flex", style: "gap:12px" }, [
      field("المصدر", sourceIn),
      field("رابط المصدر", sourceUrlIn),
    ]),
  );

  // قسم الصورة والملف
  form.append(
    el("div", { class: "text-muted", style: "font-weight:700;border-bottom:1px solid var(--line,#e5e7eb);padding-bottom:6px;margin-top:8px", text: "المرفقات" }),
    field("صورة الغلاف", el("div", {}, [coverPreview, coverInput, coverHint])),
    field("ملف الكتاب (PDF)", el("div", {}, [fileInfo, fileInput, fileHint])),
  );

  openModal(el("div", {}, [
    el("h2", { text: isEdit ? t("researchEditBook") : t("researchAddBook") }),
    form,
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
      const title = titleIn.value.trim();
      if (!title) { toast("العنوان مطلوب", "error"); return; }

      let coverPath = book?.cover_image || null;
      let filePath = book?.file_path || null;
      let fileName = book?.file_name || null;
      let fileSize = book?.file_size || null;

      // رفع صورة الغلاف
      if (coverInput.files.length > 0) {
        try {
          const fd = new FormData();
          fd.append("file", coverInput.files[0]);
          fd.append("kind", "cover");
          const res = await fetch("/api/admin/research/upload", {
            method: "POST",
            headers: { Authorization: `Bearer ${session.token}` },
            body: fd,
          });
          const json = await res.json();
          if (!res.ok) { toast(json.error || "فشل رفع الصورة", "error"); return; }
          coverPath = json.path;
        } catch (e) { toast("خطأ في رفع الصورة", "error"); return; }
      }

      // رفع ملف الكتاب
      if (fileInput.files.length > 0) {
        try {
          const fd = new FormData();
          fd.append("file", fileInput.files[0]);
          fd.append("kind", "book");
          const res = await fetch("/api/admin/research/upload", {
            method: "POST",
            headers: { Authorization: `Bearer ${session.token}` },
            body: fd,
          });
          const json = await res.json();
          if (!res.ok) { toast(json.error || "فشل رفع الملف", "error"); return; }
          filePath = json.path;
          fileName = fileInput.files[0].name;
          fileSize = fileInput.files[0].size;
        } catch (e) { toast("خطأ في رفع الملف", "error"); return; }
      }

      const data = {
        title,
        title_ar: null,
        author: authorIn.value.trim() || null,
        book_type: typeIn.value,
        legal_category: catIn.value,
        year: yearIn.value ? parseInt(yearIn.value) : null,
        pages: pagesIn.value ? parseInt(pagesIn.value) : null,
        language: langIn.value,
        description: descIn.value.trim() || null,
        source_name: sourceIn.value.trim() || null,
        source_url: sourceUrlIn.value.trim() || null,
        cover_image: coverPath,
        file_path: filePath,
        file_name: fileName,
        file_size: fileSize,
      };

      try {
        if (isEdit) {
          await api.put(`/api/admin/research/books/${book.id}`, data);
        } else {
          await api.post("/api/admin/research/books", data);
        }
        toast(t("saved") || "تم الحفظ", "success");
        closeModal();
        onDone();
      } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}
