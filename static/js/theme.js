// Theme Switcher
class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme() || 'dark';
        this.init();
    }

    init() {
        // Apply theme on page load
        this.applyTheme(this.currentTheme);

        // Create and add toggle button
        this.createToggleButton();
    }

    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    setStoredTheme(theme) {
        localStorage.setItem('theme', theme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        this.setStoredTheme(theme);
        this.updateToggleButton();
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
    }

    createToggleButton() {
        // Check if button already exists
        if (document.querySelector('.theme-toggle-container')) {
            return;
        }

        const container = document.createElement('div');
        container.className = 'theme-toggle-container';

        const button = document.createElement('button');
        button.className = 'theme-toggle';
        button.setAttribute('aria-label', 'Toggle theme');
        button.id = 'theme-toggle-btn';

        const icon = document.createElement('span');
        icon.className = 'theme-toggle-icon';
        icon.id = 'theme-icon';

        const text = document.createElement('span');
        text.className = 'theme-toggle-text';
        text.id = 'theme-text';

        button.appendChild(icon);
        button.appendChild(text);
        container.appendChild(button);

        document.body.appendChild(container);

        button.addEventListener('click', () => this.toggleTheme());

        this.updateToggleButton();
    }

    updateToggleButton() {
        const icon = document.getElementById('theme-icon');
        const text = document.getElementById('theme-text');

        if (icon && text) {
            if (this.currentTheme === 'dark') {
                icon.textContent = '☀️';
                text.textContent = 'Light Mode';
            } else {
                icon.textContent = '🌙';
                text.textContent = 'Dark Mode';
            }
        }
    }
}

// Initialize theme manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.themeManager = new ThemeManager();
    });
} else {
    window.themeManager = new ThemeManager();
}
