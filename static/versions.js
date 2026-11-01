window.addEventListener('load', () => {

    // Check for the debug param
    const params = new URLSearchParams(window.location.search);
    const isSneaky = params.has('debug') && params.get('debug') === 'true';

    // Populate the version dropdown with all the versions that are present
    const div = document.getElementById('version-dropdown-menu');

    const root = window._CURRENT_ROOT;
    const lang = window._CURRENT_LANG;
    const versions = window._VERSIONS;

    for (const [version, key, sneaky] of versions) {
        if (isSneaky || !sneaky) {
            const a = document.createElement('a');

            a.classList.add('dropdown-item');
            a.href = key === null ? `${root}/${lang}/` : `${root}/${key}/${lang}/`;
            a.innerText = version;

            div.appendChild(a);
        }
    }
})