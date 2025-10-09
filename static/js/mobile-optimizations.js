/**
 * Mobile optimizations and cross-browser compatibility for Metlab.edu
 * Handles touch interactions, responsive behavior, and mobile-specific features
 */

class MobileOptimizations {
    constructor() {
        this.isMobile = this.detectMobile();
        this.isTablet = this.detectTablet();
        this.touchSupported = 'ontouchstart' in window;
        this.init();
    }

    init() {
        this.setupViewportHandling();
        this.setupTouchOptimizations();
        this.setupResponsiveNavigation();
        this.setupMobileFormOptimizations();
        this.setupSwipeGestures();
        this.setupPerformanceOptimizations();
        this.setupAccessibilityFeatures();
        this.setupVideoOptimizations();
    }

    detectMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    detectTablet() {
        return /iPad|Android(?!.*Mobile)/i.test(navigator.userAgent);
    }

    setupViewportHandling() {
        // Prevent zoom on input focus for iOS
        if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
            const inputs = document.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.style.fontSize === '' || parseInt(input.style.fontSize) < 16) {
                    input.style.fontSize = '16px';
                }
            });
        }

        // Handle orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.adjustLayoutForOrientation();
            }, 100);
        });
    }

    setupTouchOptimizations() {
        // Add touch-friendly classes to interactive elements
        const interactiveElements = document.querySelectorAll('button, a, input[type="submit"], input[type="button"]');
        interactiveElements.forEach(element => {
            if (!element.classList.contains('btn-touch')) {
                element.classList.add('touch-target');
            }
        });

        // Improve touch feedback
        if (this.touchSupported) {
            document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
            document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
        }
    }

    handleTouchStart(e) {
        const target = e.target.closest('button, a, .touch-target');
        if (target) {
            target.classList.add('touch-active');
        }
    }

    handleTouchEnd(e) {
        const target = e.target.closest('button, a, .touch-target');
        if (target) {
            setTimeout(() => {
                target.classList.remove('touch-active');
            }, 150);
        }
    }

    setupResponsiveNavigation() {
        const nav = document.querySelector('nav');
        if (!nav) return;

        // Create mobile menu toggle if it doesn't exist
        let mobileToggle = nav.querySelector('.mobile-menu-toggle');
        if (!mobileToggle && this.isMobile) {
            mobileToggle = this.createMobileMenuToggle();
            nav.appendChild(mobileToggle);
        }

        // Handle mobile navigation
        if (mobileToggle) {
            mobileToggle.addEventListener('click', this.toggleMobileMenu.bind(this));
        }

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isMobile && !nav.contains(e.target)) {
                this.closeMobileMenu();
            }
        });
    }

    createMobileMenuToggle() {
        const toggle = document.createElement('button');
        toggle.className = 'mobile-menu-toggle md:hidden p-2 rounded-md text-gray-700 hover:text-blue-600';
        toggle.innerHTML = `
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
        `;
        return toggle;
    }

    toggleMobileMenu() {
        const navItems = document.querySelector('.nav-items');
        if (navItems) {
            navItems.classList.toggle('mobile-nav-open');
        }
    }

    closeMobileMenu() {
        const navItems = document.querySelector('.nav-items');
        if (navItems) {
            navItems.classList.remove('mobile-nav-open');
        }
    }

    setupMobileFormOptimizations() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            // Add mobile-friendly classes
            form.classList.add('form-mobile');

            // Optimize input types for mobile keyboards
            const inputs = form.querySelectorAll('input');
            inputs.forEach(input => {
                this.optimizeInputForMobile(input);
            });

            // Handle form submission on mobile
            form.addEventListener('submit', this.handleMobileFormSubmit.bind(this));
        });
    }

    optimizeInputForMobile(input) {
        // Set appropriate input types for mobile keyboards
        if (input.name && input.name.includes('email')) {
            input.type = 'email';
        } else if (input.name && input.name.includes('phone')) {
            input.type = 'tel';
        } else if (input.name && input.name.includes('url')) {
            input.type = 'url';
        }

        // Add autocomplete attributes
        if (input.name === 'username' || input.name === 'email') {
            input.autocomplete = 'username';
        } else if (input.type === 'password') {
            input.autocomplete = 'current-password';
        }
    }

    handleMobileFormSubmit(e) {
        if (this.isMobile) {
            // Scroll to top of form to show any error messages
            const form = e.target;
            setTimeout(() => {
                form.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }
    }

    setupSwipeGestures() {
        const swipeableElements = document.querySelectorAll('.swipeable, .carousel, .slider');
        swipeableElements.forEach(element => {
            this.addSwipeSupport(element);
        });
    }

    addSwipeSupport(element) {
        let startX = 0;
        let startY = 0;
        let distX = 0;
        let distY = 0;
        let threshold = 50;
        let restraint = 100;

        element.addEventListener('touchstart', (e) => {
            const touchobj = e.changedTouches[0];
            startX = touchobj.pageX;
            startY = touchobj.pageY;
        }, { passive: true });

        element.addEventListener('touchend', (e) => {
            const touchobj = e.changedTouches[0];
            distX = touchobj.pageX - startX;
            distY = touchobj.pageY - startY;

            if (Math.abs(distX) >= threshold && Math.abs(distY) <= restraint) {
                const direction = distX < 0 ? 'left' : 'right';
                this.handleSwipe(element, direction);
            }
        }, { passive: true });
    }

    handleSwipe(element, direction) {
        // Dispatch custom swipe event
        const swipeEvent = new CustomEvent('swipe', {
            detail: { direction, element }
        });
        element.dispatchEvent(swipeEvent);

        // Handle common swipe scenarios
        if (element.classList.contains('carousel')) {
            this.handleCarouselSwipe(element, direction);
        }
    }

    handleCarouselSwipe(carousel, direction) {
        const nextBtn = carousel.querySelector('.carousel-next');
        const prevBtn = carousel.querySelector('.carousel-prev');

        if (direction === 'left' && nextBtn) {
            nextBtn.click();
        } else if (direction === 'right' && prevBtn) {
            prevBtn.click();
        }
    }

    setupPerformanceOptimizations() {
        // Lazy load images on mobile
        if (this.isMobile) {
            this.setupLazyLoading();
        }

        // Reduce animations on mobile for better performance
        if (this.isMobile && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.reduceAnimations();
        }

        // Optimize scroll performance
        this.optimizeScrolling();
    }

    setupLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }

    reduceAnimations() {
        const style = document.createElement('style');
        style.textContent = `
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        `;
        document.head.appendChild(style);
    }

    optimizeScrolling() {
        // Use passive event listeners for scroll events
        const scrollElements = document.querySelectorAll('.scroll-container, .overflow-auto');
        scrollElements.forEach(element => {
            element.style.webkitOverflowScrolling = 'touch';
        });
    }

    setupAccessibilityFeatures() {
        // Improve focus visibility on mobile
        const focusableElements = document.querySelectorAll('button, a, input, select, textarea, [tabindex]');
        focusableElements.forEach(element => {
            element.addEventListener('focus', () => {
                element.classList.add('focus-visible-mobile');
            });
            element.addEventListener('blur', () => {
                element.classList.remove('focus-visible-mobile');
            });
        });

        // Add skip links for mobile navigation
        this.addSkipLinks();
    }

    addSkipLinks() {
        const main = document.querySelector('main');
        if (main && !document.querySelector('.skip-link')) {
            const skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.className = 'skip-link sr-only-mobile focus:not-sr-only';
            skipLink.textContent = 'Skip to main content';
            document.body.insertBefore(skipLink, document.body.firstChild);

            main.id = 'main-content';
        }
    }

    setupVideoOptimizations() {
        const videos = document.querySelectorAll('video');
        videos.forEach(video => {
            if (this.isMobile) {
                // Optimize video for mobile
                video.preload = 'metadata';
                video.controls = true;
                
                // Add mobile-specific video controls
                this.addMobileVideoControls(video);
            }
        });
    }

    addMobileVideoControls(video) {
        const container = video.parentElement;
        if (!container.classList.contains('video-mobile-container')) {
            container.classList.add('video-mobile-container');
            
            // Add fullscreen button for mobile
            const fullscreenBtn = document.createElement('button');
            fullscreenBtn.className = 'video-fullscreen-btn';
            fullscreenBtn.innerHTML = '⛶';
            fullscreenBtn.addEventListener('click', () => {
                if (video.requestFullscreen) {
                    video.requestFullscreen();
                } else if (video.webkitRequestFullscreen) {
                    video.webkitRequestFullscreen();
                }
            });
            
            container.appendChild(fullscreenBtn);
        }
    }

    adjustLayoutForOrientation() {
        const orientation = window.orientation;
        document.body.classList.remove('portrait', 'landscape');
        
        if (Math.abs(orientation) === 90) {
            document.body.classList.add('landscape');
        } else {
            document.body.classList.add('portrait');
        }

        // Trigger resize event for charts and other responsive elements
        window.dispatchEvent(new Event('resize'));
    }

    // Public methods for external use
    static getInstance() {
        if (!window.mobileOptimizations) {
            window.mobileOptimizations = new MobileOptimizations();
        }
        return window.mobileOptimizations;
    }

    isMobileDevice() {
        return this.isMobile;
    }

    isTabletDevice() {
        return this.isTablet;
    }

    hasTouchSupport() {
        return this.touchSupported;
    }
}

// Cross-browser compatibility utilities
class CrossBrowserUtils {
    static addEventListenerSafe(element, event, handler, options = false) {
        if (element.addEventListener) {
            element.addEventListener(event, handler, options);
        } else if (element.attachEvent) {
            element.attachEvent('on' + event, handler);
        }
    }

    static removeEventListenerSafe(element, event, handler, options = false) {
        if (element.removeEventListener) {
            element.removeEventListener(event, handler, options);
        } else if (element.detachEvent) {
            element.detachEvent('on' + event, handler);
        }
    }

    static requestAnimationFrameSafe(callback) {
        const raf = window.requestAnimationFrame ||
                   window.webkitRequestAnimationFrame ||
                   window.mozRequestAnimationFrame ||
                   window.oRequestAnimationFrame ||
                   window.msRequestAnimationFrame ||
                   function(callback) { setTimeout(callback, 1000 / 60); };
        
        return raf(callback);
    }

    static getComputedStyleSafe(element, property) {
        if (window.getComputedStyle) {
            return window.getComputedStyle(element)[property];
        } else if (element.currentStyle) {
            return element.currentStyle[property];
        }
        return null;
    }
}

// Initialize mobile optimizations when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    MobileOptimizations.getInstance();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MobileOptimizations, CrossBrowserUtils };
}