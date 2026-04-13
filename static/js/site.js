document.addEventListener('DOMContentLoaded', () => {
    const THEME_KEY = 'fashionpulse-theme';
    const rootElement = document.documentElement;
    const body = document.body;

    if (body) {
        window.requestAnimationFrame(() => {
            body.classList.remove('page-is-loading');
            body.classList.add('page-is-ready');
        });
    }

    const mainContent = document.querySelector('.page-content');
    const revealTargets = mainContent
        ? Array.from(mainContent.querySelectorAll([
            ':scope > section',
            ':scope > article',
            ':scope > div:not(.alert)',
            '.cards-grid > *',
            '.masonry-grid > *',
            '.outfit-grid > *',
            '.user-gallery-grid > *',
            '.trend-banner-thumbs > *'
        ].join(', '))).filter((element, index, elements) => {
            return !element.classList.contains('alert') && elements.indexOf(element) === index;
        })
        : [];

    if (revealTargets.length) {
        revealTargets.forEach((element, index) => {
            element.classList.add('page-section-reveal');
            element.style.setProperty('--section-delay', `${Math.min((index % 6) * 40, 160)}ms`);
        });

        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            revealTargets.forEach((element) => element.classList.add('is-visible'));
        } else {
            const observer = new IntersectionObserver((entries, sectionObserver) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) {
                        return;
                    }
                    entry.target.classList.add('is-visible');
                    sectionObserver.unobserve(entry.target);
                });
            }, {
                threshold: 0.02,
                rootMargin: '0px 0px -4% 0px',
            });

            revealTargets.forEach((element) => observer.observe(element));
        }
    }

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
    const siteHeader = document.querySelector('.site-header');
    const scrollProgressBar = document.getElementById('scrollProgressBar');
    let scrollTicking = false;

    const updateScrollEffects = () => {
        const scrollTop = window.scrollY || document.documentElement.scrollTop || 0;
        const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
        const progress = documentHeight > 0 ? Math.min(100, (scrollTop / documentHeight) * 100) : 0;

        if (scrollProgressBar) {
            scrollProgressBar.style.transform = `scaleX(${progress / 100})`;
        }

        if (siteHeader) {
            siteHeader.classList.toggle('is-scrolled', scrollTop > 12);
        }

        scrollTicking = false;
    };

    updateScrollEffects();
    window.addEventListener('scroll', () => {
        if (scrollTicking) {
            return;
        }
        scrollTicking = true;
        window.requestAnimationFrame(updateScrollEffects);
    }, { passive: true });

    if (menuToggle && siteNav) {
        const closeNavMenu = () => {
            siteNav.classList.remove('open');
            menuToggle.setAttribute('aria-expanded', 'false');
        };

        menuToggle.setAttribute('aria-expanded', 'false');

        menuToggle.addEventListener('click', () => {
            const isOpen = siteNav.classList.toggle('open');
            menuToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });

        document.addEventListener('click', (event) => {
            const clickedInsideNav = siteNav.contains(event.target);
            const clickedToggle = menuToggle.contains(event.target);
            if (!clickedInsideNav && !clickedToggle) {
                closeNavMenu();
            }
        });

        siteNav.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                closeNavMenu();
            });
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

        // Build dot indicators
        const dotsWrapper = document.createElement('div');
        dotsWrapper.className = 'hero-slider-dots';
        sources.forEach((_, i) => {
            const dot = document.createElement('button');
            dot.className = 'hero-slider-dot' + (i === 0 ? ' is-active' : '');
            dot.setAttribute('aria-label', 'Go to slide ' + (i + 1));
            dot.addEventListener('click', () => renderSlide(i));
            dotsWrapper.appendChild(dot);
        });
        container.appendChild(dotsWrapper);

        const updateDots = () => {
            dotsWrapper.querySelectorAll('.hero-slider-dot').forEach((dot, i) => {
                dot.classList.toggle('is-active', i === currentIndex);
            });
        };

        const renderSlide = (newIndex) => {
            currentIndex = (newIndex + sources.length) % sources.length;
            image.classList.add('is-fading');

            window.setTimeout(() => {
                image.src = sources[currentIndex];
            }, 160);

            window.setTimeout(() => {
                image.classList.remove('is-fading');
            }, 320);

            updateDots();
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

        // Auto-advance
        const interval = parseInt(image.dataset.sliderInterval, 10) || 4500;
        let autoTimer = window.setInterval(() => renderSlide(currentIndex + 1), interval);
        container.addEventListener('pointerdown', () => {
            window.clearInterval(autoTimer);
        });
        container.addEventListener('pointerup', () => {
            autoTimer = window.setInterval(() => renderSlide(currentIndex + 1), interval);
        });
    });

    const trendCarousel = document.querySelector('[data-trend-carousel]');
    if (trendCarousel) {
        const bannerRoot = trendCarousel.closest('.trend-banner-gallery');
        let animationId = null;
        let lastFrameTime = 0;
        const scrollSpeed = 0.035;
        let resumeAfterManualTimer = null;
        const fillThreshold = 520;
        const maxDeckMultiplier = 10;

        const originals = Array.from(trendCarousel.children);
        const makeDeck = () => {
            const fragment = document.createDocumentFragment();
            originals.forEach((item) => {
                const clone = item.cloneNode(true);
                clone.setAttribute('aria-hidden', 'true');
                fragment.appendChild(clone);
            });
            return fragment;
        };

        if (originals.length > 1) {
            trendCarousel.appendChild(makeDeck());
        }

        const trimDecks = () => {
            if (!originals.length) {
                return;
            }
            const maxCards = originals.length * maxDeckMultiplier;
            while (trendCarousel.children.length > maxCards) {
                let removedWidth = 0;
                for (let index = 0; index < originals.length; index += 1) {
                    const firstCard = trendCarousel.firstElementChild;
                    if (!firstCard) {
                        break;
                    }
                    removedWidth += firstCard.getBoundingClientRect().width + 13;
                    trendCarousel.removeChild(firstCard);
                }
                trendCarousel.scrollLeft = Math.max(0, trendCarousel.scrollLeft - removedWidth);
            }
        };

        const ensureForwardBuffer = (extraAhead = 0) => {
            if (!originals.length) {
                return;
            }

            let safetyCounter = 0;
            let remaining = trendCarousel.scrollWidth - (trendCarousel.scrollLeft + trendCarousel.clientWidth + extraAhead);
            while (remaining < fillThreshold && safetyCounter < 4) {
                trendCarousel.appendChild(makeDeck());
                safetyCounter += 1;
                remaining = trendCarousel.scrollWidth - (trendCarousel.scrollLeft + trendCarousel.clientWidth + extraAhead);
            }
            trimDecks();
        };

        const ensureBackwardBuffer = () => {
            if (!originals.length) {
                return;
            }
            if (trendCarousel.scrollLeft > fillThreshold) {
                return;
            }
            const previousWidth = trendCarousel.scrollWidth;
            trendCarousel.prepend(makeDeck());
            const addedWidth = trendCarousel.scrollWidth - previousWidth;
            trendCarousel.scrollLeft += addedWidth;
            trimDecks();
        };

        const getStep = () => {
            const firstCard = trendCarousel.querySelector('.trend-banner-card');
            if (!firstCard) {
                return 180;
            }
            return firstCard.getBoundingClientRect().width + 13;
        };

        const slide = (direction) => {
            stopAutoSlide();
            const step = getStep();
            if (direction > 0) {
                // Pre-fill enough cards for burst clicks so the physical end is never reached.
                ensureForwardBuffer(step * 4);
            } else {
                ensureBackwardBuffer();
            }

            trendCarousel.scrollBy({
                left: direction * step,
                behavior: 'smooth',
            });

            if (direction > 0) {
                window.setTimeout(() => ensureForwardBuffer(step * 2), 280);
            }

            if (resumeAfterManualTimer) {
                window.clearTimeout(resumeAfterManualTimer);
            }
            resumeAfterManualTimer = window.setTimeout(() => {
                startAutoSlide();
            }, 900);
        };

        const tick = (timestamp) => {
            if (!lastFrameTime) {
                lastFrameTime = timestamp;
            }
            const delta = timestamp - lastFrameTime;
            lastFrameTime = timestamp;

            ensureForwardBuffer(220);
            trendCarousel.scrollLeft += delta * scrollSpeed;

            animationId = window.requestAnimationFrame(tick);
        };

        const startAutoSlide = () => {
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                return;
            }
            if (animationId) {
                window.cancelAnimationFrame(animationId);
            }
            lastFrameTime = 0;
            animationId = window.requestAnimationFrame(tick);
        };

        const stopAutoSlide = () => {
            if (animationId) {
                window.cancelAnimationFrame(animationId);
                animationId = null;
            }
        };

        if (bannerRoot) {
            bannerRoot.addEventListener('click', (event) => {
                const clickedCard = event.target.closest('.trend-banner-card');
                if (!clickedCard || !trendCarousel.contains(clickedCard)) {
                    return;
                }

                const trackRect = trendCarousel.getBoundingClientRect();
                const cardRect = clickedCard.getBoundingClientRect();
                const trackMid = trackRect.left + (trackRect.width / 2);
                const cardMid = cardRect.left + (cardRect.width / 2);
                const direction = cardMid >= trackMid ? 1 : -1;

                slide(direction);
            });
        }

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                stopAutoSlide();
                return;
            }
            startAutoSlide();
        });

        startAutoSlide();
    }

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

    // ── Password visibility toggle (global) ─────────────────────────────────
    const passwordInputs = Array.from(document.querySelectorAll('input[type="password"]'));
    passwordInputs.forEach((input) => {
        if (input.closest('.pw-toggle-wrap')) {
            return;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'pw-toggle-wrap';

        const toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'pw-toggle-btn';
        toggle.setAttribute('aria-label', 'Show password');
        toggle.setAttribute('aria-pressed', 'false');
        toggle.innerHTML = '<svg class="pw-eye-open" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg><svg class="pw-eye-closed" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:none"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';

        const parent = input.parentNode;
        if (!parent) {
            return;
        }

        parent.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        wrapper.appendChild(toggle);

        toggle.addEventListener('click', () => {
            const isHidden = input.type === 'password';
            input.type = isHidden ? 'text' : 'password';
            // Fix: Show open eye when visible, closed eye when hidden
            toggle.querySelector('.pw-eye-open').style.display = isHidden ? '' : 'none';
            toggle.querySelector('.pw-eye-closed').style.display = isHidden ? 'none' : '';
            toggle.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password');
            toggle.setAttribute('aria-pressed', isHidden ? 'true' : 'false');
        });
    });

    document.addEventListener('click', (event) => {
        const toggleButton = event.target.closest('.gallery-comments-toggle');
        if (!toggleButton) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();

        const commentsId = toggleButton.getAttribute('aria-controls');
        if (!commentsId) {
            return;
        }

        const commentsBlock = document.getElementById(commentsId);
        if (!commentsBlock) {
            return;
        }

        const postContainer = toggleButton.closest('.gallery-item, .user-post-modal-content');
        if (!postContainer) {
            return;
        }

        const currentlyVisible = window.getComputedStyle(commentsBlock).display !== 'none';
        const isOpen = !currentlyVisible;

        commentsBlock.style.display = isOpen ? 'block' : 'none';
        postContainer.classList.toggle('comments-open', isOpen);
        toggleButton.setAttribute('aria-expanded', isOpen ? 'true' : 'false');

        if (isOpen) {
            const commentInput = commentsBlock.querySelector('input[id^="comment-input-"]');
            if (commentInput) {
                commentInput.focus();
            }
        }
    });

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
            // Clone each direct track item so linked cards keep their anchor wrapper.
            const originalItems = Array.from(carouselTrack.children);
            const originalCards = originalItems.map((item) => item.querySelector('.outfit-card')).filter(Boolean);

            originalItems.forEach((item) => {
                const clone = item.cloneNode(true);
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

    // ── Trend Article Slider ──────────────────────────────────────────
    (function () {
        const viewport = document.querySelector('[data-trend-slider]');
        if (!viewport) return;

        const cards = Array.from(viewport.querySelectorAll('.trend-slider-card'));
        const dotsContainer = document.querySelector('[data-trend-dots]');
        if (!cards.length) return;

        let current = 0;
        const total = cards.length;
        let isTransitioning = false;
        const TRANSITION_MS = 540;

        if (dotsContainer) {
            cards.forEach(function (_, i) {
                const dot = document.createElement('button');
                dot.className = 'trend-slider-dot';
                dot.setAttribute('aria-label', 'Slide ' + (i + 1));
                dot.addEventListener('click', function () { goTo(i); });
                dotsContainer.appendChild(dot);
            });
        }

        function getOffset(cardIndex, activeIndex) {
            let diff = ((cardIndex - activeIndex) % total + total) % total;
            if (diff > Math.floor(total / 2)) diff -= total;
            return diff;
        }

        function update() {
            cards.forEach(function (card, i) {
                card.classList.remove('pos-active', 'pos-prev', 'pos-prev2', 'pos-next', 'pos-next2');
                const offset = getOffset(i, current);
                if (offset === 0)       card.classList.add('pos-active');
                else if (offset === -1) card.classList.add('pos-prev');
                else if (offset === -2) card.classList.add('pos-prev2');
                else if (offset === 1)  card.classList.add('pos-next');
                else if (offset === 2)  card.classList.add('pos-next2');
            });
            if (dotsContainer) {
                const dots = dotsContainer.querySelectorAll('.trend-slider-dot');
                dots.forEach(function (d, i) {
                    d.classList.toggle('is-active', i === current);
                });
            }
        }

        function goTo(index) {
            if (isTransitioning) return;
            isTransitioning = true;
            viewport.classList.add('is-transitioning');
            current = ((index % total) + total) % total;
            update();
            window.setTimeout(function () {
                isTransitioning = false;
                viewport.classList.remove('is-transitioning');
            }, TRANSITION_MS);
        }

        const prevBtn = document.querySelector('.trend-slider-prev');
        const nextBtn = document.querySelector('.trend-slider-next');
        if (prevBtn) prevBtn.addEventListener('click', function () { goTo(current - 1); });
        if (nextBtn) nextBtn.addEventListener('click', function () { goTo(current + 1); });

        // Click a side card to navigate to it
        cards.forEach(function (card, i) {
            card.addEventListener('click', function (e) {
                if (e.target.closest('form') || e.target.closest('.trend-slider-cta-btn') || e.target.closest('.trend-slider-icon-btn')) return;
                if (!card.classList.contains('pos-active')) {
                    e.preventDefault();
                    goTo(i);
                }
            });
        });

        // Swipe support
        let touchStartX = 0;
        viewport.addEventListener('touchstart', function (e) {
            touchStartX = e.touches[0].clientX;
        }, { passive: true });
        viewport.addEventListener('touchend', function (e) {
            const dx = e.changedTouches[0].clientX - touchStartX;
            if (Math.abs(dx) > 48) goTo(dx < 0 ? current + 1 : current - 1);
        }, { passive: true });

        // Keyboard navigation
        document.addEventListener('keydown', function (e) {
            if (!document.querySelector('.trend-slider-section')) return;
            if (e.key === 'ArrowLeft')  goTo(current - 1);
            if (e.key === 'ArrowRight') goTo(current + 1);
        });

        update();
    }());

    // ── Toast system ──────────────────────────────────────────────────────────
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    window.showToast = (message, type) => {
        const toastType = type || 'success';
        const toast = document.createElement('div');
        toast.className = 'toast toast--' + toastType;
        toast.setAttribute('role', 'status');
        toast.setAttribute('aria-live', 'polite');
        toast.innerHTML = '<span class="toast__msg">' + message + '</span>'
            + '<button class="toast__close" aria-label="Dismiss">&times;</button>';
        toastContainer.appendChild(toast);

        window.requestAnimationFrame(() => {
            window.requestAnimationFrame(() => toast.classList.add('toast--show'));
        });

        const dismissToast = () => {
            toast.classList.remove('toast--show');
            toast.addEventListener('transitionend', () => {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, { once: true });
        };
        toast.querySelector('.toast__close').addEventListener('click', dismissToast);
        window.setTimeout(dismissToast, 4000);
    };

    // Convert existing Django alert messages to auto-dismissing toasts
    document.querySelectorAll('.alert').forEach((alert) => {
        const text = alert.textContent.trim();
        if (text) {
            const isError = alert.classList.contains('alert-error') || alert.classList.contains('error');
            window.showToast(text, isError ? 'error' : 'success');
        }
        if (alert.parentNode) alert.parentNode.removeChild(alert);
    });

    // ── Back-to-top button ────────────────────────────────────────────────────
    const backToTop = document.createElement('button');
    backToTop.id = 'backToTop';
    backToTop.className = 'back-to-top';
    backToTop.setAttribute('aria-label', 'Back to top');
    backToTop.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor"'
        + ' stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        + '<polyline points="18 15 12 9 6 15"></polyline></svg>';
    document.body.appendChild(backToTop);

    window.addEventListener('scroll', () => {
        backToTop.classList.toggle('is-visible', window.scrollY > 300);
    }, { passive: true });
    backToTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // ── AJAX gallery heart toggle ─────────────────────────────────────────────
    document.addEventListener('submit', (event) => {
        const form = event.target.closest('.gallery-heart-form');
        if (!form) return;
        event.preventDefault();

        const action = form.getAttribute('action');
        const csrfToken = (form.querySelector('[name="csrfmiddlewaretoken"]') || {}).value || '';

        fetch(action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
            body: new URLSearchParams({ csrfmiddlewaretoken: csrfToken }),
        })
        .then((r) => r.json())
        .then((data) => {
            if (!data.ok) return;
            const heartBtn = form.querySelector('.gallery-heart-btn');
            if (heartBtn) {
                heartBtn.classList.toggle('is-liked', data.liked);
                const path = heartBtn.querySelector('path');
                if (path) {
                    path.setAttribute('d', data.liked
                        ? 'M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z'
                        : 'M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z'
                    );
                }
            }
            const item = form.closest('.gallery-item, .user-post-modal-content');
            if (item) {
                const summary = item.querySelector('.gallery-like-summary');
                if (summary) {
                    summary.textContent = data.like_count + (data.like_count === 1 ? ' heart' : ' hearts');
                }
            }
            window.showToast(data.liked ? 'Added to hearts!' : 'Heart removed.');
        })
        .catch(() => {});
    });

    // ── AJAX gallery comment submit ───────────────────────────────────────────
    document.addEventListener('submit', (event) => {
        const form = event.target.closest('.gallery-comment-form');
        if (!form) return;
        event.preventDefault();

        const action = form.getAttribute('action');
        const input = form.querySelector('input[name="comment"]');
        if (!input || !input.value.trim()) return;

        const csrfToken = (form.querySelector('[name="csrfmiddlewaretoken"]') || {}).value || '';
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.disabled = true;

        fetch(action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
            body: new URLSearchParams({ csrfmiddlewaretoken: csrfToken, comment: input.value.trim() }),
        })
        .then((r) => r.json())
        .then((data) => {
            if (!data.ok) {
                window.showToast(data.error || 'Failed to post comment.', 'error');
                return;
            }
            const item = form.closest('.gallery-item, .user-post-modal-content, .tad-comments');
            if (item) {
                const list = item.querySelector('.gallery-comment-list');
                if (list) {
                    const li = document.createElement('li');
                    const deleteUrl = '/gallery/comment/' + data.comment_id + '/delete/';
                    li.innerHTML = '<div class="gallery-comment-head"><strong>'
                        + data.username + '</strong>'
                        + '<form method="post" action="' + deleteUrl + '" class="gallery-comment-delete-form" data-confirm="Delete this comment?">'
                        + '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrfToken + '">'
                        + '<button type="submit" class="gallery-comment-delete-btn">Delete</button>'
                        + '</form>'
                        + '</div><span>' + data.text + '</span>';
                    li.classList.add('comment-new');
                    list.prepend(li);
                    const emptyItem = Array.from(list.querySelectorAll('li.meta'))
                        .find((el) => el.textContent.includes('No comments'));
                    if (emptyItem) emptyItem.remove();
                }
                const title = item.querySelector('.gallery-comments-title');
                if (title) title.textContent = 'Comments (' + data.comment_count + ')';
            }
            input.value = '';
            window.showToast('Comment posted!');
        })
        .catch(() => window.showToast('Failed to post comment.', 'error'))
        .finally(() => { if (submitBtn) submitBtn.disabled = false; });
    });

    // ── AJAX gallery comment delete ───────────────────────────────────────────
    document.addEventListener('submit', (event) => {
        const form = event.target.closest('.gallery-comment-delete-form');
        if (!form) return;
        event.preventDefault();
        event.stopImmediatePropagation();

        const confirmMsg = form.getAttribute('data-confirm');
        if (confirmMsg && typeof window.confirmModal === 'function') {
            window.confirmModal(confirmMsg, 'This action cannot be undone.').then((ok) => {
                if (ok) performCommentDelete(form);
            });
            return;
        }
        performCommentDelete(form);
    }, true);

    function performCommentDelete(form) {
        const action = form.getAttribute('action');
        const csrfToken = (form.querySelector('[name="csrfmiddlewaretoken"]') || {}).value || '';
        const btn = form.querySelector('button[type="submit"]');
        if (btn) btn.disabled = true;

        fetch(action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
            body: new URLSearchParams({ csrfmiddlewaretoken: csrfToken }),
        })
        .then((r) => r.json())
        .then((data) => {
            if (!data.ok) {
                window.showToast(data.error || 'Failed to delete comment.', 'error');
                return;
            }
            const li = form.closest('li');
            const container = li ? li.closest('.gallery-item, .user-post-modal-content, .tad-comments') : null;
            if (li) li.remove();

            if (container) {
                const title = container.querySelector('.gallery-comments-title');
                if (title) title.textContent = 'Comments (' + data.comment_count + ')';
                const list = container.querySelector('.gallery-comment-list');
                if (list && !list.querySelector('li:not(.meta)')) {
                    const empty = document.createElement('li');
                    empty.className = 'meta';
                    empty.textContent = 'No comments yet.';
                    list.appendChild(empty);
                }
            }
            window.showToast('Comment deleted.');
        })
        .catch(() => window.showToast('Failed to delete comment.', 'error'))
        .finally(() => { if (btn) btn.disabled = false; });
    }

    // ── Contact form — char counter + live validation ─────────────────────────
    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
        const messageField = contactForm.querySelector('#id_message, textarea[name="message"]');
        if (messageField) {
            const maxLen = parseInt(messageField.getAttribute('maxlength'), 10) || 1000;
            const counter = document.createElement('p');
            counter.className = 'contact-char-counter';
            counter.textContent = '0 / ' + maxLen;
            messageField.parentNode.insertBefore(counter, messageField.nextSibling);

            messageField.addEventListener('input', () => {
                const len = messageField.value.length;
                counter.textContent = len + ' / ' + maxLen;
                counter.classList.toggle('contact-char-counter--warn', len > Math.floor(maxLen * 0.9));
            });
        }

        contactForm.querySelectorAll('input, textarea').forEach((field) => {
            if (!field.name) return;
            field.addEventListener('blur', () => {
                const isEmpty = !field.value.trim();
                field.classList.toggle('input--error', isEmpty);
                let errMsg = field.parentNode.querySelector('.inline-error');
                if (isEmpty) {
                    if (!errMsg) {
                        errMsg = document.createElement('p');
                        errMsg.className = 'inline-error';
                        errMsg.textContent = 'This field is required.';
                        field.parentNode.appendChild(errMsg);
                    }
                } else {
                    if (errMsg) errMsg.remove();
                }
            });

            field.addEventListener('input', () => {
                if (field.value.trim()) {
                    field.classList.remove('input--error');
                    const errMsg = field.parentNode.querySelector('.inline-error');
                    if (errMsg) errMsg.remove();
                }
            });
        });
    }

    // ── Outfit live search filter ─────────────────────────────────────────────
    const outfitSearchInput = document.getElementById('outfitSearch');
    if (outfitSearchInput) {
        const outfitTiles = document.querySelectorAll('.outfit-tile');
        const outfitEmptyEl = document.getElementById('outfitEmptyState');

        outfitSearchInput.addEventListener('input', () => {
            const query = outfitSearchInput.value.trim().toLowerCase();
            let visible = 0;
            outfitTiles.forEach((tile) => {
                const name = (tile.dataset.name || '').toLowerCase();
                const cat = (tile.dataset.category || '').toLowerCase();
                const matches = !query || name.includes(query) || cat.includes(query);
                const wrapper = tile.closest('a') || tile;
                wrapper.style.display = matches ? '' : 'none';
                if (matches) visible++;
            });
            if (outfitEmptyEl) outfitEmptyEl.classList.toggle('is-hidden', visible > 0);
        });
    }

    /* ── Nav user dropdown toggle ── */
    const navUserToggle = document.getElementById('navUserToggle');
    const navUserDropdown = document.getElementById('navUserDropdown');
    if (navUserToggle && navUserDropdown) {
        const galleryUrl = navUserToggle.dataset.galleryUrl;
        const onGalleryPage = galleryUrl && window.location.pathname === new URL(galleryUrl, window.location.origin).pathname;
        const navUserWrap = navUserToggle.closest('.nav-user-wrap');

        function toggleDropdown(open) {
            const isOpen = typeof open === 'boolean' ? open : !navUserDropdown.classList.contains('open');
            navUserDropdown.classList.toggle('open', isOpen);
            if (navUserWrap) navUserWrap.classList.toggle('is-open', isOpen);
        }

        navUserToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            if (onGalleryPage) {
                toggleDropdown();
            } else {
                window.location.href = galleryUrl;
            }
        });
        document.addEventListener('click', (e) => {
            if (!navUserDropdown.contains(e.target) && e.target !== navUserToggle) {
                toggleDropdown(false);
            }
        });
    }
});
