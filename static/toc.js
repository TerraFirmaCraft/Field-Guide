// Scrolls the current entry into view within the contents list, so long categories don't hide where you are
(function () {
    const toc = document.getElementById('site-toc');
    const current = toc?.querySelector('a[aria-current="page"]');
    if (!current) {
        return;
    }

    function reveal(scroller) {
        if (scroller.scrollHeight > scroller.clientHeight) {
            const offset = current.getBoundingClientRect().top - scroller.getBoundingClientRect().top;
            scroller.scrollTop += offset - scroller.clientHeight / 3;
        }
    }

    // Desktop: the sticky sidebar scrolls itself
    reveal(toc);

    // Mobile: the drawer body scrolls once opened
    toc.addEventListener('shown.bs.offcanvas', () => reveal(toc.querySelector('.offcanvas-body')));
})();
