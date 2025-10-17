// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth animations to stat cards
    const statCards = document.querySelectorAll('.stat-card');
    const actionCards = document.querySelectorAll('.action-card');
    
    // Animate stat cards on load
    statCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.6s ease';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100);
        }, index * 100);
    });
    
    // Animate action cards on load
    actionCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.6s ease';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100);
        }, (index * 100) + 400);
    });
    
    // Add hover effects to menu items
    const menuItems = document.querySelectorAll('.menu-item a');
    menuItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(-8px) scale(1.02)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0) scale(1)';
        });
    });
    
    // Add click effects to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });
    
    // Real-time clock update (if needed)
    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('ar-EG');
        const clockElement = document.querySelector('.current-time');
        if (clockElement) {
            clockElement.textContent = timeString;
        }
    }
    
    // Update clock every second if clock element exists
    if (document.querySelector('.current-time')) {
        setInterval(updateClock, 1000);
        updateClock();
    }
});
