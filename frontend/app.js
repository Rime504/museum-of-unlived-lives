// Museum of Unlived Lives — frontend logic.
// Talks to the gr.Server /open_room API via the official Gradio JS client.
import { Client } from "https://esm.sh/@gradio/client@2.2.1";

const $ = (sel) => document.querySelector(sel);
const lineEl = $("#line");
const openBtn = $("#open");
const stage = $("#stage");
const grid = $("#grid");
const countEl = $("#count");

const STORE_KEY = "museum.rooms.v1";
const MAX_ROOMS = 12;

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
    fig.addEventListener("click", () => openLightbox(room.png));
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
const lbImg = $("#lbImg");
const openLightbox = (src) => {
  lbImg.src = src;
  lb.classList.add("open");
};
const closeLightbox = () => lb.classList.remove("open");

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

// ---------- stage renderers ----------
function showCurating() {
  stage.innerHTML = `<div class="curating"><div class="orb"></div><p>Curating your exhibit&hellip;</p></div>`;
}

function showNotice(msg) {
  stage.innerHTML = `<div class="notice">${escapeHtml(msg)}</div>`;
}

function showExhibit(data) {
  const safeTitle = escapeAttr(data.title || "exhibit");
  stage.innerHTML = `
    <div class="reveal">
      <div class="spotlight"></div>
      ${data.card_html}
      <div class="exhibit-actions">
        <a class="ghost-btn" href="${data.png}" download="${safeTitle}.png">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14"/></svg>
          Download card
        </a>
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

  pushRoom({ title: data.title, png: data.png });
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
  showCurating();

  try {
    const client = await getClient();
    const res = await client.predict("/open_room", { user_line: text });
    const payload = Array.isArray(res?.data) ? res.data[0] : res?.data ?? res;

    if (payload && payload.ok) {
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
getClient().catch(() => {}); // warm the connection in the background
