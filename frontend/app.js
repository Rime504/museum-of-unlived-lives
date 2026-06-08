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
    fig.addEventListener("click", () => openLightbox(room));
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

const openLightbox = (room) => {
  activeRoom = room;
  if (room.card_html) {
    // Live HTML/SVG card — vector, stays crisp at full size.
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
  lbActions.hidden = false;
  lb.classList.add("open");
};

const closeLightbox = () => {
  activeRoom = null;
  lb.classList.remove("open");
  lbBody.innerHTML = "";
  lbBody.hidden = true;
  lbImg.hidden = true;
  lbImg.removeAttribute("src");
  lbActions.hidden = true;
};

$("#lbClose").addEventListener("click", closeLightbox);
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
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeLightbox();
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

initCarousel();
renderGallery();
autoGrow();
getClient().catch(() => {}); // warm the Gradio connection
