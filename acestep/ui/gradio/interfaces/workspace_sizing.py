"""Size the desktop workspace to the space above the persistent player."""
SIZING_JS = """() => {
    window.aceWorkspaceSizingCleanup?.();
    let frame;
    const resize = () => {
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
            const pane = document.getElementById('ace-workspace');
            if (!pane) return;
            const top = pane.getBoundingClientRect().top + window.scrollY;
            const bar = window.matchMedia('(max-width:700px)').matches ? 100 : 78;
            document.documentElement.style.setProperty('--ace-pane-height',
                Math.max(240, window.innerHeight - top - bar - 16) + 'px');
        });
    };
    window.addEventListener('resize', resize);
    const observer = new ResizeObserver(resize);
    const header = document.querySelector('.main-header');
    if (header) observer.observe(header);
    window.aceWorkspaceSizingCleanup = () => {
        window.removeEventListener('resize', resize); observer.disconnect(); cancelAnimationFrame(frame);
    };
    resize();
}"""
