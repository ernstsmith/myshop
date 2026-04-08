(function () {
  const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
  const CART_KEY = 'miniapp_cart_v1';
  const FALLBACK_IMAGE = '/static/shop/images/tshirt.jpg';

  const productsNode = document.getElementById('products');
  const cartLinesNode = document.getElementById('cartLines');
  const fallbackCheckoutBtn = document.getElementById('fallbackCheckout');

  let products = [];
  let productsSignature = '';
  let cart = loadCart();

  if (tg) {
    tg.ready();
    tg.expand();
  }

  function loadCart() {
    try {
      const raw = localStorage.getItem(CART_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) {
      console.warn('Failed to parse cart from localStorage', e);
      return {};
    }
  }

  function saveCart() {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
  }

  function totalItems() {
    return Object.values(cart).reduce((acc, item) => acc + item.quantity, 0);
  }

  function cartAsList() {
    return Object.values(cart);
  }

  function updateMainButton() {
    const count = totalItems();
    if (!tg) {
      fallbackCheckoutBtn.style.display = count > 0 ? 'block' : 'none';
      return;
    }

    if (count > 0) {
      tg.MainButton.setText(`Оформить заказ (${count})`);
      tg.MainButton.show();
    } else {
      tg.MainButton.hide();
    }
  }

  function renderCartSummary() {
    const items = cartAsList();
    if (items.length === 0) {
      cartLinesNode.textContent = 'Пока пусто';
      return;
    }

    cartLinesNode.innerHTML = items
      .map((item) => `${item.title} x ${item.quantity}`)
      .join('<br>');
  }

  function addToCart(product) {
    const key = String(product.id);
    if (!cart[key]) {
      cart[key] = {
        id: product.id,
        title: product.title,
        price: product.price,
        quantity: 0,
      };
    }
    cart[key].quantity += 1;

    saveCart();
    renderCartSummary();
    updateMainButton();
  }

  function renderProducts() {
    productsNode.innerHTML = '';

    if (!products.length) {
      productsNode.innerHTML = '<p>Товары не найдены</p>';
      return;
    }

    products.forEach((product) => {
      const imageSrc = product.image
        ? `https://res.cloudinary.com/daqsvvw0g/image/upload/${product.image}`
        : FALLBACK_IMAGE;
      const description = product.description || '';
      const card = document.createElement('article');
      card.className = 'mini-card';
      card.innerHTML = `
        <img src="${imageSrc}" alt="${product.title}" style="width:100%;height:180px;object-fit:contain;background:#fff;border-radius:8px;">
        <div class="mini-card-body">
          <h3 class="mini-card-title">${product.title}</h3>
          <p class="mini-card-desc">${description}</p>
          <p class="mini-card-price">${product.price} ₽</p>
          <button class="mini-btn" type="button">Добавить</button>
        </div>
      `;

      const image = card.querySelector('img');
      image.addEventListener('error', function () {
        image.src = FALLBACK_IMAGE;
      });

      const button = card.querySelector('button');
      button.addEventListener('click', function () {
        addToCart(product);
      });

      productsNode.appendChild(card);
    });
  }

  async function loadProducts() {
    try {
      const response = await fetch('/api/products/', { headers: { Accept: 'application/json' } });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const nextProducts = Array.isArray(data) ? data : (data.products || []);
      const nextSignature = JSON.stringify(nextProducts);
      if (nextSignature === productsSignature) {
        return;
      }
      productsSignature = nextSignature;
      products = nextProducts;
      renderProducts();
    } catch (error) {
      console.error('Failed to load products', error);
      productsNode.innerHTML = '<p>Не удалось загрузить товары</p>';
    }
  }

  function checkout() {
    const items = cartAsList();
    if (!items.length) {
      return;
    }

    const payload = {
      type: 'order',
      items: items.map((item) => ({
        id: item.id,
        title: item.title,
        quantity: item.quantity,
      })),
      total_items: totalItems(),
      telegram_user_id: tg && tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : null,
      username: tg && tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.username : '',
      init_data: tg ? tg.initData : '',
      ts: Date.now(),
    };

    if (tg) {
      tg.sendData(JSON.stringify(payload));
    } else {
      console.warn('Telegram WebApp API недоступен, sendData skipped', payload);
    }
  }

  if (tg) {
    tg.MainButton.onClick(checkout);
  }
  fallbackCheckoutBtn.addEventListener('click', checkout);

  renderCartSummary();
  updateMainButton();
  loadProducts();
})();
