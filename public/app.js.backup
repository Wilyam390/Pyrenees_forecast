// -------- Helper: tiny fetch wrapper with useful errors --------
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
const resultsGlobal = document.getElementById('resultsGlobal');

btnGlobal.onclick = async () => {
  resultsGlobal.innerHTML = '<li><div class="muted">Searching...</div></li>';
  try {
    const data = await api('/api/catalog/peaks_all?q=' + encodeURIComponent(qGlobal.value || ''));
    resultsGlobal.innerHTML = '';
    
    if (!data.length) {
      resultsGlobal.innerHTML = '<li><div class="muted">No peaks found. Try "Aneto", "Perdido", or "Posets"</div></li>';
      return;
    }
    
    for (const p of data) {
      const li = document.createElement('li');
      li.innerHTML = `
        <div class="peak-info">
          <div class="peak-name">${p.name}</div>
          <div class="peak-details">${p.summit_elev_m} m${p.massif ? ' • ' + p.massif : ''}</div>
        </div>
        <button data-peak-id="${p.id}">Add to My Mountains</button>
      `;
      li.querySelector('button').onclick = async (e) => {
        e.target.disabled = true;
        e.target.textContent = 'Adding...';
        await fetch('/api/my/mountains/' + p.id, { method: 'POST' });
        loadMy();
        e.target.textContent = '✓ Added';
        setTimeout(() => {
          resultsGlobal.innerHTML = '';
          qGlobal.value = '';
        }, 1000);
      };
      resultsGlobal.appendChild(li);
    }
  } catch (err) {
    resultsGlobal.innerHTML = `<li><div class="error">Error: ${err.message}</div></li>`;
  }
};

// Allow Enter key to search
qGlobal.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') btnGlobal.click();
});

// ======== BROWSE: AREA → MASSIF → (auto lists) PEAKS ===========
const selArea = document.getElementById('area');
const selMassif = document.getElementById('massif');
const resultsBrowse = document.getElementById('resultsBrowse');

(async function initSelectors() {
  try {
    const areas = await api('/api/catalog/areas');
    selArea.innerHTML =
      '<option value="">Select area...</option>' +
      areas.map((a) => `<option value="${a.id}">${a.name}</option>`).join('');
  } catch (err) {
    console.error('Failed to load areas:', err);
  }
})();

selArea.onchange = async () => {
  resultsBrowse.innerHTML = '';
  selMassif.disabled = true;
  selMassif.innerHTML = '<option value="">Select massif...</option>';
  
  if (!selArea.value) return;
  
  try {
    const massifs = await api('/api/catalog/massifs?area=' + encodeURIComponent(selArea.value));
    selMassif.innerHTML =
      '<option value="">Select massif...</option>' +
      massifs.map((m) => `<option value="${m.id}">${m.name}</option>`).join('');
    selMassif.disabled = false;
  } catch (err) {
    console.error('Failed to load massifs:', err);
  }
};

selMassif.onchange = async () => {
  resultsBrowse.innerHTML = '';
  if (!selArea.value || !selMassif.value) return;
  
  try {
    const peaks = await api(
      `/api/catalog/peaks?area=${encodeURIComponent(selArea.value)}&massif=${encodeURIComponent(selMassif.value)}`
    );
    
    if (!peaks.length) {
      resultsBrowse.innerHTML = '<li><div class="muted">No peaks in this massif.</div></li>';
      return;
    }
    
    for (const p of peaks) {
      const li = document.createElement('li');
      li.innerHTML = `
        <div class="peak-info">
          <div class="peak-name">${p.name}</div>
          <div class="peak-details">${p.summit_elev_m} m</div>
        </div>
        <button data-peak-id="${p.id}">Add to My Mountains</button>
      `;
      li.querySelector('button').onclick = async (e) => {
        e.target.disabled = true;
        e.target.textContent = 'Adding...';
        await fetch('/api/my/mountains/' + p.id, { method: 'POST' });
        loadMy();
        e.target.textContent = '✓ Added';
        setTimeout(() => {
          resultsBrowse.innerHTML = '';
          selMassif.value = '';
        }, 1000);
      };
      resultsBrowse.appendChild(li);
    }
  } catch (err) {
    resultsBrowse.innerHTML = `<li><div class="error">Error: ${err.message}</div></li>`;
  }
};

// ===================== MY MOUNTAINS CARDS ======================
async function loadMy() {
  const cards = document.getElementById('cards');
  cards.innerHTML = '<div class="muted">Loading your mountains...</div>';
  
  try {
    const mine = await api('/api/my/mountains');
    
    if (mine.length === 0) {
      cards.innerHTML = '<div class="empty-state">No mountains added yet.<br>Search and add peaks above to get started!</div>';
      return;
    }
    
    cards.innerHTML = '';
    
    for (const id of mine) {
      const m = await api('/api/catalog/peaks/' + id);

      const el = document.createElement('div');
      el.className = 'card';
      el.innerHTML = `
        <div class="card-header">
          <h3>${m.name}</h3>
          <div class="card-meta">
            ${m.massif ? m.massif + ' • ' : ''}${m.province ?? ''}
          </div>
        </div>
        
        <div class="badges">
          <span class="pill">Base: ${m.bands.base.elev_m} m</span>
          <span class="pill">Mid: ${m.bands.mid.elev_m} m</span>
          <span class="pill">Summit: ${m.bands.summit.elev_m} m</span>
        </div>
        
        <div class="band-selector">
          <div class="band active" data-band="base">Base</div>
          <div class="band" data-band="mid">Mid</div>
          <div class="band" data-band="summit">Summit</div>
        </div>
        
        <div class="weather-summary" data-summary>Loading weather...</div>
        <div class="weather-updated" data-updated></div>
        <div class="weather-table-wrap" data-tablewrap></div>
        
        <button class="remove-btn" data-remove>Remove from My Mountains</button>
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
          const hhmm = r.time.slice(11, 16);
          html += `<tr>
            <td>${hhmm}</td>
            <td>${r.temp_c}°C${r.snow_likely ? ' ❄️' : ''}</td>
            <td>${r.wind_speed_kmh ?? '-'} km/h</td>
            <td>${r.wind_gust_kmh ?? '-'} km/h</td>
            <td>${r.precip_mm} mm</td>
          </tr>`;
        }
        html += '</tbody></table><div class="table-note">Showing next 8 of 24 hours</div>';
        tableWrap.innerHTML = html;
      }

      async function loadBand(band) {
        try {
          setActive(band);
          summaryEl.textContent = 'Loading weather...';
          updatedEl.textContent = '';
          tableWrap.innerHTML = '';
          
          const data = await api(`/api/weather/${id}?band=${band}`);
          
          if (!Array.isArray(data) || data.length === 0) {
            summaryEl.innerHTML = '<span class="error">No data returned.</span>';
            return;
          }
          
          renderTable(data);
        } catch (err) {
          summaryEl.innerHTML = `<span class="error">Failed to load: ${err.message}</span> <a href="#" data-retry style="color: #667eea; font-weight: 600;">Retry</a>`;
          updatedEl.textContent = '';
          tableWrap.innerHTML = '';
          const retry = el.querySelector('[data-retry]');
          if (retry) retry.onclick = (e) => { e.preventDefault(); loadBand(band); };
        }
      }

      bands.forEach((span) => (span.onclick = () => loadBand(span.dataset.band)));
      
      el.querySelector('[data-remove]').onclick = async () => {
        if (confirm(`Remove ${m.name} from your mountains?`)) {
          await fetch('/api/my/mountains/' + id, { method: 'DELETE' });
          loadMy();
        }
      };
      
      cards.appendChild(el);

      // Initial load
      loadBand('base');
    }
  } catch (err) {
    cards.innerHTML = `<div class="error">Failed to load mountains: ${err.message}</div>`;
  }
}

// Kick off
loadMy();