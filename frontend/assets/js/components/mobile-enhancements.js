// نبراس — تحسينات تجربة الهاتف المتقدمة
// Pull-to-refresh, Swipe-back, Ripple, Scroll shadows, Auto-skeleton

export function initPullToRefresh(container, onRefresh) {
  if (!container || !onRefresh) return;
  let startY = 0;
  let pulling = false;
  let released = false;

  container.addEventListener("touchstart", (e) => {
    if (container.scrollTop === 0) {
      startY = e.touches[0].clientY;
      pulling = true;
      released = false;
    }
  }, { passive: true });

  container.addEventListener("touchmove", (e) => {
    if (!pulling || released) return;
    const delta = e.touches[0].clientY - startY;
    if (delta > 0) {
      e.preventDefault();
      const pullDistance = Math.min(delta * 0.5, 80);
      container.style.transform = `translateY(${pullDistance}px)`;
      container.classList.toggle("ptr-pulling", pullDistance > 20);
      container.classList.toggle("ptr-ready", pullDistance >= 60);
    }
  }, { passive: false });

  container.addEventListener("touchend", async () => {
    if (!pulling) return;
    pulling = false;
    released = true;
    const wasReady = container.classList.contains("ptr-ready");
    container.style.transform = "";
    container.classList.remove("ptr-pulling", "ptr-ready");
    if (wasReady) {
      container.classList.add("ptr-refreshing");
      try {
        await onRefresh();
      } finally {
        container.classList.remove("ptr-refreshing");
      }
    }
  });
}

export function initGlobalPullToRefresh() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (document.body.querySelector(".ptr-indicator")) return; // already initialized
  
  const body = document.body;
  // Insert PTR indicator at the top of the view
  const view = document.getElementById("view");
  if (!view) return;
  
  const ptrHtml = `<div class="ptr-indicator"><span class="ptr-spinner"></span>اسحب للتحديث</div>`;
  view.insertAdjacentHTML("afterbegin", ptrHtml);
  const indicator = view.querySelector(".ptr-indicator");
  
  let startY = 0;
  let pulling = false;
  let released = false;
  
  body.addEventListener("touchstart", (e) => {
    if (body.scrollTop === 0 && !pulling) {
      startY = e.touches[0].clientY;
      pulling = true;
      released = false;
    }
  }, { passive: true });

  body.addEventListener("touchmove", (e) => {
    if (!pulling || released) return;
    const delta = e.touches[0].clientY - startY;
    if (delta > 0 && body.scrollTop === 0) {
      e.preventDefault();
      const pullDistance = Math.min(delta * 0.5, 80);
      body.style.transform = `translateY(${pullDistance}px)`;
      indicator.style.transform = `translateY(${pullDistance}px)`;
      indicator.classList.toggle("ptr-pulling", pullDistance > 20);
      indicator.classList.toggle("ptr-ready", pullDistance >= 60);
    }
  }, { passive: false });

  body.addEventListener("touchend", async () => {
    if (!pulling) return;
    pulling = false;
    released = true;
    const wasReady = indicator.classList.contains("ptr-ready");
    body.style.transform = "";
    indicator.style.transform = "";
    indicator.classList.remove("ptr-pulling", "ptr-ready");
    if (wasReady) {
      indicator.classList.add("ptr-refreshing");
      indicator.innerHTML = '<span class="ptr-spinner"></span>جاري التحديث...';
      try {
        // Trigger reload of current route
        window.location.reload();
      } finally {
        indicator.classList.remove("ptr-refreshing");
        indicator.innerHTML = '<span class="ptr-spinner"></span>اسحب للتحديث';
      }
    }
  });
}

export function initSwipeBack(threshold = 80) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  let startX = 0;
  let swiping = false;
  const hint = document.querySelector(".swipe-back-hint");
  document.body.classList.toggle("swipe-back-active", !!hint);

  document.addEventListener("touchstart", (e) => {
    if (e.touches[0].clientX < 20 && window.location.hash !== "#/home" && window.location.hash !== "#/") {
      startX = e.touches[0].clientX;
      swiping = true;
    }
  }, { passive: true });

  document.addEventListener("touchmove", (e) => {
    if (!swiping) return;
    const delta = e.touches[0].clientX - startX;
    if (delta > 0) {
      document.body.style.transform = `translateX(${Math.min(delta * 0.3, 100)}px)`;
      if (hint) hint.style.opacity = Math.min(delta / threshold, 1);
    }
  }, { passive: false });

  document.addEventListener("touchend", () => {
    if (!swiping) return;
    swiping = false;
    const delta = (document.body.style.transform.match(/translateX\(([\d.]+)px\)/) || [0, 0])[1];
    document.body.style.transform = "";
    if (hint) hint.style.opacity = 0;
    if (delta >= threshold) {
      history.back();
    }
  });
}

export function initRipple() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  document.addEventListener("click", (e) => {
    const target = e.target.closest(".btn, .icon-btn, .chip, .app-tabbar a, .dropdown-toggle, .pagination a, .page-btn, .fab");
    if (!target) return;
    target.classList.add("ripple");
    target.addEventListener("transitionend", () => target.classList.remove("ripple"), { once: true });
  });
}

export function initScrollShadows() {
  document.querySelectorAll(".scroll-shadow").forEach((el) => {
    const update = () => {
      el.classList.toggle("scrolled-top", el.scrollTop > 0);
      el.classList.toggle("scrolled-bottom", el.scrollTop + el.clientHeight < el.scrollHeight - 1);
    };
    el.addEventListener("scroll", update, { passive: true });
    update();
  });
}

export function initAutoSkeleton() {
  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      for (const node of m.addedNodes) {
        if (node.nodeType === 1 && node.matches(".list-container, .grid-3, .grid-4, .grid-6")) {
          if (!node.querySelector(":scope > *")) {
            node.innerHTML = '<div class="flex-col"><div class="skeleton" style="height:80px"></div><div class="skeleton" style="height:80px"></div><div class="skeleton" style="height:80px"></div></div>';
          }
        }
      }
    }
  });
  observer.observe(document.getElementById("view"), { childList: true, subtree: true });
}

export function enhanceEmptyStates() {
  document.querySelectorAll(".empty").forEach((el) => {
    if (!el.querySelector(".empty-title")) {
      const msg = el.textContent.trim();
      el.innerHTML = `
        <div class="empty-icon" data-icon="inbox"></div>
        <div class="empty-title">${msg || "لا توجد بيانات"}</div>
      `;
    }
  });
}

export function initMobileEnhancements() {
  initRipple();
  initScrollShadows();
  initSwipeBack();
  initGlobalPullToRefresh();
  enhanceEmptyStates();
}

// Helper to create PTR indicator element
export function createPtrIndicator(text = "اسحب للتحديث") {
  return `<div class="ptr-indicator"><span class="ptr-spinner"></span>${text}</div>`;
}