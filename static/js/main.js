document.addEventListener('DOMContentLoaded', function() {

    // 1️⃣ Плавное появление карточек при скролле
    const cards = document.querySelectorAll('.product-card');

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if(entry.isIntersecting){
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); // отключаем наблюдение после появления
            }
        });
    }, { threshold: 0.1 });

    cards.forEach(card => observer.observe(card));

    // 2️⃣ Placeholder для изображений
    document.querySelectorAll('.product-card img').forEach(img => {
        img.onerror = () => img.src = '/static/images/placeholder.png';
    });

    // 3️⃣ Анимация кнопки "Купить"
    document.querySelectorAll('.buy-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault(); // предотвращаем стандартное действие, если нужен AJAX
            btn.style.transform = 'scale(0.95)';
            setTimeout(() => btn.style.transform = 'scale(1)', 150);

            // Пример уведомления пользователя
            alert('Товар добавлен в корзину!');

            // Здесь можно сделать AJAX-запрос к Django view для реального добавления товара:
            // fetch(btn.getAttribute('href'), { method: 'POST' })
            //     .then(response => response.json())
            //     .then(data => console.log(data));
        });
    });

});

document.addEventListener('DOMContentLoaded', () => {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', function(e){
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            target.scrollIntoView({ behavior: 'smooth' });
        });
    });
});

