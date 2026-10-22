/* Screen 09: cascading Division -> District -> Area selects and the live preview card. */
(function () {
  var data = JSON.parse(document.getElementById("locations-data").textContent);
  var row = document.getElementById("loc-row");
  var division = document.getElementById("division");
  var district = document.getElementById("district");
  var area = document.getElementById("area");

  function fill(select, items, wanted) {
    select.innerHTML = "";
    items.forEach(function (item) {
      var o = document.createElement("option");
      o.value = o.textContent = item;
      if (item === wanted) o.selected = true;
      select.appendChild(o);
    });
  }
  function onDivision(wantedDistrict, wantedArea) {
    var districts = Object.keys(data[division.value] || {});
    fill(district, districts, wantedDistrict);
    onDistrict(wantedArea);
  }
  function onDistrict(wantedArea) {
    var areas = (data[division.value] || {})[district.value] || [];
    fill(area, areas, wantedArea);
  }

  fill(division, Object.keys(data), row.dataset.division);
  onDivision(row.dataset.district, row.dataset.area);
  division.addEventListener("change", function () { onDivision(); render(); });
  district.addEventListener("change", function () { onDistrict(); render(); });

  /* ---------- live preview ---------- */
  var q = function (s) { return document.querySelector(s); };
  function shortTime(slot) {
    var m = slot.match(/^(\S+) (AM|PM) – (\S+) (AM|PM)$/);
    return m && m[2] === m[4] ? m[1] + " – " + m[3] + " " + m[2] : slot;
  }
  function chip(text, cls) {
    var s = document.createElement("span");
    s.className = "chip" + (cls ? " " + cls : "");
    s.textContent = text;
    return s;
  }
  function render() {
    var subject = q("#subject").value, level = q("#class_level").value;
    q("#pv-title").textContent = subject + " · " + level;

    var budget = q("#budget").value.replace(/\s/g, "") || "—";
    var nums = (q("#budget").value.replace(/,/g, "").match(/\d+/g) || []).map(Number);
    var budgetText = nums.length ? "৳" + nums.map(function (n) { return n.toLocaleString("en-US"); }).join("–") : budget;
    var days = Array.prototype.map.call(document.querySelectorAll("input[name=preferred_days]:checked"), function (i) { return i.value; });
    var mode = document.querySelector("input[name=teaching_mode]:checked");
    var online = !mode || mode.value === "ONLINE";

    var chips = q("#pv-chips");
    chips.innerHTML = "";
    chips.appendChild(chip(budgetText));
    if (days.length) chips.appendChild(chip(days.join(" · ")));
    chips.appendChild(chip(shortTime(q("#time_slot").value)));
    chips.appendChild(chip(online ? "Online" : "Offline", online ? "green" : "red"));

    var desc = q("#description").value.trim();
    q("#pv-desc").textContent = desc.length > 110 ? desc.slice(0, 110) + "…" : desc;
    q("#pv-loc").textContent = area.value + ", " + district.value;
  }
  document.getElementById("post-form").addEventListener("input", render);
  document.getElementById("post-form").addEventListener("change", render);
  render();
})();
