document.addEventListener('DOMContentLoaded', () => {
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
});
