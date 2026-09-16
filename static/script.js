
const input = document.getElementById('movieInput');
const suggestions = document.getElementById('suggestions');
const btn = document.getElementById('recommendBtn');
const results = document.getElementById('results');
const loader = document.getElementById('loader');

let debounceTimer = null;

input.addEventListener('input', () => {
  clearTimeout(debounceTimer);
  const q = input.value.trim();

  if (!q) {
    suggestions.innerHTML = '';
    return;
  }

  debounceTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/autocomplete?q=${encodeURIComponent(q)}`);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Autocomplete failed');
      }

      suggestions.innerHTML = data.map(t => `<li>${escapeHtml(t)}</li>`).join('');

      document.querySelectorAll('#suggestions li').forEach(li => {
        li.addEventListener('click', () => {
          input.value = li.textContent;
          suggestions.innerHTML = '';
        });
      });
    } catch (e) {
      console.error('Autocomplete error:', e);
      suggestions.innerHTML = '';
    }
  }, 180);
});

document.addEventListener('click', (e) => {
  if (!e.target.closest('.search-box')) suggestions.innerHTML = '';
});

btn.addEventListener('click', getRecommendations);

input.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') getRecommendations();
});

async function getRecommendations() {
  const movie = input.value.trim();

  if (!movie) {
    alert('Please enter a movie name 🎥');
    return;
  }

  suggestions.innerHTML = '';
  results.innerHTML = '';
  loader.classList.remove('hidden');
  btn.disabled = true;

  try {
    const res = await fetch('/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ movie })
    });

    const text = await res.text();
    let data;

    try {
      data = JSON.parse(text);
    } catch {
      throw new Error(`Server returned HTTP ${res.status}, not JSON.`);
    }

    if (!res.ok) {
      throw new Error(data.error || `Server error (${res.status})`);
    }

    if (!Array.isArray(data) || !data.length) {
      results.innerHTML = `<p style="grid-column:1/-1;text-align:center;color:#aaa;">
        😕 No recommendations found. Try a title from the suggestions below, or type a more specific movie name.</p>`;
      return;
    }

    data.forEach((item, i) => {
      const card = document.createElement('div');
      card.className = 'card';
      card.style.animationDelay = `${i * 0.08}s`;

      const img = document.createElement('img');
      img.src = item.poster;
      img.alt = item.title;
      img.onerror = () => {
        img.src = '/static/no-poster.svg';
      };

      const title = document.createElement('div');
      title.className = 'title';
      title.textContent = item.title;

      card.appendChild(img);
      card.appendChild(title);
      results.appendChild(card);
    });

  } catch (err) {
    console.error('Recommendation error:', err);
    results.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;">
        <p style="color:#ff7777;font-size:1.05rem;">Something went wrong 😓</p>
        <p style="color:#aaa;margin-top:8px;">${escapeHtml(err.message)}</p>
      </div>`;
  } finally {
    loader.classList.add('hidden');
    btn.disabled = false;
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
