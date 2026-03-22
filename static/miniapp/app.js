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
                    <button class="mini-btn" onclick="addToCart(${product.id})">В корзину</button>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Ошибка загрузки товаров:', error);
    }
}

// Функция добавления в корзину
function addToCart(productId) {
    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const existing = cart.find(item => item.id === productId);
    
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({ id: productId, quantity: 1 });
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
    if (cart.length === 0) return;
    
    const initData = window.Telegram?.WebApp?.initData || '';
    
    try {
        const response = await fetch('/api/order/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cart: cart,
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
            throw new Error('Ошибка');
        }
    } catch (error) {
        console.error('Ошибка оформления:', error);
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.showAlert('Ошибка при оформлении заказа');
        }
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
