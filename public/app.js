async function api(path) {
    const r = await fetch(path);
    if (!r.ok) {
      const t = await r.text();
      throw new Error(`${r.status} ${r.statusText}: ${t}`);
    }
    return r.json();
  }
  
  // =============== GLOBAL SEARCH (search all peaks) ===============
  const qGlobal = document.getElementById('qGlobal');
  const btnGlobal = document.getElementById('searchGlobal');
  const results = document.getElementById('results');
  
  btnGlobal.onclick = async () => {
    results.innerHTML = '';
    try {
      const data = await api('/api/catalog/peaks_all?q=' + encodeURIComponent(qGlobal.value || ''));
      if (!data.length) {
        results.innerHTML = '<li class="muted">No peaks found.</li>';
        return;
      }
      for (const p of data) {
        const li = document.createElement('li');
        li.innerHTML = `${p.name} <small>(${p.summit_elev_m} m${p.massif ? ', ' + p.massif : ''})</small> <button>Add</button>`;
        li.querySelector('button').onclick = async () => {
          await fetch('/api/my/mountains/' + p.id, { method: 'POST' });
          loadMy();
        };
        results.appendChild(li);
      }
    } catch (err) {
      results.innerHTML = `<li class="error">${err.message}</li>`;
    }
  };
  
  const selArea = document.getElementById('area');
  const selMassif = document.getElementById('massif');
  
  (async function initSelectors() {
    const areas = await api('/api/catalog/areas');
    selArea.innerHTML =
      '<option value="">Select area…</option>' +
      areas.map((a) => `<option value="${a.id}">${a.name}</option>`).join('');
  })();
  
  selArea.onchange = async () => {
    results.innerHTML = '';
    selMassif.disabled = true;
    selMassif.innerHTML = '';
    if (!selArea.value) return;
    const massifs = await api('/api/catalog/massifs?area=' + encodeURIComponent(selArea.value));
    selMassif.innerHTML =
      '<option value="">Select massif…</option>' +
      massifs.map((m) => `<option value="${m.id}">${m.name}</option>`).join('');
    selMassif.disabled = false;
  };
  
  selMassif.onchange = async () => {
    results.innerHTML = '';
    if (!selArea.value || !selMassif.value) return;
    const peaks = await api(
      `/api/catalog/peaks?area=${encodeURIComponent(selArea.value)}&massif=${encodeURIComponent(
        selMassif.value
      )}`
    );
    if (!peaks.length) {
      results.innerHTML = '<li class="muted">No peaks in this massif.</li>';
      return;
    }
    for (const p of peaks) {
      const li = document.createElement('li');
      li.innerHTML = `${p.name} <small>(${p.summit_elev_m} m)</small> <button>Add</button>`;
      li.querySelector('button').onclick = async () => {
        await fetch('/api/my/mountains/' + p.id, { method: 'POST' });
        loadMy();
      };
      results.appendChild(li);
    }
  };
  
  // ===================== MY MOUNTAINS CARDS ======================
  async function loadMy() {
    const cards = document.getElementById('cards');
    cards.innerHTML = '';
    const mine = await api('/api/my/mountains');
  
    for (const id of mine) {
      const m = await api('/api/catalog/peaks/' + id);
  
      const el = document.createElement('div');
      el.className = 'card';
      el.innerHTML = `
        <h3>${m.name}</h3>
        <div class="muted">${m.massif ? m.massif + ' • ' : ''}${m.province ?? ''}</div>
        <div class="badges" style="margin:6px 0 8px;">
          <span class="pill">Base: ${m.bands.base.elev_m} m</span>
          <span class="pill">Mid: ${m.bands.mid.elev_m} m</span>
          <span class="pill">Summit: ${m.bands.summit.elev_m} m</span>
        </div>
        <div>
          <span class="band active" data-band="base">Base</span>
          <span class="band" data-band="mid">Mid</span>
          <span class="band" data-band="summit">Summit</span>
        </div>
        <div class="muted" style="margin:6px 0;" data-summary>Loading…</div>
        <div class="muted" style="margin:2px 0;" data-updated></div>
        <div data-tablewrap></div>
        <button class="remove" style="margin-top:8px;">Remove</button>
      `;
  
      const bands = el.querySelectorAll('.band');
      const summaryEl = el.querySelector('[data-summary]');
      const updatedEl = el.querySelector('[data-updated]');
      const tableWrap = el.querySelector('[data-tablewrap]');
  
      function setActive(band) {
        bands.forEach((s) => s.classList.remove('active'));
        el.querySelector(`.band[data-band="${band}"]`).classList.add('active');
      }
  
      function renderTable(rows) {
        // rows: [{time:"YYYY-MM-DDTHH:MM", temp_c, wind_speed_kmh, wind_gust_kmh, precip_mm, snow_likely}]
        const first = rows[0];
        const nowLine = `Now: ${first.temp_c}°C, wind ${first.wind_speed_kmh} km/h${
          first.wind_gust_kmh ? ` (gust ${first.wind_gust_kmh})` : ''
        }, precip ${first.precip_mm} mm${first.snow_likely ? ' ❄️' : ''}`;
        summaryEl.textContent = nowLine;
  
        const fetchedAt = new Date();
        const hh = String(fetchedAt.getHours()).padStart(2, '0');
        const mm = String(fetchedAt.getMinutes()).padStart(2, '0');
        updatedEl.textContent = `Updated ${hh}:${mm} • TZ: Europe/Madrid`;
  
        let html =
          '<table><thead><tr><th>Time</th><th>Temp</th><th>Wind</th><th>Gust</th><th>Precip</th></tr></thead><tbody>';
        for (const r of rows.slice(0, 8)) {
          // Avoid timezone conversion: take "HH:MM" directly from API string
          const hhmm = r.time.slice(11, 16);
          html += `<tr>
            <td>${hhmm}</td>
            <td>${r.temp_c}°C${r.snow_likely ? ' ❄️' : ''}</td>
            <td>${r.wind_speed_kmh ?? '-'}</td>
            <td>${r.wind_gust_kmh ?? '-'}</td>
            <td>${r.precip_mm}</td>
          </tr>`;
        }
        html += '</tbody></table><div class="muted">Showing next 8 of 24 hours.</div>';
        tableWrap.innerHTML = html;
      }
  
      async function loadBand(band) {
        try {
          setActive(band);
          summaryEl.textContent = 'Loading…';
          updatedEl.textContent = '';
          tableWrap.innerHTML = '';
          const data = await api(`/api/weather/${id}?band=${band}`);
          if (!Array.isArray(data) || data.length === 0) {
            summaryEl.innerHTML = '<span class="error">No data returned.</span>';
            return;
          }
          renderTable(data);
        } catch (err) {
          summaryEl.innerHTML = `<span class="error">Failed to load: ${err.message}</span> <a href="#" data-retry>Retry</a>`;
          updatedEl.textContent = '';
          tableWrap.innerHTML = '';
          const retry = el.querySelector('[data-retry]');
          if (retry) retry.onclick = (e) => { e.preventDefault(); loadBand(band); };
        }
      }
  
      bands.forEach((span) => (span.onclick = () => loadBand(span.dataset.band)));
      el.querySelector('.remove').onclick = async () => {
        await fetch('/api/my/mountains/' + id, { method: 'DELETE' });
        loadMy();
      };
      document.getElementById('cards').appendChild(el);
  
      loadBand('base');
    }
  }
  
  loadMy();
  