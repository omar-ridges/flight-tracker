const state = { query: "", timer: null };

function fmtTime(iso) {
  if (!iso) return "\u2014";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function badgeClass(status) {
  return "badge " + status.toLowerCase().replace(/\s+/g, "-");
}

function esc(value) {
  // Escape HTML metacharacters so API data can never break the markup.
  return String(value).replace(/[&<>"']/g, (ch) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
  ));
}

function renderRows(flights) {
  const tbody = document.querySelector("#flights tbody");
  tbody.innerHTML = "";
  flights.forEach((f) => {
    const tr = document.createElement("tr");
    const route = f.origin.code + " \u2192 " + f.destination.code;
    const pct = Math.round((f.progress || 0) * 100);
    tr.innerHTML =
      '<td class="num">' + esc(f.flight_number) + "</td>" +
      "<td>" + esc(f.airline) + "</td>" +
      "<td>" + esc(f.aircraft) + "</td>" +
      '<td class="num">' + esc(route) + "</td>" +
      '<td><span class="' + esc(badgeClass(f.status)) + '">' + esc(f.status) + "</span></td>" +
      '<td><div class="progress"><div class="fill" style="width:' + pct +
      '%"></div></div><span class="pct">' + pct + "%</span></td>" +
      "<td>" + fmtTime(f.departure) + "</td>" +
      "<td>" + fmtTime(f.arrival) + "</td>";
    tr.addEventListener("click", () => showFlight(f.flight_number));
    tbody.appendChild(tr);
  });
  document.getElementById("empty").hidden = flights.length > 0;
}

async function refresh() {
  try {
    const params = state.query ? "?q=" + encodeURIComponent(state.query) : "";
    const res = await fetch("/api/flights" + params);
    if (!res.ok) throw new Error("HTTP " + res.status);
    renderRows(await res.json());
    document.getElementById("updated").textContent =
      "Updated " + new Date().toLocaleTimeString();
    document.getElementById("error").hidden = true;
  } catch (err) {
    const el = document.getElementById("error");
    el.textContent = "Failed to load flights: " + err.message;
    el.hidden = false;
  }
}

async function showFlight(number) {
  try {
    const res = await fetch("/api/flights/" + encodeURIComponent(number));
    if (!res.ok) return;
    const f = await res.json();
    const pct = Math.round((f.progress || 0) * 100);
    document.getElementById("modal-body").innerHTML =
      "<h2>" + esc(f.flight_number) + " \u2014 " + esc(f.airline) + "</h2>" +
      "<p>" + esc(f.aircraft) + " \u00b7 Gate " + esc(f.gate || "\u2014") + "</p>" +
      '<p><span class="' + esc(badgeClass(f.status)) + '">' + esc(f.status) + "</span>" +
      (f.delay_minutes ? " <em>Delayed " + esc(f.delay_minutes) + " min</em>" : "") + "</p>" +
      "<p><strong>" + esc(f.origin.code) + "</strong> " + esc(f.origin.name) + " (" + esc(f.origin.city) + ")<br>" +
      "Departs " + esc(fmtTime(f.departure)) + "</p>" +
      '<div class="progress"><div class="fill" style="width:' + pct + '%"></div></div>' +
      "<p><strong>" + esc(f.destination.code) + "</strong> " + esc(f.destination.name) + " (" + esc(f.destination.city) + ")<br>" +
      "Arrives " + esc(fmtTime(f.arrival)) + "</p>" +
      "<p>Position: " + esc(f.position.lat) + ", " + esc(f.position.lon) + "</p>";
    document.getElementById("modal-backdrop").hidden = false;
  } catch (err) {
    console.error("Failed to load flight " + number, err);
  }
}

function closeModal() {
  document.getElementById("modal-backdrop").hidden = true;
}

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("search");
  let debounce;
  input.addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      state.query = input.value.trim();
      refresh();
    }, 200);
  });
  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("modal-backdrop").addEventListener("click", (e) => {
    if (e.target.id === "modal-backdrop") closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
  refresh();
  state.timer = setInterval(refresh, 5000);
});
