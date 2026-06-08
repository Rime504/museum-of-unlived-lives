// Museum of Unlived Lives — frontend logic.
// Talks to the gr.Server /open_room API via the official Gradio JS client.
import { Client } from "https://esm.sh/@gradio/client@2.2.1";
// SnapDOM: pixel-accurate DOM→image incl. ::before/::after, CSS vars, web fonts, SVG.
import { snapdom } from "https://esm.sh/@zumer/snapdom@1";

// Card surface color behind the rounded card when exported to an image.
const CARD_EXPORT_BG = "#0e0c13";

const $ = (sel) => document.querySelector(sel);
const lineEl = $("#line");
const openBtn = $("#open");
const stage = $("#stage");
const countEl = $("#count");
const galleryEmpty = $("#galleryEmpty");
const galleryCarousel = $("#galleryCarousel");
const galleryHint = $("#galleryHint");
const carouselTrack = $("#carouselTrack");
const carouselViewport = $("#carouselViewport");
const carouselPrev = $("#carouselPrev");
const carouselNext = $("#carouselNext");
const carouselDots = $("#carouselDots");
const carouselCounter = $("#carouselCounter");

const STORE_KEY = "museum.rooms.v2";
const MAX_ROOMS = 12;

const DOWNLOAD_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14"/></svg>`;

/** Rooms opened this page session — first load shows curator warmup copy. */
let roomsOpenedThisSession = 0;
/** Room currently open in the lightbox (gallery history). */
let activeRoom = null;
/** Index in loadRooms() while lightbox is open. */
let lightboxIndex = 0;
/** Carousel position — explicit so last slide (12) is always reachable. */
let carouselIndex = 0;

// ---------- small helpers ----------
const escapeHtml = (s) =>
  (s || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const escapeAttr = (s) => escapeHtml(s).replace(/"/g, "&quot;");

const autoGrow = () => {
  lineEl.style.height = "auto";
  lineEl.style.height = lineEl.scrollHeight + "px";
};

// ---------- personal gallery (localStorage) ----------
function loadRooms() {
  try {
    return JSON.parse(localStorage.getItem(STORE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveRooms(rooms) {
  let list = rooms.slice(0, MAX_ROOMS);
  // On quota errors, drop the oldest rooms and retry so the newest always persists.
  while (list.length) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(list));
      return;
    } catch {
      list = list.slice(0, -1);
    }
  }
}

function getCarouselSlides() {
  return [...carouselTrack.querySelectorAll(".carousel-slide")];
}

function syncCarouselSpacers() {
  const slides = getCarouselSlides();
  const spacers = carouselTrack.querySelectorAll(".carousel-spacer");
  if (!slides.length || !spacers.length || !carouselViewport) return;
  const pad = Math.max(0, (carouselViewport.clientWidth - slides[0].offsetWidth) / 2);
  spacers.forEach((el) => {
    el.style.width = `${pad}px`;
    el.style.flexBasis = `${pad}px`;
  });
}

function slideScrollLeft(slide) {
  return slide.offsetLeft + slide.offsetWidth / 2 - carouselViewport.clientWidth / 2;
}

function getActiveSlideIndex() {
  const slides = getCarouselSlides();
  if (!slides.length) return 0;
  const center = carouselViewport.scrollLeft + carouselViewport.clientWidth / 2;
  let best = 0;
  let bestDist = Infinity;
  slides.forEach((slide, i) => {
    const slideCenter = slide.offsetLeft + slide.offsetWidth / 2;
    const dist = Math.abs(slideCenter - center);
    if (dist < bestDist) {
      bestDist = dist;
      best = i;
    }
  });
  return best;
}

function scrollToSlide(index, smooth = true) {
  const slides = getCarouselSlides();
  const total = slides.length;
  if (!total) return;

  carouselIndex = Math.max(0, Math.min(total - 1, index));
  const slide = slides[carouselIndex];
  const target = slideScrollLeft(slide);
  const maxScroll = Math.max(0, carouselViewport.scrollWidth - carouselViewport.clientWidth);

  carouselViewport.scrollTo({
    left: Math.min(maxScroll, Math.max(0, target)),
    behavior: smooth ? "smooth" : "instant",
  });
  requestAnimationFrame(updateCarouselUi);
}

function updateCarouselUi() {
  const slides = getCarouselSlides();
  const total = slides.length;
  if (!total) return;

  const active = carouselIndex;
  slides.forEach((slide, i) => slide.classList.toggle("is-active", i === active));

  carouselDots.querySelectorAll(".carousel-dot").forEach((dot, i) => {
    dot.classList.toggle("is-active", i === active);
    dot.setAttribute("aria-selected", i === active ? "true" : "false");
  });

  carouselCounter.textContent = `${active + 1} / ${total}`;
  carouselPrev.disabled = active <= 0;
  carouselNext.disabled = active >= total - 1;
}

let carouselScrollTimer = null;
function onCarouselScroll() {
  clearTimeout(carouselScrollTimer);
  carouselScrollTimer = setTimeout(() => {
    carouselIndex = getActiveSlideIndex();
    updateCarouselUi();
  }, 80);
}

function initCarousel() {
  carouselPrev?.addEventListener("click", () => scrollToSlide(carouselIndex - 1));
  carouselNext?.addEventListener("click", () => scrollToSlide(carouselIndex + 1));
  carouselViewport?.addEventListener("scroll", onCarouselScroll, { passive: true });

  carouselViewport?.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      scrollToSlide(carouselIndex - 1);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      scrollToSlide(carouselIndex + 1);
    }
  });

  new ResizeObserver(() => {
    syncCarouselSpacers();
    scrollToSlide(carouselIndex, false);
  }).observe(carouselViewport);
}

function renderGallery({ scrollToStart = false } = {}) {
  const rooms = loadRooms();
  countEl.textContent = rooms.length === 1 ? "1 room" : `${rooms.length} rooms`;

  if (!rooms.length) {
    galleryEmpty.hidden = false;
    galleryCarousel.hidden = true;
    galleryHint.hidden = true;
    carouselTrack.innerHTML = "";
    carouselDots.innerHTML = "";
    return;
  }

  galleryEmpty.hidden = true;
  galleryCarousel.hidden = false;
  galleryHint.hidden = rooms.length < 2;

  carouselTrack.innerHTML = "";
  carouselDots.innerHTML = "";

  const leadSpacer = document.createElement("div");
  leadSpacer.className = "carousel-spacer";
  leadSpacer.setAttribute("aria-hidden", "true");
  carouselTrack.appendChild(leadSpacer);

  rooms.forEach((room, i) => {
    const fig = document.createElement("figure");
    fig.className = "carousel-slide";
    fig.style.animationDelay = `${Math.min(i * 0.05, 0.35)}s`;
    fig.innerHTML = `
      <img src="${room.png}" alt="${escapeAttr(room.title)}" loading="lazy" draggable="false" />
      <figcaption>${escapeHtml(room.title)}</figcaption>`;
    fig.addEventListener("click", () => openLightbox(i));
    carouselTrack.appendChild(fig);

    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = "carousel-dot";
    dot.setAttribute("role", "tab");
    dot.setAttribute("aria-label", `Room ${i + 1}: ${room.title}`);
    dot.setAttribute("aria-selected", "false");
    dot.addEventListener("click", () => scrollToSlide(i));
    carouselDots.appendChild(dot);
  });

  const trailSpacer = document.createElement("div");
  trailSpacer.className = "carousel-spacer";
  trailSpacer.setAttribute("aria-hidden", "true");
  carouselTrack.appendChild(trailSpacer);

  requestAnimationFrame(() => {
    syncCarouselSpacers();
    if (scrollToStart) carouselIndex = 0;
    else carouselIndex = Math.min(carouselIndex, rooms.length - 1);
    scrollToSlide(carouselIndex, false);
  });
}

function pushRoom(room) {
  const rooms = loadRooms();
  rooms.unshift(room);
  saveRooms(rooms);
  renderGallery({ scrollToStart: true });
}

// ---------- lightbox ----------
const lb = $("#lightbox");
const lbBody = $("#lbBody");
const lbImg = $("#lbImg");
const lbActions = $("#lbActions");
const lbDownload = $("#lbDownload");
const lbPrev = $("#lbPrev");
const lbNext = $("#lbNext");
const lbCounter = $("#lbCounter");

function renderLightboxRoom(room) {
  if (room.card_html) {
    lbBody.hidden = false;
    lbBody.innerHTML = room.card_html;
    lbImg.hidden = true;
    lbImg.removeAttribute("src");
  } else {
    lbBody.hidden = true;
    lbBody.innerHTML = "";
    lbImg.hidden = false;
    lbImg.src = room.png;
  }
}

function updateLightboxNav() {
  const rooms = loadRooms();
  const total = rooms.length;
  const multi = total > 1;
  lbPrev.hidden = !multi;
  lbNext.hidden = !multi;
  lbPrev.disabled = lightboxIndex <= 0;
  lbNext.disabled = lightboxIndex >= total - 1;
  lbCounter.textContent = multi ? `${lightboxIndex + 1} / ${total}` : "";
}

function showLightboxRoom(index, { direction = 0 } = {}) {
  const rooms = loadRooms();
  if (!rooms.length) return;
  lightboxIndex = Math.max(0, Math.min(rooms.length - 1, index));
  activeRoom = rooms[lightboxIndex];
  carouselIndex = lightboxIndex;

  if (direction !== 0 && lbBody) {
    lbBody.classList.remove("lb-from-left", "lb-from-right");
    lbBody.classList.add(direction > 0 ? "lb-from-right" : "lb-from-left");
  }

  renderLightboxRoom(activeRoom);
  updateLightboxNav();
  scrollToSlide(lightboxIndex, true);
}

const openLightbox = (index) => {
  const rooms = loadRooms();
  if (!rooms.length) return;
  showLightboxRoom(typeof index === "number" ? index : 0, { direction: 0 });
  lbActions.hidden = false;
  lb.classList.add("open");
};

const navigateLightbox = (delta) => {
  if (!lb.classList.contains("open")) return;
  const rooms = loadRooms();
  const next = lightboxIndex + delta;
  if (next < 0 || next >= rooms.length) return;
  showLightboxRoom(next, { direction: delta });
};

const closeLightbox = () => {
  activeRoom = null;
  lb.classList.remove("open");
  lbBody.innerHTML = "";
  lbBody.hidden = true;
  lbBody.classList.remove("lb-from-left", "lb-from-right");
  lbImg.hidden = true;
  lbImg.removeAttribute("src");
  lbActions.hidden = true;
  scrollToSlide(lightboxIndex, true);
};

$("#lbClose").addEventListener("click", closeLightbox);
lbPrev?.addEventListener("click", (e) => {
  e.stopPropagation();
  navigateLightbox(-1);
});
lbNext?.addEventListener("click", (e) => {
  e.stopPropagation();
  navigateLightbox(1);
});
lbDownload?.addEventListener("click", async () => {
  if (!activeRoom) return;
  lbDownload.disabled = true;
  try {
    await exportRoomPng({
      cardEl: lbBody.querySelector(".museum-card"),
      title: activeRoom.title,
      fallbackPng: activeRoom.png,
    });
  } catch {
    if (activeRoom.png) triggerDownload(activeRoom.png, `${activeRoom.title || "exhibit"}.png`);
  } finally {
    lbDownload.disabled = false;
  }
});
lb.addEventListener("click", (e) => {
  if (e.target === lb) closeLightbox();
});

let lbTouchX = 0;
lb?.addEventListener(
  "touchstart",
  (e) => {
    lbTouchX = e.changedTouches[0].screenX;
  },
  { passive: true }
);
lb?.addEventListener(
  "touchend",
  (e) => {
    if (!lb.classList.contains("open")) return;
    const dx = e.changedTouches[0].screenX - lbTouchX;
    if (Math.abs(dx) > 48) navigateLightbox(dx < 0 ? 1 : -1);
  },
  { passive: true }
);

document.addEventListener("keydown", (e) => {
  if (!lb.classList.contains("open")) return;
  if (e.key === "Escape") closeLightbox();
  else if (e.key === "ArrowLeft") {
    e.preventDefault();
    navigateLightbox(-1);
  } else if (e.key === "ArrowRight") {
    e.preventDefault();
    navigateLightbox(1);
  }
});

// ---------- gradio server connection ----------
let clientPromise = null;
const getClient = () => (clientPromise ||= Client.connect(window.location.origin));

// ---------- capture the exact card shown on screen ----------
async function fontsReady() {
  try {
    await (document.fonts?.ready ?? Promise.resolve());
  } catch {
    /* ignore */
  }
}

// 4× PNG ≈ ~1600px wide — sharp on Instagram/X feeds; PNG uploads everywhere SVG can't.
const CARD_EXPORT_SCALE = 4;

/** Social-ready PNG: exact on-screen card, transparent rounded corners, crisp text. */
async function downloadCardPng(cardEl, title) {
  await fontsReady();
  await snapdom.download(cardEl, {
    format: "png",
    filename: title,
    scale: CARD_EXPORT_SCALE,
    embedFonts: true,
    backgroundColor: "transparent",
  });
}

/** Small JPEG for the gallery grid (keeps localStorage under quota).
 *  The lightbox renders the live card_html instead, so this stays tiny on purpose. */
async function captureCardThumb(cardEl) {
  await fontsReady();
  const img = await snapdom.toJpg(cardEl, {
    scale: 0.5,
    quality: 0.82,
    embedFonts: true,
    backgroundColor: CARD_EXPORT_BG,
  });
  return img.src;
}

function triggerDownload(url, filename) {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

async function exportRoomPng({ cardEl, title, fallbackPng }) {
  const fileName = `${title || "exhibit"}.png`;
  if (cardEl) {
    await downloadCardPng(cardEl, title || "exhibit");
    return;
  }
  if (fallbackPng) triggerDownload(fallbackPng, fileName);
}

// ---------- stage renderers ----------
function showCurating(isFirstLoad = false) {
  const subcopy = isFirstLoad
    ? `<p class="curating-sub">The curator is opening the archive for the first time this session. Please allow about a minute.</p>`
    : "";

  stage.innerHTML = `
    <div class="curating" role="status" aria-live="polite" aria-busy="true">
      <div class="orb" aria-hidden="true"></div>
      <p class="curating-title">Curating your exhibit&hellip;</p>
      ${subcopy}
    </div>`;
}

function showNotice(msg) {
  stage.innerHTML = `<div class="notice">${escapeHtml(msg)}</div>`;
}

async function showExhibit(data) {
  const title = data.title || "exhibit";
  stage.innerHTML = `
    <div class="reveal">
      <div class="spotlight"></div>
      ${data.card_html}
      <div class="exhibit-actions">
        <button class="ghost-btn" id="download" type="button">
          ${DOWNLOAD_ICON}
          Download card
        </button>
        <button class="ghost-btn" id="again" type="button">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 12a8 8 0 1 1 2.3 5.6M4 20v-4h4"/></svg>
          Open another room
        </button>
      </div>
    </div>`;

  $("#again")?.addEventListener("click", () => {
    lineEl.value = "";
    autoGrow();
    lineEl.focus();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  const cardEl = stage.querySelector(".museum-card");
  const downloadBtn = $("#download");

  // Download = the exact card on screen (server PNG only as a last resort).
  downloadBtn?.addEventListener("click", async () => {
    downloadBtn.disabled = true;
    try {
      await exportRoomPng({ cardEl, title, fallbackPng: data.png });
    } catch {
      if (data.png) triggerDownload(data.png, fileName);
    } finally {
      downloadBtn.disabled = false;
    }
  });

  // Small grid thumb only; lightbox renders the live card_html (crisp vector).
  let thumb = data.png;
  try {
    if (cardEl) thumb = await captureCardThumb(cardEl);
  } catch {
    /* keep server PNG */
  }
  pushRoom({ title, png: thumb, card_html: data.card_html });
}

// ---------- main action ----------
async function openRoom() {
  const text = lineEl.value.trim();
  if (!text) {
    showNotice("Share a path you did not take — the words that follow \u201CWhat if\u201D.");
    lineEl.focus();
    return;
  }

  openBtn.disabled = true;
  const originalLabel = openBtn.textContent;
  openBtn.innerHTML = 'Opening the room<span class="dots"></span>';
  const isFirstLoad = roomsOpenedThisSession === 0;
  showCurating(isFirstLoad);

  try {
    const client = await getClient();
    const res = await client.predict("/open_room", { user_line: text });
    const payload = Array.isArray(res?.data) ? res.data[0] : res?.data ?? res;

    if (payload && payload.ok) {
      roomsOpenedThisSession += 1;
      showExhibit(payload);
    } else {
      showNotice((payload && payload.error) || "The museum could not open this room.");
    }
  } catch (err) {
    showNotice("The museum could not open this room. (" + (err?.message || err) + ")");
  } finally {
    openBtn.disabled = false;
    openBtn.textContent = originalLabel;
  }
}

// ---------- wiring ----------
lineEl.addEventListener("input", autoGrow);
openBtn.addEventListener("click", openRoom);
lineEl.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
    e.preventDefault();
    openRoom();
  }
});

// ---------- living atmosphere: drifting dust motes + parallax ----------
const prefersReducedMotion =
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;

function initDust() {
  const canvas = document.getElementById("dust");
  if (!canvas || prefersReducedMotion) return;
  const ctx = canvas.getContext("2d", { alpha: true });
  if (!ctx) return;

  const TINTS = [
    [201, 168, 106], // brass
    [167, 139, 250], // violet
    [233, 228, 240], // pale light
  ];
  let dpr = 1;
  let w = 0;
  let h = 0;
  let motes = [];

  const rand = (a, b) => a + Math.random() * (b - a);

  function spawn() {
    const count = Math.round(Math.min(64, Math.max(28, (w * h) / 26000)));
    motes = new Array(count).fill(0).map(() => {
      const tint = TINTS[(Math.random() * TINTS.length) | 0];
      return {
        x: Math.random() * w,
        y: Math.random() * h,
        r: rand(0.5, 2.1),
        vy: rand(-5, -14) / 1000, // drift upward, px per ms
        vx: rand(-4, 4) / 1000,
        sway: rand(0.0006, 0.0016),
        phase: Math.random() * Math.PI * 2,
        base: rand(0.12, 0.55),
        tw: rand(0.0008, 0.0022), // twinkle speed
        tint,
      };
    });
  }

  function resize() {
    dpr = Math.min(2, window.devicePixelRatio || 1);
    w = canvas.clientWidth;
    h = canvas.clientHeight;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    spawn();
  }

  let last = performance.now();
  function frame(now) {
    const dt = Math.min(48, now - last);
    last = now;
    ctx.clearRect(0, 0, w, h);

    for (const m of motes) {
      m.y += m.vy * dt;
      m.x += (m.vx + Math.sin(now * m.sway + m.phase) * 0.012) * dt;

      if (m.y < -6) {
        m.y = h + 6;
        m.x = Math.random() * w;
      }
      if (m.x < -6) m.x = w + 6;
      else if (m.x > w + 6) m.x = -6;

      const alpha = m.base * (0.55 + 0.45 * Math.sin(now * m.tw + m.phase));
      const [r, g, b] = m.tint;
      ctx.beginPath();
      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha.toFixed(3)})`;
      ctx.shadowColor = `rgba(${r}, ${g}, ${b}, ${(alpha * 0.6).toFixed(3)})`;
      ctx.shadowBlur = m.r * 3.4;
      ctx.arc(m.x, m.y, m.r, 0, Math.PI * 2);
      ctx.fill();
    }
    rafId = requestAnimationFrame(frame);
  }

  let rafId = 0;
  let resizeTimer = null;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(resize, 160);
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      cancelAnimationFrame(rafId);
    } else {
      last = performance.now();
      rafId = requestAnimationFrame(frame);
    }
  });

  resize();
  rafId = requestAnimationFrame(frame);
}

function initParallax() {
  if (prefersReducedMotion || window.matchMedia?.("(pointer: coarse)").matches) return;
  const root = document.documentElement;
  const lantern = document.getElementById("lantern");

  // normalized -1..1 for parallax; raw px for the lantern
  let tx = 0, ty = 0, cx = 0, cy = 0;
  let lpx = window.innerWidth / 2, lpy = window.innerHeight * 0.4;
  let lcx = lpx, lcy = lpy;
  let running = false;

  function loop() {
    cx += (tx - cx) * 0.06;
    cy += (ty - cy) * 0.06;
    lcx += (lpx - lcx) * 0.12;
    lcy += (lpy - lcy) * 0.12;

    root.style.setProperty("--px", cx.toFixed(3));
    root.style.setProperty("--py", cy.toFixed(3));
    if (lantern) {
      lantern.style.setProperty("--lx", `${lcx.toFixed(1)}px`);
      lantern.style.setProperty("--ly", `${lcy.toFixed(1)}px`);
    }

    const settled =
      Math.abs(tx - cx) < 0.001 && Math.abs(ty - cy) < 0.001 &&
      Math.abs(lpx - lcx) < 0.2 && Math.abs(lpy - lcy) < 0.2;
    if (settled) running = false;
    else requestAnimationFrame(loop);
  }

  function kick() {
    if (!running) {
      running = true;
      requestAnimationFrame(loop);
    }
  }

  window.addEventListener(
    "pointermove",
    (e) => {
      tx = (e.clientX / window.innerWidth - 0.5) * 2;
      ty = (e.clientY / window.innerHeight - 0.5) * 2;
      lpx = e.clientX;
      lpy = e.clientY;
      lantern?.classList.add("lit");
      kick();
    },
    { passive: true }
  );
  window.addEventListener("pointerleave", () => lantern?.classList.remove("lit"));
}

// ---------- drifting "What if…" whispers ----------
const WHISPER_LINES = [
  "What if I had stayed",
  "What if I had said yes",
  "What if I had never left",
  "What if I had walked away",
  "What if I had told the truth",
  "What if I had answered the call",
  "What if I had chosen the other road",
  "What if I had been brave",
  "What if I had let go sooner",
  "What if I had forgiven them",
  "What if I had gone alone",
  "What if I had kept the letter",
  "What if I had turned back",
  "What if I had waited one more day",
  "What if I had believed you",
];

function initWhispers() {
  const layer = document.getElementById("whispers");
  if (!layer || prefersReducedMotion) return;

  let pool = [...WHISPER_LINES];
  function nextLine() {
    if (!pool.length) pool = [...WHISPER_LINES];
    const i = (Math.random() * pool.length) | 0;
    return pool.splice(i, 1)[0];
  }

  function spawn() {
    if (document.hidden) return;
    const el = document.createElement("span");
    el.className = "whisper";
    el.textContent = nextLine();

    const wx = `${(8 + Math.random() * 78).toFixed(1)}vw`;
    const wy = `${(20 + Math.random() * 64).toFixed(1)}vh`;
    const dur = 11 + Math.random() * 7;
    el.style.setProperty("--wx", wx);
    el.style.setProperty("--wy", wy);
    el.style.setProperty("--wo", (0.12 + Math.random() * 0.16).toFixed(3));
    el.style.animation = `whisper-rise ${dur.toFixed(1)}s ease-in-out forwards`;

    layer.appendChild(el);
    el.addEventListener("animationend", () => el.remove());
  }

  // gentle cadence — never more than ~2-3 on screen
  const tick = () => {
    spawn();
    setTimeout(tick, 4200 + Math.random() * 3600);
  };
  setTimeout(tick, 1400);
}

initDust();
initParallax();
initWhispers();
initCarousel();
renderGallery();
autoGrow();
getClient().catch(() => {}); // warm the Gradio connection
