const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

console.log("Telegram user:", tg.initDataUnsafe?.user);

const mainButton = tg.MainButton;

mainButton.setText("Оформить заказ");
mainButton.show();

mainButton.onClick(function () {
    alert("Заказ отправлен");
});

const mainButton = tg.MainButton;

mainButton.setText("Оформить заказ");
mainButton.show();

mainButton.onClick(function () {
    alert("Заказ отправлен");
});

document.addEventListener('DOMContentLoaded', function() {

    // =========================
    // 1️⃣ Placeholder для изображений
    // =========================
    document.querySelectorAll('.product-card img').forEach(img => {
        img.onerror = () => img.src = '/static/images/test-img.jpg';
    });

    // =========================
    // 2️⃣ Анимация кнопки "Купить"
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
    // 3️⃣ Плавная прокрутка по якорям
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
    // 4️⃣ Закрытие меню Bootstrap после клика на ссылку
    // =========================
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', () => {
            const navbarCollapse = document.getElementById('navbarNav');
            if (navbarCollapse.classList.contains('show')) {
                new bootstrap.Collapse(navbarCollapse).hide();
            }
        });
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
