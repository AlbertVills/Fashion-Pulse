document.addEventListener('DOMContentLoaded', () => {
    const THEME_KEY = 'fashionpulse-theme';
    const rootElement = document.documentElement;

    const applyTheme = (theme) => {
        const normalized = theme === 'dark' ? 'dark' : 'light';
        rootElement.setAttribute('data-theme', normalized);
        try {
            localStorage.setItem(THEME_KEY, normalized);
        } catch (error) {
        }
    };

    const updateThemeButtons = () => {
        const currentTheme = rootElement.getAttribute('data-theme') || 'light';
        document.querySelectorAll('.theme-btn[data-theme-choice]').forEach((button) => {
            const themeChoice = button.dataset.themeChoice || 'light';
            button.classList.toggle('is-active', themeChoice === currentTheme);
        });
    };

    let savedTheme = 'light';
    try {
        savedTheme = localStorage.getItem(THEME_KEY) || rootElement.getAttribute('data-theme') || 'light';
    } catch (error) {
        savedTheme = rootElement.getAttribute('data-theme') || 'light';
    }
    applyTheme(savedTheme);

    const menuToggle = document.getElementById('menuToggle');
    const siteNav = document.getElementById('siteNav');

    if (menuToggle && siteNav) {
        menuToggle.addEventListener('click', () => {
            siteNav.classList.toggle('open');
        });

        document.addEventListener('click', (event) => {
            const clickedInsideNav = siteNav.contains(event.target);
            const clickedToggle = menuToggle.contains(event.target);
            if (!clickedInsideNav && !clickedToggle) {
                siteNav.classList.remove('open');
            }
        });
    }

    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.site-nav a');
    navLinks.forEach((link) => {
        const href = link.getAttribute('href');
        if (!href) {
            return;
        }
        if (href !== '/' && currentPath.startsWith(href)) {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });

    const tagFilters = document.querySelectorAll('.tag-btn');
    const trendItems = document.querySelectorAll('.trend-item');

    if (tagFilters.length && trendItems.length) {
        tagFilters.forEach((button) => {
            button.addEventListener('click', () => {
                tagFilters.forEach((btn) => btn.classList.remove('active'));
                button.classList.add('active');

                const selected = button.dataset.filter;

                trendItems.forEach((item) => {
                    if (selected === 'all') {
                        item.style.display = '';
                        return;
                    }

                    const season = item.dataset.season || '';
                    const theme = item.dataset.theme || '';
                    const style = item.dataset.style || '';
                    const matches = season === selected || theme === selected || style === selected;
                    item.style.display = matches ? '' : 'none';
                });
            });
        });
    }

    const sliderImages = document.querySelectorAll('img[data-slider-images]');
    sliderImages.forEach((image) => {
        const sources = (image.dataset.sliderImages || '')
            .split('|')
            .map((source) => source.trim())
            .filter(Boolean);

        if (sources.length < 2) {
            return;
        }

        const container = image.closest('.hero-feature, .page-banner');
        if (!container) {
            return;
        }

        container.classList.add('slider-draggable');
        image.setAttribute('draggable', 'false');

        let currentIndex = 0;
        let startX = 0;
        let endX = 0;
        let isPointerDown = false;
        const dragThreshold = 45;

        const renderSlide = (newIndex) => {
            currentIndex = (newIndex + sources.length) % sources.length;
            image.classList.add('is-fading');

            window.setTimeout(() => {
                image.src = sources[currentIndex];
            }, 160);

            window.setTimeout(() => {
                image.classList.remove('is-fading');
            }, 320);
        };

        const nextSlide = () => renderSlide(currentIndex + 1);
        const prevSlide = () => renderSlide(currentIndex - 1);

        container.addEventListener('pointerdown', (event) => {
            if (event.button !== 0) {
                return;
            }

            if (event.target.closest('a, button, input, textarea, select, label')) {
                return;
            }

            isPointerDown = true;
            startX = event.clientX;
            endX = event.clientX;
            container.classList.add('is-grabbing');
            if (container.setPointerCapture) {
                container.setPointerCapture(event.pointerId);
            }
            event.preventDefault();
        });

        container.addEventListener('pointermove', (event) => {
            if (!isPointerDown) {
                return;
            }
            endX = event.clientX;
        });

        container.addEventListener('pointerup', (event) => {
            if (!isPointerDown) {
                return;
            }

            endX = event.clientX;
            const deltaX = endX - startX;
            if (deltaX > dragThreshold) {
                prevSlide();
            } else if (deltaX < -dragThreshold) {
                nextSlide();
            }

            isPointerDown = false;
            container.classList.remove('is-grabbing');
            if (container.releasePointerCapture) {
                try {
                    container.releasePointerCapture(event.pointerId);
                } catch (error) {
                }
            }
        });

        container.addEventListener('pointercancel', () => {
            isPointerDown = false;
            container.classList.remove('is-grabbing');
        });

        container.addEventListener('pointerleave', () => {
            if (!isPointerDown) {
                container.classList.remove('is-grabbing');
            }
        });
    });

    const profileImageInput = document.querySelector('input[type="file"][name="profile_image"]');
    const profileImageTrigger = document.getElementById('profileImageTrigger');
    const profileAvatarImage = document.getElementById('profileAvatarImage');
    const profileAvatarFallback = document.getElementById('profileAvatarFallback');

    if (profileImageInput && profileImageTrigger) {
        profileImageTrigger.addEventListener('click', () => {
            profileImageInput.click();
        });
    }

    if (profileImageInput && profileAvatarImage && profileAvatarFallback) {
        profileImageInput.addEventListener('change', (event) => {
            const selectedFile = event.target.files && event.target.files[0];
            if (!selectedFile) {
                return;
            }

            const reader = new FileReader();
            reader.onload = (loadEvent) => {
                profileAvatarImage.src = loadEvent.target?.result || '';
                profileAvatarImage.classList.remove('is-hidden');
                profileAvatarFallback.classList.add('is-hidden');
            };
            reader.readAsDataURL(selectedFile);
        });
    }

    document.addEventListener('click', (event) => {
        const themeButton = event.target.closest('.theme-btn[data-theme-choice]');
        if (!themeButton) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();

        const themeChoice = themeButton.dataset.themeChoice || 'light';
        applyTheme(themeChoice);
        updateThemeButtons();
    });

    updateThemeButtons();

    const outfitPage = document.querySelector('.outfit-page');
    if (outfitPage) {
        const filterButtons = [];
        const outfitCards = outfitPage.querySelectorAll('.outfit-card');
        const searchInput = null;
        const emptyState = outfitPage.querySelector('#outfitEmptyState');
        const cataloguePills = outfitPage.querySelectorAll('.catalogue-pill');
        const carouselTrack = outfitPage.querySelector('#outfitCarouselTrack');
        const carouselPrevBtn = outfitPage.querySelector('.outfit-carousel-btn--prev');
        const carouselNextBtn = outfitPage.querySelector('.outfit-carousel-btn--next');

        cataloguePills.forEach((pill) => {
            pill.addEventListener('click', () => {
                // filter strip removed — catalogue pills are decorative only now
            });
        });

        if (carouselTrack) {
            // Clone cards so the CSS animation loop is seamless
            const originalCards = Array.from(carouselTrack.querySelectorAll('.outfit-card'));
            originalCards.forEach((card) => {
                const clone = card.cloneNode(true);
                clone.setAttribute('aria-hidden', 'true');
                carouselTrack.appendChild(clone);
            });

            // Calculate total width of originals and set animation duration proportionally
            const updateAnimationDuration = () => {
                const totalWidth = originalCards.reduce((sum, card) => {
                    return sum + card.offsetWidth + 16; // 16 = gap
                }, 0);
                // ~80px per second — adjust divisor to change speed
                const duration = Math.max(8, totalWidth / 80);
                carouselTrack.style.animationDuration = duration + 's';
            };

            updateAnimationDuration();
            carouselTrack.classList.add('is-autoscrolling');
            window.addEventListener('resize', updateAnimationDuration);
        }

        const modal = outfitPage.querySelector('#outfitQuickView');
        const modalImage = outfitPage.querySelector('#outfitModalImage');
        const modalCategory = outfitPage.querySelector('#outfitModalCategory');
        const modalTitle = outfitPage.querySelector('#outfitModalTitle');
        const modalDescription = outfitPage.querySelector('#outfitModalDescription');
        const closeTargets = outfitPage.querySelectorAll('[data-modal-close="true"]');
        const quickButtons = outfitPage.querySelectorAll('.outfit-quick-btn');

        const closeModal = () => {
            if (!modal) {
                return;
            }
            modal.classList.add('is-hidden');
            modal.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('modal-open');
        };

        const openModal = (button) => {
            if (!modal || !modalImage || !modalCategory || !modalTitle || !modalDescription) {
                return;
            }

            modalImage.src = button.dataset.image || '';
            modalImage.alt = button.dataset.name || 'Outfit preview';
            modalCategory.textContent = button.dataset.category || '';
            modalTitle.textContent = button.dataset.name || '';
            modalDescription.textContent = button.dataset.description || '';

            modal.classList.remove('is-hidden');
            modal.setAttribute('aria-hidden', 'false');
            document.body.classList.add('modal-open');
        };

        outfitPage.addEventListener('click', (event) => {
            const quickButton = event.target.closest('.outfit-quick-btn');
            if (!quickButton) {
                return;
            }
            event.preventDefault();
            openModal(quickButton);
        });

        quickButtons.forEach((button) => {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                openModal(button);
            });

            button.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    openModal(button);
                }
            });
        });

        closeTargets.forEach((element) => {
            element.addEventListener('click', closeModal);
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                closeModal();
            }
        });

        if (typeof applyOutfitFilters === 'function') {
            applyOutfitFilters();
        }
    }
});
