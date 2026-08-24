/* ================================================================
   BTS PROJECT — Main JavaScript
   Mobile-first, accessible, SaaS-ready
   ================================================================ */

'use strict';

// ─── Mobile Nav ────────────────────────────────────────────────
const hamburger = document.getElementById('hamburger');
const mobileDrawer = document.getElementById('mobileDrawer');

if (hamburger && mobileDrawer) {
  hamburger.addEventListener('click', () => {
    const open = mobileDrawer.classList.toggle('open');
    hamburger.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
    hamburger.setAttribute('aria-expanded', open);
  });

  // Close on outside tap
  document.addEventListener('click', (e) => {
    if (mobileDrawer.classList.contains('open') &&
        !mobileDrawer.contains(e.target) &&
        !hamburger.contains(e.target)) {
      mobileDrawer.classList.remove('open');
      hamburger.classList.remove('open');
      document.body.style.overflow = '';
    }
  });

  // Close on escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && mobileDrawer.classList.contains('open')) {
      mobileDrawer.classList.remove('open');
      hamburger.classList.remove('open');
      document.body.style.overflow = '';
    }
  });
}

// ─── Toast Notifications ────────────────────────────────────────
function showToast(msg, type = 'info', duration = 3500) {
  // Remove existing toasts
  document.querySelectorAll('.bts-toast').forEach(t => t.remove());

  const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle', info: 'fa-info-circle' };
  const toast = document.createElement('div');
  toast.className = `bts-toast ${type}`;
  toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> ${msg}`;
  document.body.appendChild(toast);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => toast.classList.add('show'));
  });

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

window.showToast = showToast;

// ─── FAQ Accordion ──────────────────────────────────────────────
document.querySelectorAll('.faq-question').forEach(btn => {
  btn.addEventListener('click', () => {
    const isOpen = btn.classList.contains('open');
    // Close all
    document.querySelectorAll('.faq-question').forEach(b => {
      b.classList.remove('open');
      b.nextElementSibling?.classList.remove('open');
      b.setAttribute('aria-expanded', 'false');
    });
    // Open clicked (if was closed)
    if (!isOpen) {
      btn.classList.add('open');
      btn.nextElementSibling?.classList.add('open');
      btn.setAttribute('aria-expanded', 'true');
    }
  });
});

// ─── Cart Badge (live update) ────────────────────────────────────
async function updateCartBadge() {
  try {
    const res = await fetch('/api/cart/', { credentials: 'same-origin' });
    if (!res.ok) return;
    const data = await res.json();
    const badges = document.querySelectorAll('.cart-badge');
    const count = data.total_items || 0;
    badges.forEach(badge => {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    });
  } catch (_) {}
}

// ─── Build Tracker (custom package progress) ─────────────────────
async function updateBuildTracker() {
  const tracker = document.getElementById('build-tracker');
  if (!tracker) return;

  try {
    const res = await fetch('/api/cart/', { credentials: 'same-origin' });
    if (!res.ok) return;
    const data = await res.json();
    const minItems = parseInt(tracker.dataset.min || 5);
    const count = data.custom_item_count || 0;
    const pct   = Math.min((count / minItems) * 100, 100);

    const fill    = document.getElementById('build-progress-fill');
    const countEl = document.getElementById('build-count');
    const lockMsg = document.getElementById('checkout-lock-msg');
    const checkoutBtn = document.getElementById('checkout-btn');

    if (fill)    fill.style.width = pct + '%';
    if (countEl) countEl.textContent = count;

    if (data.can_checkout) {
      lockMsg?.style && (lockMsg.style.display = 'none');
      if (checkoutBtn) {
        checkoutBtn.removeAttribute('disabled');
        checkoutBtn.classList.replace('btn-outline-pink', 'btn-primary');
      }
    } else {
      lockMsg?.style && (lockMsg.style.display = 'flex');
      if (checkoutBtn) {
        checkoutBtn.setAttribute('disabled', '');
        checkoutBtn.classList.replace('btn-primary', 'btn-outline-pink');
      }
    }
  } catch (_) {}
}

// ─── Add to Cart (AJAX) ──────────────────────────────────────────
document.querySelectorAll('.add-to-cart-api').forEach(btn => {
  btn.addEventListener('click', async function () {
    const type = this.dataset.type;
    const id   = this.dataset.id;
    const sizeInput = document.querySelector(`[data-size-select="${id}"]`);
    const size = sizeInput?.value || '';

    const originalHtml = this.innerHTML;
    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    this.disabled = true;

    try {
      const res = await fetch('/api/cart/add/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ type, id, size }),
      });

      if (res.ok) {
        showToast('Added to cart! 🛒', 'success');
        updateCartBadge();
        updateBuildTracker();
      } else {
        const err = await res.json();
        showToast(err.error || 'Could not add to cart', 'error');
      }
    } catch (_) {
      showToast('Network error. Please try again.', 'error');
    } finally {
      this.innerHTML = originalHtml;
      this.disabled = false;
    }
  });
});

// ─── Wishlist Toggle ─────────────────────────────────────────────
document.querySelectorAll('.wishlist-toggle').forEach(btn => {
  btn.addEventListener('click', function () {
    const icon = this.querySelector('i');
    const isActive = this.classList.toggle('active');
    if (icon) icon.className = isActive ? 'fas fa-heart' : 'far fa-heart';
    showToast(isActive ? 'Added to wishlist ❤️' : 'Removed from wishlist', isActive ? 'success' : 'info');
  });
});

// ─── Product Image Gallery ────────────────────────────────────────
document.querySelectorAll('.product-thumb').forEach(thumb => {
  thumb.addEventListener('click', function () {
    const main = document.getElementById('main-product-img');
    if (main) main.src = this.src;
    document.querySelectorAll('.product-thumb').forEach(t => t.classList.remove('active'));
    this.classList.add('active');
  });
});

// ─── Size Selector ────────────────────────────────────────────────
document.querySelectorAll('.size-group').forEach(group => {
  group.querySelectorAll('.size-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      group.querySelectorAll('.size-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const hidden = group.querySelector('[data-size-select]');
      if (hidden) hidden.value = this.dataset.size;
      // Also update any form hidden input
      const productId = hidden?.dataset.sizeSelect;
      const formHidden = document.querySelector(`[data-size-hidden="${productId}"]`);
      if (formHidden) formHidden.value = this.dataset.size;
    });
  });
});

// ─── Scroll Reveal ───────────────────────────────────────────────
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll(
  '.package-card, .product-card, .brand-card, .step-card, .stat-card, .reveal'
).forEach((el, i) => {
  el.classList.add('reveal');
  el.style.transitionDelay = `${(i % 6) * 60}ms`;
  revealObserver.observe(el);
});

// ─── Active Nav Link ─────────────────────────────────────────────
document.querySelectorAll('.nav-links a, .mobile-drawer a').forEach(link => {
  if (link.href === window.location.href ||
      (link.href !== window.location.origin + '/' && window.location.pathname.startsWith(new URL(link.href).pathname))) {
    link.classList.add('active');
  }
});

// ─── Smooth Scroll ───────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const id = a.getAttribute('href').slice(1);
    const target = document.getElementById(id);
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// ─── CSRF Token ──────────────────────────────────────────────────
function getCsrfToken() {
  return document.cookie.split(';')
    .map(c => c.trim().split('='))
    .find(([k]) => k === 'csrftoken')?.[1] || '';
}

// ─── Messages auto-dismiss ────────────────────────────────────────
document.querySelectorAll('.alert[data-auto-dismiss]').forEach(alert => {
  setTimeout(() => {
    alert.style.opacity = '0';
    alert.style.transition = 'opacity 0.4s ease';
    setTimeout(() => alert.remove(), 400);
  }, 4000);
});

// ─── Init ─────────────────────────────────────────────────────────
updateCartBadge();
updateBuildTracker();
