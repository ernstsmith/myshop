// Получение данных о товарах
async function loadProducts() {
    try {
        const response = await fetch('/api/products/');
        const products = await response.json();
        
        // ОТЛАДКА: выводим первый товар в консоль
        console.log('Products:', products);
        if (products.length > 0) {
            console.log('First product image:', products[0].image);
        }
        
        const container = document.getElementById('products');
        container.innerHTML = '';
        
        products.forEach(product => {
            const card = document.createElement('div');
            card.className = 'mini-card';
            
            // Используем Cloudinary для картинок
            const imgSrc = product.image 
                ? `https://res.cloudinary.com/daqsvvw0g/image/upload/${product.image}`
                : '';
            
            card.innerHTML = `
                ${imgSrc ? `<img src="${imgSrc}" alt="${product.title}">` : ''}
                <div class="mini-card-body">
                    <h3 class="mini-card-title">${product.title}</h3>
                    <p class="mini-card-price">${product.price} ₽</p>
                    <button class="mini-btn" type="button">В корзину</button>
                </div>
            `;
            const button = card.querySelector('.mini-btn');
            button.addEventListener('click', () => {
                addToCart(product.id, product.title, product.price);
            });
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Ошибка загрузки товаров:', error);
    }
}

// Функция добавления в корзину
function addToCart(productId, productTitle, productPrice) {
    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const existing = cart.find(item => item.id === productId);
    
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({
            id: productId,
            title: productTitle,
            price: productPrice,
            quantity: 1
        });
    }
    
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartUI();
    
    // Вибрация через Telegram
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }
}

// Обновление отображения корзины
function updateCartUI() {
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const cartLines = document.getElementById('cartLines');
    
    if (cart.length === 0) {
        cartLines.innerHTML = 'Пока пусто';
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.MainButton.hide();
        }
        return;
    }
    
    let total = 0;
    let lines = '';
    
    cart.forEach(item => {
        // Нужно получить цену товара из загруженных данных
        lines += `${item.title || 'Товар'} x${item.quantity}<br>`;
        total += (item.price || 0) * item.quantity;
    });
    
    lines += `<strong>Итого: ${total} ₽</strong>`;
    cartLines.innerHTML = lines;
    
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.MainButton.setText(`Оформить заказ (${total} ₽)`);
        window.Telegram.WebApp.MainButton.show();
        window.Telegram.WebApp.MainButton.onClick(checkout);
    }
}

// Оформление заказа
async function checkout() {
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    if (cart.length === 0) {
        console.log('Корзина пуста');
        return;
    }
    
    // Добавляем CSRF токен
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    const initData = window.Telegram?.WebApp?.initData || '';
    console.log('initData length:', initData.length);
    console.log('initData:', initData.substring(0, 100)); // первые 100 символов
    
    try {
        const response = await fetch('/api/order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                cart: cart.map(item => ({
                    id: item.id,
                    quantity: item.quantity
                })),
                initData: initData
            })
        });
        
        if (response.ok) {
            localStorage.removeItem('cart');
            updateCartUI();
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.showAlert('Заказ оформлен!');
                window.Telegram.WebApp.close();
            }
        } else {
            const error = await response.json();
            console.error('Ошибка:', error);
            alert('Ошибка: ' + JSON.stringify(error));
        }
    } catch (error) {
        console.error('Ошибка оформления:', error);
        alert('Ошибка сети: ' + error.message);
    }
}

// Загрузка данных о товарах при старте
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    updateCartUI();
    
    // Инициализация Telegram WebApp
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
        window.Telegram.WebApp.MainButton.hide();
    }
});
