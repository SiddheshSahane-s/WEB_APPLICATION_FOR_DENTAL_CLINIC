document.addEventListener('DOMContentLoaded', () => {

    // ── Hide Loader ──────────────────────────────────────────────
    const loader = document.getElementById('loader');
    if (loader) {
        setTimeout(() => loader.classList.add('hidden'), 600);
    }

    // ── Navbar Scroll Effect ─────────────────────────────────────
    const navbar = document.getElementById('navbar');
    const onScroll = () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        // Scroll-top button
        if (scrollTop) {
            scrollTop.classList.toggle('show', window.scrollY > 500);
        }
    };
    window.addEventListener('scroll', onScroll, { passive: true });

    // ── Mobile Hamburger ─────────────────────────────────────────
    const hamburger = document.getElementById('hamburger');
    const navLinks  = document.getElementById('navLinks');
    if (hamburger && navLinks) {
        hamburger.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            hamburger.classList.toggle('active');
        });
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!navbar.contains(e.target)) {
                navLinks.classList.remove('active');
                hamburger.classList.remove('active');
            }
        });
    }

    // ── Theme Toggle ─────────────────────────────────────────────
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon   = document.getElementById('themeIcon');
    const html        = document.documentElement;

    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const cur     = html.getAttribute('data-theme');
            const newTheme = cur === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
            // Small visual ripple on theme change
            document.body.style.transition = 'background-color 0.6s ease, color 0.6s ease';
        });
    }

    function updateThemeIcon(theme) {
        if (!themeIcon) return;
        themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }

    // ── Scroll to Top ─────────────────────────────────────────────
    const scrollTop = document.getElementById('scrollTop');
    if (scrollTop) {
        scrollTop.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ── Auto-hide Toasts ──────────────────────────────────────────
    document.querySelectorAll('.toast').forEach(toast => {
        setTimeout(() => {
            toast.style.transform = 'translateX(120%)';
            setTimeout(() => toast.remove(), 400);
        }, 5000);
    });

    // ── Testimonial Slider ────────────────────────────────────────
    initSlider();

    // ── Navbar dropdown mobile toggle ─────────────────────────────
    document.querySelectorAll('.nav-dropdown > .nav-link, .nav-dropdown > button').forEach(link => {
        link.addEventListener('click', function (e) {
            if (window.innerWidth <= 992) {
                e.preventDefault();
                const parent = this.closest('.nav-dropdown');
                parent.classList.toggle('active');
            }
        });
    });

    // ── Smooth hover tilt on spec cards ──────────────────────────
    document.querySelectorAll('.spec-card, .blog-card, .cta-card').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect  = card.getBoundingClientRect();
            const x     = ((e.clientX - rect.left) / rect.width  - 0.5) * 6;
            const y     = ((e.clientY - rect.top)  / rect.height - 0.5) * -6;
            card.style.transform = `translateY(-8px) rotateX(${y}deg) rotateY(${x}deg) scale(1.02)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });

    // ── Ripple effect on buttons ──────────────────────────────────
    document.querySelectorAll('.btn, .btn-hero-primary, .btn-hero-whatsapp, .btn-primary-sm').forEach(btn => {
        btn.addEventListener('click', function (e) {
            const ripple = document.createElement('span');
            const rect   = this.getBoundingClientRect();
            const size   = Math.max(rect.width, rect.height);
            ripple.style.cssText = `
                position:absolute;
                border-radius:50%;
                width:${size}px; height:${size}px;
                left:${e.clientX - rect.left - size/2}px;
                top:${e.clientY - rect.top - size/2}px;
                background:rgba(255,255,255,0.35);
                transform:scale(0);
                animation:ripple-expand 0.6s ease-out forwards;
                pointer-events:none;
                z-index:100;
            `;
            if (!this.style.position || this.style.position === 'static') {
                this.style.position = 'relative';
            }
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 700);
        });
    });

    // Inject ripple keyframe
    if (!document.getElementById('ripple-style')) {
        const s = document.createElement('style');
        s.id = 'ripple-style';
        s.textContent = `@keyframes ripple-expand { to { transform: scale(2.5); opacity: 0; } }`;
        document.head.appendChild(s);
    }

    // ── Animate numbers in feature strip ─────────────────────────
    // Already handled in index.html extra_js via IntersectionObserver

});

// ── Slider ────────────────────────────────────────────────────────
function initSlider() {
    const slider = document.getElementById('testimonialsSlider');
    if (!slider) return;

    const cards   = Array.from(slider.querySelectorAll('.testimonial-card'));
    if (cards.length === 0) return;

    const dotsContainer = document.getElementById('sliderDots');
    let current = 0;
    let autoTimer;

    // Build dots
    if (dotsContainer) {
        cards.forEach((_, i) => {
            const dot = document.createElement('div');
            dot.className = 'slider-dot' + (i === 0 ? ' active' : '');
            dot.addEventListener('click', () => goTo(i));
            dotsContainer.appendChild(dot);
        });
    }

    // Hide all except first
    cards.forEach((card, i) => {
        card.style.display     = i === 0 ? 'block' : 'none';
        card.style.animation   = '';
    });

    function goTo(index) {
        cards[current].style.display = 'none';
        current = (index + cards.length) % cards.length;
        const card = cards[current];
        card.style.display = 'block';
        card.style.animation = 'none';
        requestAnimationFrame(() => {
            card.style.animation = 'slideIn 0.5s cubic-bezier(0.34,1.2,0.64,1) both';
        });
        // Update dots
        if (dotsContainer) {
            dotsContainer.querySelectorAll('.slider-dot').forEach((d, i) => {
                d.classList.toggle('active', i === current);
            });
        }
    }

    // Inject slide animation
    if (!document.getElementById('slider-style')) {
        const s = document.createElement('style');
        s.id = 'slider-style';
        s.textContent = `@keyframes slideIn { from { opacity:0; transform:translateX(40px) scale(0.97); } to { opacity:1; transform:translateX(0) scale(1); } }`;
        document.head.appendChild(s);
    }

    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) nextBtn.addEventListener('click', () => { clearInterval(autoTimer); goTo(current + 1); startAuto(); });
    if (prevBtn) prevBtn.addEventListener('click', () => { clearInterval(autoTimer); goTo(current - 1); startAuto(); });

    function startAuto() {
        autoTimer = setInterval(() => goTo(current + 1), 4500);
    }
    startAuto();
}
