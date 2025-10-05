// -------- Helper: API wrapper --------
async function api(path) {
  const r = await fetch(path);
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`${r.status} ${r.statusText}: ${t}`);
  }
  return r.json();
}

// -------- DOM Elements --------
const qGlobal = document.getElementById('qGlobal');
const btnGlobal = document.getElementById('searchGlobal');
const results = document.getElementById('results');
const selArea = document.getElementById('area');
const selMassif = document.getElementById('massif');
const cardsContainer = document.getElementById('cards');
const mountainCount = document.getElementById('mountainCount');

// =============== GLOBAL SEARCH ===============
btnGlobal.onclick = async () => {
  results.innerHTML = '<li class="loading">Searching...</li>';
  try {
    const data = await api('/api/catalog/peaks_all?q=' + encodeURIComponent(qGlobal.value || ''));
    
    if (!data.length) {
      results.innerHTML = '<li class="muted" style="text-align:center; padding: 20px;">No peaks found. Try a different search term.</li>';
      return;
    }
    
    results.innerHTML = '';
    for (const p of data) {
      const li = document.createElement('li');
      li.innerHTML = `
        <div class="peak-info">
          <div class="peak-name">${p.name}</div>
          <div class="peak-details">${p.summit_elev_m} m${p.massif ? ' • ' + p.massif : ''}</div>
        </div>
        <button class="add-btn">+ Add</button>
      `;
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

// Allow Enter key to search
qGlobal.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') btnGlobal.click();
});

// ======== BROWSE: AREA → MASSIF → PEAKS ===========
(async function initSelectors() {
  const areas = await api('/api/catalog/areas');
  selArea.innerHTML =
    '<option value="">Select area…</option>' +
    areas.map((a) => `<option value="${a.id}">${a.name}</option>`).join('');
})();

selArea.onchange = async () => {
  results.innerHTML = '';
  selMassif.disabled = true;
  selMassif.innerHTML = '<option value="">Select massif…</option>';
  
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
  
  results.innerHTML = '<li class="loading">Loading peaks...</li>';
  
  try {
    const peaks = await api(
      `/api/catalog/peaks?area=${encodeURIComponent(selArea.value)}&massif=${encodeURIComponent(selMassif.value)}`
    );
    
    if (!peaks.length) {
      results.innerHTML = '<li class="muted" style="text-align:center; padding: 20px;">No peaks in this massif.</li>';
      return;
    }
    
    results.innerHTML = '';
    for (const p of peaks) {
      const li = document.createElement('li');
      li.innerHTML = `
        <div class="peak-info">
          <div class="peak-name">${p.name}</div>
          <div class="peak-details">${p.summit_elev_m} m</div>
        </div>
        <button class="add-btn">+ Add</button>
      `;
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

// ===================== MY MOUNTAINS CARDS ======================
async function loadMy() {
  cardsContainer.innerHTML = '<div class="loading">Loading your mountains...</div>';
  
  try {
    const mine = await api('/api/my/mountains');
    
    // Update count
    mountainCount.textContent = `${mine.length} ${mine.length === 1 ? 'peak' : 'peaks'}`;
    
    if (mine.length === 0) {
      cardsContainer.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">🏔️</div>
          <div class="empty-state-text">No mountains added yet</div>
          <div class="empty-state-hint">Search for a peak above to get started!</div>
        </div>
      `;
      return;
    }
    
    cardsContainer.innerHTML = '';
    
    for (const id of mine) {
      const m = await api('/api/catalog/peaks/' + id);
      const card = createMountainCard(id, m);
      cardsContainer.appendChild(card);
    }
  } catch (err) {
    cardsContainer.innerHTML = `<div class="error">Failed to load mountains: ${err.message}</div>`;
  }
}

function createMountainCard(id, mountain) {
  const card = document.createElement('div');
  card.className = 'mountain-card';
  
  card.innerHTML = `
    <div class="card-header">
      <h3 class="card-title">${mountain.name}</h3>
      <div class="card-subtitle">${mountain.massif ? mountain.massif + ' • ' : ''}${mountain.province ?? ''}</div>
    </div>
    
    <div class="elevation-badges">
      <span class="badge">📍 Base: ${mountain.bands.base.elev_m} m</span>
      <span class="badge">⛰️ Mid: ${mountain.bands.mid.elev_m} m</span>
      <span class="badge">🏔️ Summit: ${mountain.bands.summit.elev_m} m</span>
    </div>
    
    <div class="band-selector">
      <button class="band-btn active" data-band="base">Base</button>
      <button class="band-btn" data-band="mid">Mid</button>
      <button class="band-btn" data-band="summit">Summit</button>
    </div>
    
    <div class="weather-summary" data-summary>
      <div class="loading">Loading weather...</div>
    </div>
    
    <div class="weather-table-wrap" data-tablewrap></div>
    
    <div class="card-actions">
      <button class="advanced-btn" data-advanced>📊 Advanced Weather</button>
      <button class="remove-btn" data-remove>🗑️ Remove</button>
    </div>
  `;
  
  // Get references
  const bandButtons = card.querySelectorAll('.band-btn');
  const summaryEl = card.querySelector('[data-summary]');
  const tableWrap = card.querySelector('[data-tablewrap]');
  const removeBtn = card.querySelector('[data-remove]');
  const advancedBtn = card.querySelector('[data-advanced]');
  
  let currentBand = 'base';
  let currentWeatherData = null;
  
  // Band switching
  function setActiveBand(band) {
    currentBand = band;
    bandButtons.forEach(btn => {
      if (btn.dataset.band === band) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }
  
  // Render weather table
  function renderWeather(weatherData) {
    currentWeatherData = weatherData;
    
    const first = weatherData[0];
    const snowIcon = first.snow_likely ? ' ❄️' : '';
    
    summaryEl.innerHTML = `
      <div class="current-weather">
        🌡️ ${first.temp_c}°C • 💨 ${first.wind_speed_kmh} km/h${first.wind_gust_kmh ? ` (gusts ${first.wind_gust_kmh})` : ''}
      </div>
      <div class="weather-meta">
        💧 ${first.precip_mm} mm${snowIcon} • Updated ${new Date().toLocaleTimeString('en-GB', {hour: '2-digit', minute: '2-digit'})} • TZ: Europe/Madrid
      </div>
    `;
    
    let tableHTML = `
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Temp</th>
            <th>Wind</th>
            <th>Gust</th>
            <th>Precip</th>
          </tr>
        </thead>
        <tbody>
    `;
    
    for (const row of weatherData.slice(0, 8)) {
      const hhmm = row.time.slice(11, 16);
      const snowIcon = row.snow_likely ? ' ❄️' : '';
      
      tableHTML += `
        <tr>
          <td><strong>${hhmm}</strong></td>
          <td>${row.temp_c}°C${snowIcon}</td>
          <td>${row.wind_speed_kmh ?? '-'} km/h</td>
          <td>${row.wind_gust_kmh ?? '-'} km/h</td>
          <td>${row.precip_mm} mm</td>
        </tr>
      `;
    }
    
    tableHTML += `
        </tbody>
      </table>
      <div class="table-footer">Showing next 8 of 24 hours</div>
    `;
    
    tableWrap.innerHTML = tableHTML;
  }
  
  // Load weather for a band
  async function loadWeather(band) {
    try {
      setActiveBand(band);
      summaryEl.innerHTML = '<div class="loading">Loading weather...</div>';
      tableWrap.innerHTML = '';
      
      const data = await api(`/api/weather/${id}?band=${band}`);
      
      if (!Array.isArray(data) || data.length === 0) {
        summaryEl.innerHTML = '<div class="error">No weather data available</div>';
        return;
      }
      
      renderWeather(data);
    } catch (err) {
      summaryEl.innerHTML = `
        <div class="error">
          Failed to load weather: ${err.message}
          <a href="#" data-retry>Retry</a>
        </div>
      `;
      tableWrap.innerHTML = '';
      
      const retryLink = summaryEl.querySelector('[data-retry]');
      if (retryLink) {
        retryLink.onclick = (e) => {
          e.preventDefault();
          loadWeather(band);
        };
      }
    }
  }
  
  // Event listeners
  bandButtons.forEach(btn => {
    btn.onclick = () => loadWeather(btn.dataset.band);
  });
  
  removeBtn.onclick = async () => {
    if (confirm(`Remove ${mountain.name} from your list?`)) {
      await fetch('/api/my/mountains/' + id, { method: 'DELETE' });
      loadMy();
    }
  };
  
  advancedBtn.onclick = () => {
    if (currentWeatherData) {
      showAdvancedWeather(mountain, currentBand, currentWeatherData);
    } else {
      alert('Please wait for weather data to load first');
    }
  };
  
  // Initial load
  loadWeather('base');
  
  return card;
}

// ===================== ADVANCED WEATHER MODAL ======================
function showAdvancedWeather(mountain, band, weatherData) {
  const modal = document.getElementById('advancedModal');
  const modalTitle = document.getElementById('modalTitle');
  const modalSubtitle = document.getElementById('modalSubtitle');
  const modalBody = document.getElementById('modalBody');
  const modalClose = document.getElementById('modalClose');
  
  // Set title
  modalTitle.textContent = `${mountain.name} - Advanced Weather`;
  modalSubtitle.textContent = `${band.charAt(0).toUpperCase() + band.slice(1)} elevation: ${mountain.bands[band].elev_m} m • 24-hour forecast`;
  
  // Calculate statistics
  const temps = weatherData.map(d => d.temp_c);
  const winds = weatherData.map(d => d.wind_speed_kmh).filter(w => w !== null);
  const precips = weatherData.map(d => d.precip_mm);
  
  const avgTemp = (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1);
  const minTemp = Math.min(...temps);
  const maxTemp = Math.max(...temps);
  const maxWind = Math.max(...winds);
  const totalPrecip = precips.reduce((a, b) => a + b, 0).toFixed(1);
  const snowHours = weatherData.filter(d => d.snow_likely).length;
  
  // Build modal content
  modalBody.innerHTML = `
    <!-- Statistics Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">🌡️ Temperature Range</div>
        <div class="stat-value">${minTemp}° to ${maxTemp}°C</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">📊 Average Temp</div>
        <div class="stat-value">${avgTemp}°C</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">💨 Max Wind</div>
        <div class="stat-value">${maxWind} km/h</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">💧 Total Precipitation</div>
        <div class="stat-value">${totalPrecip} mm</div>
      </div>
      ${snowHours > 0 ? `
      <div class="stat-card">
        <div class="stat-label">❄️ Snow Likely</div>
        <div class="stat-value">${snowHours} hours</div>
      </div>
      ` : ''}
    </div>
    
    <!-- Temperature Chart -->
    <div class="chart-container">
      <div class="chart-title">🌡️ Temperature (24 hours)</div>
      <div class="chart-wrapper">
        <canvas id="tempChart"></canvas>
      </div>
    </div>
    
    <!-- Wind Chart -->
    <div class="chart-container">
      <div class="chart-title">💨 Wind Speed & Gusts (24 hours)</div>
      <div class="chart-wrapper">
        <canvas id="windChart"></canvas>
      </div>
    </div>
    
    <!-- Precipitation Chart -->
    <div class="chart-container">
      <div class="chart-title">💧 Precipitation (24 hours)</div>
      <div class="chart-wrapper">
        <canvas id="precipChart"></canvas>
      </div>
    </div>
    
    <!-- Detailed Hourly Table -->
    <div class="chart-container hourly-detail-table">
      <div class="chart-title">📋 Complete 24-Hour Forecast</div>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Weather</th>
            <th>Temp</th>
            <th>Wind</th>
            <th>Direction</th>
            <th>Gust</th>
            <th>Precip</th>
            <th>Humidity</th>
            <th>Clouds</th>
          </tr>
        </thead>
        <tbody>
          ${weatherData.map(d => `
            <tr>
              <td><strong>${d.time.slice(11, 16)}</strong></td>
              <td>${d.weather_description}${d.snow_likely ? ' ❄️' : ''}</td>
              <td>${d.temp_c}°C</td>
              <td>${d.wind_speed_kmh ?? '-'} km/h</td>
              <td>${d.wind_direction}</td>
              <td>${d.wind_gust_kmh ?? '-'} km/h</td>
              <td>${d.precip_mm} mm</td>
              <td>${d.humidity ?? '-'}%</td>
              <td>${d.cloud_cover ?? '-'}%</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
  
  // Show modal
  modal.classList.add('active');
  
  // Create charts
  setTimeout(() => {
    createCharts(weatherData);
  }, 100);
  
  // Close handlers
  modalClose.onclick = () => modal.classList.remove('active');
  modal.onclick = (e) => {
    if (e.target === modal) modal.classList.remove('active');
  };
}

function createCharts(weatherData) {
  const labels = weatherData.map(d => d.time.slice(11, 16));
  
  // Temperature Chart
  new Chart(document.getElementById('tempChart'), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Temperature (°C)',
        data: weatherData.map(d => d.temp_c),
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: false,
          title: { display: true, text: '°C' }
        }
      }
    }
  });
  
  // Wind Chart
  new Chart(document.getElementById('windChart'), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Wind Speed (km/h)',
          data: weatherData.map(d => d.wind_speed_kmh),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4
        },
        {
          label: 'Gusts (km/h)',
          data: weatherData.map(d => d.wind_gust_kmh),
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          tension: 0.4,
          borderDash: [5, 5]
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'km/h' }
        }
      }
    }
  });
  
  // Precipitation Chart
  new Chart(document.getElementById('precipChart'), {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Precipitation (mm)',
        data: weatherData.map(d => d.precip_mm),
        backgroundColor: weatherData.map(d => 
          d.snow_likely ? 'rgba(59, 130, 246, 0.7)' : 'rgba(16, 185, 129, 0.7)'
        ),
        borderColor: weatherData.map(d => 
          d.snow_likely ? '#3b82f6' : '#10b981'
        ),
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'mm' }
        }
      }
    }
  });
}

// ===================== INITIALIZE ======================
loadMy();