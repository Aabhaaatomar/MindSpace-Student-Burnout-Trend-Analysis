/*
    MindSpace - Client Javascript Controllers
*/

document.addEventListener('DOMContentLoaded', () => {
    // 1. Theme (Dark / Light) Controller
    const themeToggle = document.getElementById('theme-toggle');
    const htmlEl = document.documentElement;
    
    // Check initial theme settings
    const currentTheme = localStorage.getItem('theme') || 'light';
    htmlEl.setAttribute('data-theme', currentTheme);
    updateThemeToggleIcon(currentTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const activeTheme = htmlEl.getAttribute('data-theme');
            const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
            
            htmlEl.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeToggleIcon(newTheme);
            
            showToast(`Switched to ${newTheme} mode!`, 'info');
            
            // Dispatch custom event to let charts re-draw with adjusted colors if listening
            window.dispatchEvent(new Event('themeChanged'));
        });
    }

    function updateThemeToggleIcon(theme) {
        if (!themeToggle) return;
        const icon = themeToggle.querySelector('i');
        if (icon) {
            if (theme === 'dark') {
                icon.className = 'bi bi-sun-fill text-warning';
            } else {
                icon.className = 'bi bi-moon-stars-fill text-primary';
            }
        }
    }

    // 2. Dynamic Toast Notification Engine
    window.showToast = function(message, type = 'info') {
        let toastContainer = document.querySelector('.toast-container-custom');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container-custom';
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        toast.className = `toast-custom border-start border-4`;
        
        let iconClass = 'bi-info-circle-fill text-primary';
        let borderColor = 'border-primary';
        
        if (type === 'success') {
            iconClass = 'bi-check-circle-fill text-success';
            borderColor = 'border-success';
            toast.style.borderColor = 'var(--accent)';
        } else if (type === 'danger') {
            iconClass = 'bi-exclamation-triangle-fill text-danger';
            borderColor = 'border-danger';
            toast.style.borderColor = 'var(--danger)';
        } else if (type === 'warning') {
            iconClass = 'bi-exclamation-circle-fill text-warning';
            borderColor = 'border-warning';
            toast.style.borderColor = 'var(--warning)';
        }

        toast.innerHTML = `
            <i class="bi ${iconClass} fs-5"></i>
            <div class="flex-grow-1 text-start">${message}</div>
            <button type="button" class="btn-close ms-auto" style="font-size: 0.8rem;"></button>
        `;

        toastContainer.appendChild(toast);

        // Close button click listener
        toast.querySelector('.btn-close').addEventListener('click', () => {
            toast.remove();
        });

        // Auto remove after 4.5 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 4500);
    };

    // 3. Notification Hub Reader (AJAX)
    const notificationItems = document.querySelectorAll('.notification-item-dismiss');
    notificationItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const id = this.getAttribute('data-notif-id');
            const parent = this.closest('.notification-dropdown-item') || this.closest('.list-group-item');
            
            fetch(`/notifications/read/${id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (parent) {
                        parent.style.opacity = '0.4';
                        // Remove badge indicator
                        const badge = parent.querySelector('.badge');
                        if (badge) badge.remove();
                    }
                    
                    // Update global count badge
                    const countBadges = document.querySelectorAll('.notification-count-badge');
                    countBadges.forEach(badge => {
                        let currentCount = parseInt(badge.textContent);
                        if (!isNaN(currentCount) && currentCount > 0) {
                            currentCount--;
                            badge.textContent = currentCount;
                            if (currentCount === 0) {
                                badge.style.display = 'none';
                            }
                        }
                    });
                    
                    showToast('Notification marked as read', 'success');
                }
            })
            .catch(err => console.error(err));
        });
    });

    // 4. Global search functionality simulation
    const globalSearchInput = document.getElementById('global-search');
    if (globalSearchInput) {
        globalSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = globalSearchInput.value.trim();
                if (query) {
                    // Redirect to the data management dashboard with search query
                    window.location.href = `/admin/students?search=${encodeURIComponent(query)}`;
                }
            }
        });
    }
});
