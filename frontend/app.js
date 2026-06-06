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
const grid = $("#grid");
const countEl = $("#count");

const STORE_KEY = "museum.rooms.v1";
const MAX_ROOMS = 12;

/** Rooms opened this page session — first load shows curator warmup copy. */
let roomsOpenedThisSession = 0;

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
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(rooms.slice(0, MAX_ROOMS)));
  } catch {
    /* quota exceeded — keep the session going without persistence */
  }
}

function renderGallery() {
  const rooms = loadRooms();
  countEl.textContent = rooms.length === 1 ? "1 room" : `${rooms.length} rooms`;

  if (!rooms.length) {
    grid.innerHTML = '<p class="gallery-empty">Your rooms will gather here.</p>';
    return;
  }

  grid.innerHTML = "";
  for (const room of rooms) {
    const fig = document.createElement("figure");
    fig.className = "frame";
    fig.innerHTML = `
      <img src="${room.png}" alt="${escapeAttr(room.title)}" loading="lazy" />
      <figcaption>${escapeHtml(room.title)}</figcaption>`;
    fig.addEventListener("click", () => openLightbox(room));
    grid.appendChild(fig);
  }
}

function pushRoom(room) {
  const rooms = loadRooms();
  rooms.unshift(room);
  saveRooms(rooms);
  renderGallery();
}

// ---------- lightbox ----------
const lb = $("#lightbox");
const lbBody = $("#lbBody");
const lbImg = $("#lbImg");

const openLightbox = (room) => {
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
  lb.classList.add("open");
};

const closeLightbox = () => {
  lb.classList.remove("open");
  lbBody.innerHTML = "";
  lbBody.hidden = true;
  lbImg.hidden = true;
  lbImg.removeAttribute("src");
};

$("#lbClose").addEventListener("click", closeLightbox);
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

/** Small JPEG data URL for the gallery (keeps localStorage under quota). */
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
  const fileName = `${title}.png`;
  stage.innerHTML = `
    <div class="reveal">
      <div class="spotlight"></div>
      ${data.card_html}
      <div class="exhibit-actions">
        <button class="ghost-btn" id="download" type="button">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14"/></svg>
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
      if (cardEl) {
        await downloadCardPng(cardEl, title);
      } else if (data.png) {
        triggerDownload(data.png, fileName);
      }
    } catch {
      if (data.png) triggerDownload(data.png, fileName);
    } finally {
      downloadBtn.disabled = false;
    }
  });

  // Gallery thumbnail from the live card; fall back to the server PNG.
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

renderGallery();
autoGrow();
getClient().catch(() => {}); // warm the Gradio connection
