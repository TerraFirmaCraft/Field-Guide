
async function loadIndex() {
    const response = await fetch(`/${getBaseUrl()}/${getLang()}/search_index.json`);
    return response.json();
}

function getQuery() {
    const params = new URLSearchParams(window.location.search);
    return params.get('q') || '';
}

function getLang() {
    const pathParts = window.location.pathname.split('/').filter(Boolean);
    return pathParts.length > 0 ? pathParts[isLocal() ? 0 : 1] : '';
}

// Detect if we're on GitHub Pages (production) or localhost (dev)
function isLocal() {
    return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
}

function getBaseUrl() {
    return isLocal() ? '' : '/Field-Guide';
}

function boldQuery(text, query) {
    if (!query) return text;
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<b>$1</b>');
}

async function performSearch(query) {
    const data = await loadIndex();
    const fuse = new Fuse(data, {
        keys: ['content'],
        includeScore: true,
        threshold: 0.1,          // higher = more lenient
        ignoreLocation: true,    // disable position penalty
        minMatchCharLength: 2,   // ignore single-letter queries
    });

    let results = fuse.search(query);
    const seenUrls = new Set();
    results = results.filter(r => {
        if (seenUrls.has(r.item.url)) {
            return false;
        }
        seenUrls.add(r.item.url);
        return true;
    });
    const resultsList = document.getElementById('results');
    resultsList.innerHTML = results
    .map(r => `<li><a href="${r.item.url}">${r.item.entry}</a><p>${boldQuery(r.item.content, query)}</p></li>`)
    .join('') || '<li>No results found.</li>';
}

const input = document.getElementById('search-box');
const query = getQuery();

input.value = query;
if (query) performSearch(query);

document.getElementById('search-box').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      const query = encodeURIComponent(this.value.trim());
      if (!query) return;

      const target = `/${getBaseUrl()}/${getLang()}/search.html?q=${query}`;

      window.location.href = target;
    }
});

function handleSearch(e) {
    e.preventDefault(); // Prevent page reload
    const query = document.getElementById('search-box').value.trim();
    if (!query) return;
    const target = `/${getBaseUrl()}/${getLang()}/search.html?q=${query}`;
    window.location.href = target;
}