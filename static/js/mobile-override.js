/**
 * MOBILE OVERRIDE - JavaScript nativo
 * Desabilita completamente AdminLTE/Jazzmin no mobile
 */

(function() {
    'use strict';
    
    // Só executa no mobile
    if (window.innerWidth > 768) return;
    
    console.log('🔧 Mobile Override: Ativando comportamento nativo');
    
    // DESABILITAR BIBLIOTECAS PROBLEMÁTICAS
    function disableProblematicLibraries() {
        // Desabilitar AdminLTE
        if (window.AdminLTE) {
            window.AdminLTE = null;
        }
        
        // Desabilitar Perfect Scrollbar
        if (window.PerfectScrollbar) {
            window.PerfectScrollbar = null;
        }
        
        // Desabilitar OverlayScrollbars
        if (window.OverlayScrollbars) {
            window.OverlayScrollbars = null;
        }
        
        // Desabilitar qualquer inicialização automática
        if (window.jQuery) {
            window.jQuery(document).off('ready');
        }
    }
    
    // IMPLEMENTAR MENU MOBILE SIMPLES
    function initSimpleMobileMenu() {
        const sidebar = document.querySelector('.main-sidebar');
        const toggleButton = document.querySelector('[data-widget="pushmenu"]') || 
                           document.querySelector('.navbar-toggler');
        
        if (!sidebar || !toggleButton) {
            console.log('⚠️ Elementos não encontrados');
            return;
        }
        
        // Criar overlay se não existir
        let overlay = document.querySelector('.mobile-sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'mobile-sidebar-overlay';
            document.body.appendChild(overlay);
        }
        
        // Função para abrir menu
        function openMenu() {
            sidebar.classList.add('mobile-open');
            overlay.classList.add('show');
            document.body.style.overflow = 'hidden';
            console.log('📱 Menu aberto');
        }
        
        // Função para fechar menu
        function closeMenu() {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('show');
            document.body.style.overflow = '';
            console.log('📱 Menu fechado');
        }
        
        // Event listeners
        toggleButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (sidebar.classList.contains('mobile-open')) {
                closeMenu();
            } else {
                openMenu();
            }
        });
        
        overlay.addEventListener('click', closeMenu);
        
        // Fechar com ESC
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeMenu();
            }
        });
        
        console.log('✅ Menu mobile simples inicializado');
    }
    
    // FIX PARA CAMPOS DE FORMULÁRIO
    function fixFormFields() {
        const inputs = document.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            // Garantir font-size 16px para evitar zoom
            input.style.fontSize = '16px';
            
            // Fix para campos que não respondem
            input.addEventListener('touchstart', function(e) {
                e.stopPropagation();
                setTimeout(() => this.focus(), 100);
            }, { passive: false });
            
            // Fix específico para selects
            if (input.tagName === 'SELECT') {
                input.addEventListener('touchend', function(e) {
                    e.preventDefault();
                    this.focus();
                    this.click();
                }, { passive: false });
            }
        });
        
        console.log(`✅ ${inputs.length} campos de formulário corrigidos`);
    }
    
    // FORÇAR SCROLL NATIVO
    function forceNativeScroll() {
        const scrollElements = document.querySelectorAll('.main-sidebar .sidebar, .nav-sidebar');
        
        scrollElements.forEach(el => {
            // Remover classes problemáticas
            el.classList.remove('os-content', 'perfect-scrollbar', 'ps');
            
            // Forçar scroll nativo
            el.style.overflow = 'auto';
            el.style.overflowY = 'auto';
            el.style.overflowX = 'hidden';
            el.style.webkitOverflowScrolling = 'touch';
            
            // Remover event listeners problemáticos
            const newElement = el.cloneNode(true);
            el.parentNode.replaceChild(newElement, el);
        });
        
        console.log('✅ Scroll nativo forçado');
    }
    
    // INICIALIZAÇÃO
    function init() {
        console.log('🚀 Iniciando Mobile Override...');
        
        disableProblematicLibraries();
        
        // Aguardar DOM estar pronto
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(() => {
                    initSimpleMobileMenu();
                    fixFormFields();
                    forceNativeScroll();
                }, 100);
            });
        } else {
            setTimeout(() => {
                initSimpleMobileMenu();
                fixFormFields();
                forceNativeScroll();
            }, 100);
        }
    }
    
    // Executar imediatamente
    init();
    
})();