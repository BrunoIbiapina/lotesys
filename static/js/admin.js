/**
 * LoteSys Admin - Enhanced JavaScript
 * Modern interactions and mobile responsiveness
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // ====== Mobile Sidebar Toggle ======
    function initMobileSidebar() {
        const sidebarToggle = document.querySelector('[data-widget="pushmenu"]') || 
                             document.querySelector('.navbar-toggler') ||
                             document.querySelector('[data-toggle="sidebar"]');
        const body = document.body;
        
        // Criar overlay para mobile se não existir
        if (!document.querySelector('.sidebar-overlay')) {
            const overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            overlay.style.cssText = `
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                background: rgba(0, 0, 0, 0.5) !important;
                z-index: 999 !important;
                display: none !important;
                opacity: 0 !important;
                transition: opacity 0.3s ease !important;
            `;
            overlay.addEventListener('click', () => {
                closeSidebar();
            });
            document.body.appendChild(overlay);
        }
        
        function openSidebar() {
            body.classList.add('sidebar-open');
            const overlay = document.querySelector('.sidebar-overlay');
            if (overlay) {
                overlay.style.display = 'block';
                setTimeout(() => overlay.style.opacity = '1', 10);
            }
            
            // Focar no primeiro link do menu
            setTimeout(() => {
                const firstNavLink = document.querySelector('.nav-sidebar .nav-link');
                if (firstNavLink) {
                    firstNavLink.focus();
                }
            }, 300);
            
            // Prevenir scroll do body
            document.body.style.overflow = 'hidden';
        }
        
        function closeSidebar() {
            body.classList.remove('sidebar-open');
            const overlay = document.querySelector('.sidebar-overlay');
            if (overlay) {
                overlay.style.opacity = '0';
                setTimeout(() => overlay.style.display = 'none', 300);
            }
            
            // Restaurar scroll do body
            document.body.style.overflow = '';
        }
        
        function toggleSidebar() {
            if (body.classList.contains('sidebar-open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        }
        
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                if (window.innerWidth <= 768) {
                    toggleSidebar();
                } else {
                    // Comportamento padrão para desktop
                    body.classList.toggle('sidebar-collapse');
                }
            });
        }
        
        // Fechar sidebar com ESC no mobile
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && window.innerWidth <= 768) {
                closeSidebar();
            }
        });
        
        // Melhorar scroll da sidebar no mobile
        const sidebar = document.querySelector('.main-sidebar .sidebar') ||
                       document.querySelector('.main-sidebar .nav-sidebar') ||
                       document.querySelector('.main-sidebar');
        
        if (sidebar) {
            // Fix scroll no mobile
            sidebar.addEventListener('touchstart', function(e) {
                const startY = e.touches[0].clientY;
                const scrollTop = sidebar.scrollTop;
                const maxScroll = sidebar.scrollHeight - sidebar.clientHeight;
                
                // Se no topo e tentando scrollar para cima, ou no final e tentando scrollar para baixo
                if ((scrollTop <= 0 && startY < e.touches[0].clientY) || 
                    (scrollTop >= maxScroll && startY > e.touches[0].clientY)) {
                    e.preventDefault();
                }
            }, { passive: false });
            
            // Scroll suave para links ativos
            const activeLink = sidebar.querySelector('.nav-link.active');
            if (activeLink) {
                setTimeout(() => {
                    activeLink.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center',
                        inline: 'nearest'
                    });
                }, 500);
            }
        }
        
        // Fechar sidebar ao redimensionar janela
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                closeSidebar();
            }
        });
    }
    
    // ====== Enhanced Form Interactions ======
    function initFormEnhancements() {
        // Auto-focus first input in forms
        const firstInput = document.querySelector('.form-row:first-child input:not([readonly]):not([disabled])');
        if (firstInput) {
            firstInput.focus();
        }
        
        // Corrigir problemas de foco em mobile
        if (window.innerWidth <= 768) {
            // Prevenir zoom no iOS
            const inputs = document.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                if (input.style.fontSize !== '16px') {
                    input.style.fontSize = '16px';
                }
                
                // Fix para campos que não respondem ao toque
                input.addEventListener('touchstart', function(e) {
                    e.stopPropagation();
                    this.focus();
                }, { passive: false });
                
                // Melhorar resposta ao toque
                input.addEventListener('click', function(e) {
                    e.stopPropagation();
                    if (!this.matches(':focus')) {
                        this.focus();
                    }
                });
            });
            
            // Fix para selects que não abrem
            const selects = document.querySelectorAll('select');
            selects.forEach(select => {
                select.addEventListener('touchend', function(e) {
                    e.preventDefault();
                    this.focus();
                    // Simular click para abrir o select
                    const event = new MouseEvent('mousedown', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    this.dispatchEvent(event);
                }, { passive: false });
            });
        }
        
        // Add loading state to submit buttons
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function() {
                const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.textContent = submitBtn.textContent.replace(/Save|Salvar|Submit/, 'Salvando...');
                    submitBtn.classList.add('loading');
                }
            });
        });
        
        // Enhanced form validation feedback
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('invalid', function() {
                this.classList.add('is-invalid');
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid') && this.validity.valid) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });
    }
    
    // ====== Table Enhancements ======
    function initTableEnhancements() {
        // Add hover effects to table rows
        const tableRows = document.querySelectorAll('.results tbody tr');
        tableRows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
        
        // Make entire row clickable if it has a link
        tableRows.forEach(row => {
            const link = row.querySelector('a');
            if (link) {
                row.style.cursor = 'pointer';
                row.addEventListener('click', function(e) {
                    // Don't trigger if clicking on actual links, buttons, or checkboxes
                    if (!e.target.matches('a, button, input[type="checkbox"], input[type="radio"]')) {
                        link.click();
                    }
                });
            }
        });
    }
    
    // ====== Success Animations ======
    function initSuccessAnimations() {
        // Animate success messages
        const messages = document.querySelectorAll('.alert-success, .messagelist .success');
        messages.forEach(message => {
            message.classList.add('success-animation');
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                message.style.opacity = '0';
                message.style.transform = 'translateY(-20px)';
                setTimeout(() => {
                    message.remove();
                }, 300);
            }, 5000);
        });
    }
    
    // ====== Search Enhancements ======
    function initSearchEnhancements() {
        const searchInput = document.querySelector('#searchbar');
        if (searchInput) {
            // Add search icon
            const searchIcon = document.createElement('span');
            searchIcon.innerHTML = '<i class="fas fa-search"></i>';
            searchIcon.style.cssText = `
                position: absolute;
                right: 12px;
                top: 50%;
                transform: translateY(-50%);
                color: #6b7280;
                pointer-events: none;
            `;
            
            const searchContainer = searchInput.parentElement;
            searchContainer.style.position = 'relative';
            searchContainer.appendChild(searchIcon);
            
            // Add clear button when typing
            searchInput.addEventListener('input', function() {
                if (this.value.length > 0 && !searchContainer.querySelector('.clear-search')) {
                    const clearBtn = document.createElement('button');
                    clearBtn.innerHTML = '<i class="fas fa-times"></i>';
                    clearBtn.className = 'clear-search';
                    clearBtn.type = 'button';
                    clearBtn.style.cssText = `
                        position: absolute;
                        right: 40px;
                        top: 50%;
                        transform: translateY(-50%);
                        background: none;
                        border: none;
                        color: #6b7280;
                        cursor: pointer;
                        padding: 4px;
                        border-radius: 50%;
                    `;
                    
                    clearBtn.addEventListener('click', () => {
                        searchInput.value = '';
                        clearBtn.remove();
                        searchInput.focus();
                    });
                    
                    searchContainer.appendChild(clearBtn);
                } else if (this.value.length === 0) {
                    const clearBtn = searchContainer.querySelector('.clear-search');
                    if (clearBtn) clearBtn.remove();
                }
            });
        }
    }
    
    // ====== Responsive Table Wrapper ======
    function initResponsiveTables() {
        const tables = document.querySelectorAll('table:not(.table-responsive table)');
        tables.forEach(table => {
            if (!table.closest('.table-responsive')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'table-responsive';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
        });
    }
    
    // ====== Smooth Scrolling for Anchors ======
    function initSmoothScrolling() {
        const links = document.querySelectorAll('a[href^="#"]');
        links.forEach(link => {
            link.addEventListener('click', function(e) {
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
    
    // ====== Keyboard Shortcuts ======
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + S to save forms
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                const saveBtn = document.querySelector('input[name="_save"], input[name="_continue"], .submit-row input[type="submit"]');
                if (saveBtn) {
                    e.preventDefault();
                    saveBtn.click();
                }
            }
            
            // Escape to close modals/sidebars
            if (e.key === 'Escape') {
                document.body.classList.remove('sidebar-open');
            }
            
            // Ctrl/Cmd + / to focus search
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                const searchInput = document.querySelector('#searchbar, input[name="q"]');
                if (searchInput) {
                    e.preventDefault();
                    searchInput.focus();
                }
            }
        });
    }
    
    // ====== Enhanced Select2 Integration ======
    function initSelect2Enhancements() {
        // Wait for Select2 to initialize
        setTimeout(() => {
            const select2Elements = document.querySelectorAll('.select2-container');
            select2Elements.forEach(container => {
                container.style.borderRadius = 'var(--border-radius)';
            });
        }, 100);
    }
    
    // ====== Toast Notifications ======
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-lg);
            z-index: 9999;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
    
    // ====== Initialize All Features ======
    initMobileSidebar();
    initFormEnhancements();
    initTableEnhancements();
    initSuccessAnimations();
    initSearchEnhancements();
    initResponsiveTables();
    initSmoothScrolling();
    initKeyboardShortcuts();
    initSelect2Enhancements();
    
    // ====== Window Resize Handler ======
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            // Close sidebar on desktop
            if (window.innerWidth > 768) {
                document.body.classList.remove('sidebar-open');
            }
        }, 250);
    });
    
    // ====== Performance: Lazy Load Images ======
    if ('IntersectionObserver' in window) {
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    }
    
    console.log('🚀 LoteSys Admin Enhanced - Loaded successfully!');
});

// ====== Utility Functions ======
window.LoteSysAdmin = {
    showToast: function(message, type = 'info') {
        // This function is now available globally
        return showToast(message, type);
    },
    
    refreshPage: function() {
        window.location.reload();
    },
    
    goBack: function() {
        window.history.back();
    }
};