// Основной JavaScript файл

document.addEventListener('DOMContentLoaded', function() {
    // Устанавливаем текущий год в футере
    const currentYear = document.getElementById('current-year');
    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }
    
    // Инициализация меню для мобильных устройств
    initMobileMenu();
    
    // Инициализация слайдера на главной странице
    if (document.querySelector('.hero-slider')) {
        initHeroSlider();
    }
    
    // Инициализация форм
    initForms();
});

// Мобильное меню
function initMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navMain = document.querySelector('.nav-main');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleMobileMenu();
        });

        // Клик по любой ссылке меню закрывает его - иначе оно
        // оставалось бы открытым при переходе на новую страницу.
        document.querySelectorAll('.nav-link, .contact-btn').forEach(link => {
            link.addEventListener('click', function() {
                closeMobileMenu();
            });
        });

        // Закрытие по клику за пределами меню.
        document.addEventListener('click', function(e) {
            if (navMain && navMain.classList.contains('active') &&
                !navMain.contains(e.target) &&
                !menuToggle.contains(e.target)) {
                closeMobileMenu();
            }
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && navMain && navMain.classList.contains('active')) {
                closeMobileMenu();
            }
        });
    }
    
    function toggleMobileMenu() {
        menuToggle.classList.toggle('active');
        navMain.classList.toggle('active');
        document.body.style.overflow = navMain.classList.contains('active') ? 'hidden' : '';
    }
    
    function closeMobileMenu() {
        menuToggle.classList.remove('active');
        navMain.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Слайдер на главной странице
function initHeroSlider() {
    const slides = document.querySelectorAll('.slide');
    const dots = document.querySelectorAll('.dot');
    const prevBtn = document.querySelector('.slider-prev');
    const nextBtn = document.querySelector('.slider-next');
    
    let currentSlide = 0;
    let slideInterval;
    
    function showSlide(index) {
        slides.forEach(slide => slide.classList.remove('active'));
        dots.forEach(dot => dot.classList.remove('active'));
        slides[index].classList.add('active');
        dots[index].classList.add('active');
        currentSlide = index;
    }
    
    function nextSlide() {
        showSlide((currentSlide + 1) % slides.length);
    }
    
    function prevSlide() {
        showSlide((currentSlide - 1 + slides.length) % slides.length);
    }
    
    function startSlideShow() {
        if (slides.length > 1) {
            slideInterval = setInterval(nextSlide, 5000);
        }
    }
    
    function stopSlideShow() {
        if (slideInterval) clearInterval(slideInterval);
    }
    
    // Ручное переключение слайда сбрасывает автопрокрутку, чтобы
    // следующая смена слайда не происходила сразу после клика.
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            stopSlideShow();
            nextSlide();
            startSlideShow();
        });
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            stopSlideShow();
            prevSlide();
            startSlideShow();
        });
    }
    
    dots.forEach((dot, index) => {
        dot.addEventListener('click', function() {
            stopSlideShow();
            showSlide(index);
            startSlideShow();
        });
    });
    
    const slider = document.querySelector('.hero-slider');
    if (slider) {
        slider.addEventListener('mouseenter', stopSlideShow);
        slider.addEventListener('mouseleave', startSlideShow);
    }
    
    startSlideShow();
}

// Формы
function initForms() {
    const newsletterForms = document.querySelectorAll('.newsletter-form');
    
    newsletterForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const emailInput = this.querySelector('input[type="email"]');
            const email = emailInput.value.trim();
            
            if (validateEmail(email)) {
                showNotification('Спасибо за подписку!');
                emailInput.value = '';
            } else {
                showNotification('Пожалуйста, введите корректный email адрес.', 'error');
                emailInput.focus();
            }
        });
    });
    
    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: ${type === 'success' ? '#8a9b8c' : '#e6c9c9'};
        color: ${type === 'success' ? '#ffffff' : '#333333'};
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        z-index: 3000;
        transform: translateX(150%);
        transition: transform 0.3s ease;
        font-size: 0.9rem;
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.style.transform = 'translateX(0)', 10);
    setTimeout(() => {
        notification.style.transform = 'translateX(150%)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Скрытие шапки при скролле на мобильных
let lastScrollTop = 0;
const header = document.querySelector('.header');
const scrollThreshold = 100;

window.addEventListener('scroll', function() {
    let scrollTop = window.pageYOffset || document.documentElement.scrollTop;

    // Шапка прячется только при скролле вниз дальше порога scrollThreshold
    // и сразу возвращается при скролле вверх.
    if (window.innerWidth <= 768) {
        if (scrollTop > lastScrollTop && scrollTop > scrollThreshold) {
            header.style.transform = 'translateY(-100%)';
            header.style.transition = 'transform 0.3s ease';
        } else if (scrollTop < lastScrollTop) {
            header.style.transform = 'translateY(0)';
        }
    }

    lastScrollTop = scrollTop;
});