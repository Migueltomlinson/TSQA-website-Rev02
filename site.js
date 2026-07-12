// TSQA shared site behaviour (Rev 2 multi-page).
function toggleMenu() {
  var links = document.getElementById('navLinks');
  var btn = document.getElementById('hamburger');
  var open = links.classList.toggle('open');
  if (btn) { btn.setAttribute('aria-expanded', open ? 'true' : 'false'); }
}

window.addEventListener('scroll', function () {
  var nav = document.getElementById('navbar');
  if (nav) {
    if (window.scrollY > 40) { nav.classList.add('scrolled'); }
    else { nav.classList.remove('scrolled'); }
  }
  var grid = document.getElementById('heroGrid');
  if (grid) { grid.style.transform = 'translateY(' + (window.scrollY * 0.25) + 'px)'; }
});

function observeReveal() {
  var reveals = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    reveals.forEach(function (el) { el.classList.add('visible'); });
    return;
  }
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  reveals.forEach(function (el) { observer.observe(el); });
}

async function submitForm() {
  var required = ['f-first', 'f-email', 'f-service'];
  var valid = true;
  required.forEach(function (id) {
    var el = document.getElementById(id);
    if (!el.value.trim()) {
      el.style.borderColor = '#e05252';
      valid = false;
      setTimeout(function () { el.style.borderColor = ''; }, 2000);
    }
  });
  if (!valid) return;

  var btn = document.querySelector('.form-submit');
  btn.textContent = 'Sending...';
  btn.disabled = true;

  var data = {
    firstName: document.getElementById('f-first').value,
    lastName: document.getElementById('f-last').value,
    company: document.getElementById('f-company').value,
    email: document.getElementById('f-email').value,
    phone: document.getElementById('f-phone').value,
    service: document.getElementById('f-service').value,
    message: document.getElementById('f-message').value
  };

  try {
    var response = await fetch('https://formspree.io/f/xvznypvy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(data)
    });
    if (response.ok) {
      document.getElementById('contactFormWrap').style.display = 'none';
      document.getElementById('formSuccess').style.display = 'block';
    } else {
      btn.textContent = 'Something went wrong. Try again.';
      btn.disabled = false;
    }
  } catch (err) {
    btn.textContent = 'Something went wrong. Try again.';
    btn.disabled = false;
  }
}

document.addEventListener('DOMContentLoaded', observeReveal);
