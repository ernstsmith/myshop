document.addEventListener('DOMContentLoaded', function() {

    // =========================
    // 1️⃣ Плавное появление карточек при скролле
    // =========================
    const cards = document.querySelectorAll('.product-card');
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if(entry.isIntersecting){
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    cards.forEach(card => observer.observe(card));

    // =========================
    // 2️⃣ Placeholder для изображений
    // =========================
    document.querySelectorAll('.product-card img').forEach(img => {
        img.onerror = () => img.src = '/static/images/placeholder.png';
    });

    // =========================
    // 3️⃣ Анимация кнопки "Купить"
    // =========================
    document.querySelectorAll('.buy-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            btn.style.transform = 'scale(0.95)';
            setTimeout(() => btn.style.transform = 'scale(1)', 150);
            alert('Товар добавлен в корзину!');
        });
    });

    // =========================
    // 4️⃣ Плавная прокрутка по якорям
    // =========================
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e){
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if(target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // =========================
    // 5️⃣ Закрытие меню Bootstrap после клика на ссылку
    // =========================
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', () => {
            const navbarCollapse = document.getElementById('navbarNav');
            if (navbarCollapse.classList.contains('show')) {
                new bootstrap.Collapse(navbarCollapse).hide();
            }
        });
    });

    // =========================
    // 6️⃣ Скрытие/появление navbar при скролле
    // =========================
    const navbar = document.querySelector('nav.navbar');
    let lastScrollTop = 0;
    window.addEventListener('scroll', () => {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;

        if (scrollTop > lastScrollTop && scrollTop > 50) {
            // Скроллим вниз — скрываем
            navbar.style.transform = 'translateY(-100%)';
        } else {
            // Скроллим вверх — показываем
            navbar.style.transform = 'translateY(0)';
        }

        lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
    });

});
document.addEventListener("DOMContentLoaded", function () {
    const gallerySwiper = new Swiper('.gallery-swiper', {
        loop: true,
        slidesPerView: 1,
        spaceBetween: 10,

        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },

        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
    });
});
