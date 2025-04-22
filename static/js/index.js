(function (globals) {
  'use strict';

  function setTheme(themeName) {
    localStorage.setItem('theme', themeName);
    document.documentElement.className = themeName;
    document.querySelector('#theme-control').checked = themeName === 'theme-light';
  }

  globals.toggleTheme = function (checkbox) {
    setTheme(checkbox.checked ? 'theme-light' : 'theme-dark');
  };

  function renderMarkdown() {
    const markdownElements = document.querySelectorAll('.render-marked');
    for (let el of markdownElements) {
      el.innerHTML = globals.marked.parse(el.textContent);
    }
  }

  window.addEventListener('DOMContentLoaded', function () {
    setTheme(localStorage.getItem('theme') || 'theme-dark');
    renderMarkdown();

    // ✅ Only attach size-selector logic on the product page
    if (window.location.pathname === "/") {
      document.querySelectorAll('.size-selector').forEach(select => {
        select.addEventListener('change', updateCart);
      });

      updateCart(); // Trigger once on load
    }
  });

  function updateCart() {
    let qtySmall = 0, qtyMedium = 0, qtyLarge = 0;
    const pricePerUnit = 14.99;
    let productsInCart = [];

    document.querySelectorAll('.product-card').forEach(card => {
      const productId = parseInt(card.dataset.id);

      ['small', 'medium', 'large'].forEach(size => {
        const selector = card.querySelector(`.size-selector[data-size="${size}"]`);
        if (!selector) return;

        const qty = parseInt(selector.value);
        if (qty > 0) {
          productsInCart.push({
            product_id: productId,
            size,
            qty
          });
        }

        if (size === 'small') qtySmall += qty;
        if (size === 'medium') qtyMedium += qty;
        if (size === 'large') qtyLarge += qty;
      });
    });

    const totalQty = qtySmall + qtyMedium + qtyLarge;
    const subtotal = (totalQty * pricePerUnit).toFixed(2);

    if (document.getElementById("qty-small")) {
      document.getElementById("qty-small").textContent = qtySmall;
      document.getElementById("qty-medium").textContent = qtyMedium;
      document.getElementById("qty-large").textContent = qtyLarge;
      document.getElementById("qty-total").textContent = totalQty;
      document.getElementById("subtotal").textContent = subtotal;
    }

    const cartData = {
      small: qtySmall,
      medium: qtyMedium,
      large: qtyLarge,
      total: totalQty,
      pricePerUnit,
      subtotal,
      products: productsInCart
    };

    // ✅ Only save cart if there's something in it
    if (totalQty > 0 || productsInCart.length > 0) {
      localStorage.setItem('cart', JSON.stringify(cartData));
      console.log("🛒 Cart saved:", cartData);
    }
  }

})(this);