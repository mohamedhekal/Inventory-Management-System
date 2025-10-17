// Add Invoice JavaScript
document.addEventListener('DOMContentLoaded', function () {
    // تحديث معلومات المنتج عند التغيير
    const productSelect = document.getElementById('product_code');
    const quantityInput = document.getElementById('quantity');

    if (productSelect) {
        productSelect.addEventListener('change', updateProductInfo);
    }

    if (quantityInput) {
        quantityInput.addEventListener('change', calculateTotal);
    }

    // إضافة تأثيرات بصرية للنموذج
    const formInputs = document.querySelectorAll('input, select, textarea');
    formInputs.forEach(input => {
        input.addEventListener('focus', function () {
            this.style.borderColor = '#C8102E';
            this.style.boxShadow = '0 0 0 2px rgba(200, 16, 46, 0.2)';
        });

        input.addEventListener('blur', function () {
            this.style.borderColor = '';
            this.style.boxShadow = '';
        });
    });

    // إضافة تأثيرات للزر
    const submitBtn = document.querySelector('.btn-primary');
    if (submitBtn) {
        submitBtn.addEventListener('click', function (e) {
            // إظهار رسالة التحميل
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الحفظ...';
            this.disabled = true;

            // إعادة تعيين الزر بعد 3 ثواني
            setTimeout(() => {
                this.innerHTML = '<i class="fas fa-save"></i> حفظ الطلب';
                this.disabled = false;
            }, 3000);
        });
    }
});

// تحديث معلومات المنتج
function updateProductInfo() {
    const productSelect = document.getElementById('product_code');
    const selectedOption = productSelect.options[productSelect.selectedIndex];

    if (selectedOption.value) {
        // إضافة تأثير بصري للمنتج المحدد
        productSelect.style.borderColor = '#00aa00';
        productSelect.style.boxShadow = '0 0 0 2px rgba(0, 170, 0, 0.2)';

        // إظهار رسالة تأكيد
        showNotification(`تم اختيار: ${selectedOption.text}`, 'success');
    } else {
        productSelect.style.borderColor = '';
        productSelect.style.boxShadow = '';
    }
}

// حساب المجموع
function calculateTotal() {
    const productSelect = document.getElementById('product_code');
    const quantityInput = document.getElementById('quantity');

    if (productSelect.value && quantityInput.value) {
        const prices = {
            'sales_v1': 40000,
            'sales_v2': 45000,
            'spare_head': 15000,
            'charging_cable': 10000
        };

        const price = prices[productSelect.value];
        const quantity = parseInt(quantityInput.value);
        const total = price * quantity;

        // إظهار المجموع
        showNotification(`المجموع: ${total.toLocaleString()} دينار عراقي`, 'info');
    }
}

// إظهار إشعار
function showNotification(message, type = 'info') {
    // إنشاء عنصر الإشعار
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="notification-close">&times;</button>
    `;

    // إضافة الأنماط
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? 'linear-gradient(135deg, #00aa00, #44ff44)' :
            type === 'error' ? 'linear-gradient(135deg, #ff4444, #cc0000)' :
                'linear-gradient(135deg, #0088ff, #44aaff)'};
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 10px;
        animation: slideInRight 0.3s ease;
    `;

    // إضافة زر الإغلاق
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.style.cssText = `
        background: none;
        border: none;
        color: white;
        font-size: 18px;
        cursor: pointer;
        opacity: 0.8;
        margin-left: 10px;
    `;

    closeBtn.addEventListener('mouseenter', function () {
        this.style.opacity = '1';
    });

    closeBtn.addEventListener('mouseleave', function () {
        this.style.opacity = '0.8';
    });

    // إضافة إلى الصفحة
    document.body.appendChild(notification);

    // إزالة تلقائياً بعد 5 ثواني
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// إضافة أنماط CSS للإشعارات
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .notification {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 500;
    }
    
    .notification-close:hover {
        opacity: 1 !important;
    }
`;
document.head.appendChild(style);
