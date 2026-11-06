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

function renderRows(flights) {
  const tbody = document.querySelector("#flights tbody");
  tbody.innerHTML = "";
  flights.forEach((f) => {
    const tr = document.createElement("tr");
    const route = f.origin.code + " \u2192 " + f.destination.code;
    const pct = Math.round((f.progress || 0) * 100);
    tr.innerHTML =
      '<td class="num">' + f.flight_number + "</td>" +
      "<td>" + f.airline + "</td>" +
      "<td>" + f.aircraft + "</td>" +
      '<td class="num">' + route + "</td>" +
      '<td><span class="' + badgeClass(f.status) + '">' + f.status + "</span></td>" +
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
  const res = await fetch("/api/flights/" + encodeURIComponent(number));
  if (!res.ok) return;
  const f = await res.json();
  const pct = Math.round((f.progress || 0) * 100);
  document.getElementById("modal-body").innerHTML =
    "<h2>" + f.flight_number + " \u2014 " + f.airline + "</h2>" +
    "<p>" + f.aircraft + " \u00b7 Gate " + (f.gate || "\u2014") + "</p>" +
    '<p><span class="' + badgeClass(f.status) + '">' + f.status + "</span>" +
    (f.delay_minutes ? " <em>Delayed " + f.delay_minutes + " min</em>" : "") + "</p>" +
    "<p><strong>" + f.origin.code + "</strong> " + f.origin.name + " (" + f.origin.city + ")<br>" +
    "Departs " + fmtTime(f.departure) + "</p>" +
    '<div class="progress"><div class="fill" style="width:' + pct + '%"></div></div>' +
    "<p><strong>" + f.destination.code + "</strong> " + f.destination.name + " (" + f.destination.city + ")<br>" +
    "Arrives " + fmtTime(f.arrival) + "</p>" +
    "<p>Position: " + f.position.lat + ", " + f.position.lon + "</p>";
  document.getElementById("modal-backdrop").hidden = false;
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
