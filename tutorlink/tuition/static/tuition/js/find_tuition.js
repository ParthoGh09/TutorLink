/* Screen 10: cascading location filter + dual-handle budget slider. */
(function () {
  /* ---------- location ---------- */
  var data = JSON.parse(document.getElementById("locations-data").textContent);
  var wrap = document.getElementById("filter-loc");
  var division = document.getElementById("f-division");
  var district = document.getElementById("f-district");
  var area = document.getElementById("f-area");

  function fill(select, items, allLabel, wanted) {
    select.innerHTML = "";
    var all = document.createElement("option");
    all.value = ""; all.textContent = allLabel;
    select.appendChild(all);
    items.forEach(function (item) {
      var o = document.createElement("option");
      o.value = o.textContent = item;
      if (item === wanted) o.selected = true;
      select.appendChild(o);
    });
  }
  function districts(wanted) {
    fill(district, Object.keys(data[division.value] || {}), "All Districts", wanted);
    areas();
  }
  function areas(wanted) {
    fill(area, ((data[division.value] || {})[district.value]) || [], "All Areas", wanted);
  }
  fill(division, Object.keys(data), "All Divisions", wrap.dataset.division);
  districts(wrap.dataset.district);
  areas(wrap.dataset.area);
  division.addEventListener("change", function () { districts(); });
  district.addEventListener("change", function () { areas(); });

  /* ---------- budget slider ---------- */
  var box = document.getElementById("budget-range");
  var lo = box.querySelectorAll("input")[0];
  var hi = box.querySelectorAll("input")[1];
  var fill_ = box.querySelector(".fill");
  var minL = document.getElementById("min-label");
  var maxL = document.getElementById("max-label");
  var floor = +box.dataset.floor, ceil = +box.dataset.ceil;

  function fmt(n) { return "৳" + n.toLocaleString("en-US"); }
  function sync(e) {
    var a = +lo.value, b = +hi.value;
    if (a > b) {                       // keep handles from crossing
      if (e && e.target === lo) { lo.value = b; a = b; } else { hi.value = a; b = a; }
    }
    var span = ceil - floor;
    fill_.style.left = ((a - floor) / span * 100) + "%";
    fill_.style.width = ((b - a) / span * 100) + "%";
    minL.textContent = fmt(a);
    maxL.textContent = b >= ceil ? fmt(ceil) + "+" : fmt(b);
  }
  lo.addEventListener("input", sync);
  hi.addEventListener("input", sync);
  sync();
})();
