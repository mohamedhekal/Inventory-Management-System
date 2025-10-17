// ملف JavaScript لصفحة الموظفين

document.addEventListener('DOMContentLoaded', function() {
    console.log('تم تحميل صفحة الموظفين');
    
    // تحديث التاريخ الحالي
    updateCurrentDate();
    
    // إضافة مستمعي الأحداث
    addEventListeners();
});

function updateCurrentDate() {
    const dateInput = document.getElementById('date');
    if (dateInput && !dateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
}

function addEventListeners() {
    // فلتر التاريخ
    const dateFilter = document.getElementById('date');
    if (dateFilter) {
        dateFilter.addEventListener('change', function() {
            this.form.submit();
        });
    }
    
    // أزرار التصدير
    const exportButtons = document.querySelectorAll('.btn-success');
    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.href.includes('export')) {
                e.preventDefault();
                handleExport(this.href);
            }
        });
    });
}

function handleExport(exportUrl) {
    if (confirm('هل تريد تصدير تقرير الأداء؟')) {
        const button = event.target;
        const originalText = button.innerHTML;
        
        // إظهار حالة التحميل
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التصدير...';
        button.disabled = true;
        
        // بدء التحميل
        window.location.href = exportUrl;
        
        // إعادة تعيين الزر بعد 3 ثواني
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 3000);
    }
}

// دالة لتحديث الإحصائيات
function updateStats() {
    const statsContainer = document.querySelector('.summary-stats');
    if (statsContainer) {
        // يمكن إضافة تحديثات ديناميكية هنا
        console.log('تم تحديث الإحصائيات');
    }
}

// دالة لتحديث الجدول
function updateTable() {
    const table = document.querySelector('.data-table');
    if (table) {
        // يمكن إضافة تحديثات ديناميكية هنا
        console.log('تم تحديث الجدول');
    }
}


