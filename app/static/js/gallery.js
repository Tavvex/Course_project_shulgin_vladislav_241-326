// Галерея портфолио

document.addEventListener('DOMContentLoaded', function() {
    initFiltersAndSorting();
    initLightbox();
    initModalWithData();
});

function initFiltersAndSorting() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const statusButtons = document.querySelectorAll('.status-btn');
    const sortButtons = document.querySelectorAll('.sort-btn');
    const portfolioGrid = document.getElementById('portfolio-grid');

    if (!portfolioGrid) return;

    let currentFilter = 'all';
    let currentStatus = 'all';
    let currentSort = 'newest';

    // Фильтрация и сортировка выполняются на стороне клиента: карточки
    // не скрываются полностью, а переставляются через CSS order,
    // поэтому переключение фильтров происходит без перезагрузки страницы.
    function updateDisplay() {
        const items = document.querySelectorAll('.portfolio-item');
        const visibleItems = [];
        const hiddenItems = [];

        items.forEach(item => {
            const categories = item.getAttribute('data-category');
            const status = item.getAttribute('data-status');

            const categoryMatch = currentFilter === 'all' || categories === currentFilter;
            const statusMatch = currentStatus === 'all' || status === currentStatus;

            if (categoryMatch && statusMatch) {
                visibleItems.push(item);
            } else {
                hiddenItems.push(item);
            }
        });

        visibleItems.sort((a, b) => {
            const yearA = parseInt(a.getAttribute('data-year'));
            const yearB = parseInt(b.getAttribute('data-year'));
            return currentSort === 'newest' ? yearB - yearA : yearA - yearB;
        });

        visibleItems.forEach((item, index) => {
            item.style.order = index;
            item.style.display = 'block';
        });

        hiddenItems.forEach((item, index) => {
            item.style.order = visibleItems.length + index;
            item.style.display = 'none';
        });
    }
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentFilter = this.getAttribute('data-filter');
            updateDisplay();
        });
    });
    
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            statusButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentStatus = this.getAttribute('data-status');
            updateDisplay();
        });
    });
    
    sortButtons.forEach(button => {
        button.addEventListener('click', function() {
            sortButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentSort = this.getAttribute('data-sort');
            updateDisplay();
        });
    });
    
    updateDisplay();
}

function initModalWithData() {
    const viewButtons = document.querySelectorAll('.view-details');
    const workModal = document.getElementById('work-modal');

    // window.worksData приходит из шаблона портфолио (works_data | tojson).
    if (!workModal || !window.worksData) return;

    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const workId = parseInt(this.getAttribute('data-work'));
            const work = window.worksData.find(w => w.id === workId);

            if (work) {
                document.getElementById('modal-work-title').textContent = `"${work.title}"`;
                document.getElementById('modal-work-details').textContent = `${work.technique} • ${work.size} • ${work.year}`;
                document.getElementById('modal-work-description').textContent = work.description || 'Описание работы будет добавлено позже.';
                // Путь к изображению хранится в image_path и относится к папке portfolio.
                document.getElementById('modal-work-image').src = work.image_path
                    ? `/static/images/portfolio/${work.image_path}`
                    : '';
                document.getElementById('modal-work-image').alt = work.title;

                workModal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        });
    });
    
    const closeButtons = workModal.querySelectorAll('.modal-close, .modal-close-btn');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            workModal.classList.remove('active');
            document.body.style.overflow = '';
        });
    });
    
    workModal.addEventListener('click', function(e) {
        if (e.target === this) {
            this.classList.remove('active');
            document.body.style.overflow = '';
        }
    });
}

// Полноэкранный просмотр изображений портфолио с переключением
// между работами стрелками и клавиатурой.
function initLightbox() {
    const galleryImages = document.querySelectorAll('.portfolio-image img');
    if (!galleryImages.length) return;

    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox';
    lightbox.innerHTML = `
        <div class="lightbox-content">
            <span class="lightbox-close">&times;</span>
            <img src="" alt="" class="lightbox-img">
            <div class="lightbox-caption"></div>
            <button class="lightbox-prev"><i class="fas fa-chevron-left"></i></button>
            <button class="lightbox-next"><i class="fas fa-chevron-right"></i></button>
        </div>
    `;
    document.body.appendChild(lightbox);
    
    let currentIndex = 0;
    const images = Array.from(galleryImages);
    
    galleryImages.forEach((img, index) => {
        img.style.cursor = 'pointer';
        img.addEventListener('click', function(e) {
            e.stopPropagation();
            currentIndex = index;
            updateLightbox();
            lightbox.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    });
    
    function updateLightbox() {
        const lightboxImg = lightbox.querySelector('.lightbox-img');
        const caption = lightbox.querySelector('.lightbox-caption');
        const currentImg = images[currentIndex];
        
        lightboxImg.src = currentImg.src;
        lightboxImg.alt = currentImg.alt;
        
        const workCard = currentImg.closest('.portfolio-card');
        const workTitle = workCard.querySelector('.portfolio-info h3');
        const workDetails = workCard.querySelector('.portfolio-info p');
        
        if (workTitle && workDetails) {
            caption.innerHTML = `<h3>${workTitle.textContent}</h3><p>${workDetails.textContent}</p>`;
        }
    }
    
    lightbox.querySelector('.lightbox-close').addEventListener('click', function() {
        lightbox.classList.remove('active');
        document.body.style.overflow = 'auto';
    });
    
    lightbox.addEventListener('click', function(e) {
        if (e.target === lightbox) {
            lightbox.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    });
    
    lightbox.querySelector('.lightbox-prev').addEventListener('click', function(e) {
        e.stopPropagation();
        currentIndex = (currentIndex - 1 + images.length) % images.length;
        updateLightbox();
    });
    
    lightbox.querySelector('.lightbox-next').addEventListener('click', function(e) {
        e.stopPropagation();
        currentIndex = (currentIndex + 1) % images.length;
        updateLightbox();
    });
    
    document.addEventListener('keydown', function(e) {
        if (!lightbox.classList.contains('active')) return;
        
        if (e.key === 'Escape') {
            lightbox.classList.remove('active');
            document.body.style.overflow = 'auto';
        } else if (e.key === 'ArrowLeft') {
            currentIndex = (currentIndex - 1 + images.length) % images.length;
            updateLightbox();
        } else if (e.key === 'ArrowRight') {
            currentIndex = (currentIndex + 1) % images.length;
            updateLightbox();
        }
    });
}

// Стили для лайтбокса
const lightboxStyles = `
.lightbox {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.3s ease, visibility 0.3s ease;
}
.lightbox.active {
    opacity: 1;
    visibility: visible;
}
.lightbox-content {
    position: relative;
    max-width: 90%;
    max-height: 90%;
}
.lightbox-img {
    max-width: 100%;
    max-height: 80vh;
    display: block;
    border-radius: 8px;
    box-shadow: 0 5px 25px rgba(0, 0, 0, 0.5);
}
.lightbox-caption {
    position: absolute;
    bottom: -70px;
    left: 0;
    width: 100%;
    color: white;
    text-align: center;
    padding: 10px;
}
.lightbox-caption h3 {
    color: white;
    margin-bottom: 5px;
    font-size: 1.3rem;
}
.lightbox-caption p {
    color: #ccc;
    margin: 0;
    font-size: 0.9rem;
}
.lightbox-close {
    position: absolute;
    top: -40px;
    right: 0;
    color: white;
    font-size: 2rem;
    cursor: pointer;
    transition: color 0.3s ease;
}
.lightbox-close:hover {
    color: #8a9b8c;
}
.lightbox-prev, .lightbox-next {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background-color: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    font-size: 1.2rem;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    cursor: pointer;
    transition: background-color 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}
.lightbox-prev:hover, .lightbox-next:hover {
    background-color: rgba(138, 155, 140, 0.7);
}
.lightbox-prev { left: -70px; }
.lightbox-next { right: -70px; }
@media (max-width: 767px) {
    .lightbox-prev, .lightbox-next {
        width: 40px;
        height: 40px;
        font-size: 1rem;
    }
    .lightbox-prev { left: 10px; }
    .lightbox-next { right: 10px; }
    .lightbox-caption { bottom: -80px; }
    .lightbox-caption h3 { font-size: 1.1rem; }
}
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = lightboxStyles;
document.head.appendChild(styleSheet);