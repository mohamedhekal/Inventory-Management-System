// ملف JavaScript المبسط لصفحة المخزون

// متغيرات عامة
let categoryChart;

// تهيئة الصفحة
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    setupEventListeners();
});

// تهيئة الصفحة
function initializePage() {
    console.log('تم تهيئة صفحة المخزون');
}

// إعداد مستمعي الأحداث
function setupEventListeners() {
    // إغلاق المودال عند النقر خارجه
    const modal = document.getElementById('editModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeEditModal();
            }
        });
    }
}

// فلترة المنتجات
function filterProducts() {
    const searchValue = document.getElementById('searchInput').value.toLowerCase();
    const categoryValue = document.getElementById('categoryFilter').value;
    const stockValue = document.getElementById('stockFilter').value;
    
    const rows = document.querySelectorAll('#productsTableBody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        let showRow = true;
        
        // فلتر البحث
        if (searchValue) {
            const productName = row.cells[0].textContent.toLowerCase();
            if (!productName.includes(searchValue)) {
                showRow = false;
            }
        }
        
        // فلتر الفئة
        if (categoryValue && showRow) {
            const category = row.cells[1].textContent;
            if (category !== categoryValue) {
                showRow = false;
            }
        }
        
        // فلتر المخزون
        if (stockValue && showRow) {
            const stock = parseInt(row.cells[2].textContent);
            if (stockValue === 'متوفر' && stock <= 10) {
                showRow = false;
            } else if (stockValue === 'منخفض' && (stock === 0 || stock > 10)) {
                showRow = false;
            } else if (stockValue === 'نفذ' && stock > 0) {
                showRow = false;
            }
        }
        
        // إظهار/إخفاء الصف
        if (showRow) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    console.log(`تم عرض ${visibleCount} منتج`);
}

// فتح مودال التعديل
function openEditModal(productId, productName, stock, returns) {
    document.getElementById('editProductId').value = productId;
    document.getElementById('editProductName').value = productName;
    document.getElementById('editStock').value = stock;
    document.getElementById('editReturns').value = returns;
    
    document.getElementById('editModal').style.display = 'block';
}

// إغلاق مودال التعديل
function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

// حفظ التغييرات
function saveChanges() {
    const productId = document.getElementById('editProductId').value;
    const stock = document.getElementById('editStock').value;
    const returns = document.getElementById('editReturns').value;
    
    if (!stock || !returns) {
        alert('يرجى ملء جميع الحقول المطلوبة');
        return;
    }
    
    // إرسال البيانات إلى الخادم
    fetch(`/update_product_stock/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            stock: parseInt(stock),
            returns: parseInt(returns)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('تم تحديث المخزون بنجاح!');
            closeEditModal();
            location.reload(); // إعادة تحميل الصفحة لتحديث البيانات
        } else {
            alert('حدث خطأ أثناء تحديث المخزون: ' + data.error);
        }
    })
    .catch(error => {
        console.error('خطأ:', error);
        alert('حدث خطأ أثناء تحديث المخزون');
    });
}

// تصدير المخزون
function exportInventory() {
    const rows = document.querySelectorAll('#productsTableBody tr');
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // إضافة رأس الجدول
    csvContent += "المنتج,الفئة,المخزون,المرتجعات,السعر,الحالة\n";
    
    // إضافة بيانات المنتجات
    rows.forEach(row => {
        if (row.style.display !== 'none') {
            const productName = row.cells[0].textContent;
            const category = row.cells[1].textContent;
            const stock = row.cells[2].textContent;
            const returns = row.cells[3].textContent;
            const price = row.cells[4].textContent;
            const status = row.cells[5].textContent;
            
            csvContent += `"${productName}","${category}","${stock}","${returns}","${price}","${status}"\n`;
        }
    });
    
    // تحميل الملف
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "مخزون_نظام المبيعات.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log('تم تصدير المخزون بنجاح');
}

// تحديث المخزون
function updateStock(productId, action, quantity) {
    fetch(`/update_stock/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            action: action,
            quantity: parseInt(quantity)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('تم تحديث المخزون بنجاح!');
            location.reload();
        } else {
            alert('حدث خطأ أثناء تحديث المخزون: ' + data.error);
        }
    })
    .catch(error => {
        console.error('خطأ:', error);
        alert('حدث خطأ أثناء تحديث المخزون');
    });
}

// إضافة مرتجع
function addReturn(productId, quantity) {
    fetch(`/add_return/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            quantity: parseInt(quantity)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('تم إضافة المرتجع بنجاح!');
            location.reload();
        } else {
            alert('حدث خطأ أثناء إضافة المرتجع: ' + data.error);
        }
    })
    .catch(error => {
        console.error('خطأ:', error);
        alert('حدث خطأ أثناء إضافة المرتجع');
    });
}

// حذف منتج
function deleteProduct(productId) {
    if (confirm('هل أنت متأكد من حذف هذا المنتج؟')) {
        fetch(`/delete_product/${productId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('تم حذف المنتج بنجاح!');
                location.reload();
            } else {
                alert('حدث خطأ أثناء حذف المنتج: ' + data.error);
            }
        })
        .catch(error => {
            console.error('خطأ:', error);
            alert('حدث خطأ أثناء حذف المنتج');
        });
    }
}

// تحديث حالة المخزون
function updateStockStatus() {
    const stockCells = document.querySelectorAll('#productsTableBody tr td:nth-child(3)');
    const statusCells = document.querySelectorAll('#productsTableBody tr td:nth-child(6)');
    
    stockCells.forEach((cell, index) => {
        const stock = parseInt(cell.textContent);
        const statusCell = statusCells[index];
        
        if (stock > 10) {
            statusCell.innerHTML = '<span style="color: #28a745;">متوفر</span>';
        } else if (stock > 0) {
            statusCell.innerHTML = '<span style="color: #ffc107;">منخفض</span>';
        } else {
            statusCell.innerHTML = '<span style="color: #dc3545;">نفذ</span>';
        }
    });
}

// تهيئة الرسوم البيانية
function initializeCharts() {
    // يمكن إضافة المزيد من الرسوم البيانية هنا
    console.log('تم تهيئة الرسوم البيانية');
}

// تحديث الإحصائيات
function updateStats() {
    const rows = document.querySelectorAll('#productsTableBody tr');
    let totalStock = 0;
    let totalReturns = 0;
    let lowStockCount = 0;
    
    rows.forEach(row => {
        if (row.style.display !== 'none') {
            const stock = parseInt(row.cells[2].textContent);
            const returns = parseInt(row.cells[3].textContent);
            
            totalStock += stock;
            totalReturns += returns;
            
            if (stock <= 10 && stock > 0) {
                lowStockCount++;
            }
        }
    });
    
    console.log(`إجمالي المخزون: ${totalStock}`);
    console.log(`إجمالي المرتجعات: ${totalReturns}`);
    console.log(`المنتجات منخفضة المخزون: ${lowStockCount}`);
}

// تصدير البيانات
function exportData(format = 'csv') {
    if (format === 'csv') {
        exportInventory();
    } else if (format === 'excel') {
        // يمكن إضافة تصدير Excel هنا
        alert('سيتم إضافة تصدير Excel قريباً');
    }
}

// البحث المتقدم
function advancedSearch() {
    const searchValue = document.getElementById('searchInput').value;
    const categoryValue = document.getElementById('categoryFilter').value;
    const stockValue = document.getElementById('stockFilter').value;
    
    console.log('بحث متقدم:', { searchValue, categoryValue, stockValue });
    
    filterProducts();
}

// إعادة تعيين الفلاتر
function resetFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('categoryFilter').value = '';
    document.getElementById('stockFilter').value = '';
    
    filterProducts();
}

// تحديث تلقائي للمخزون
function autoUpdateStock() {
    // يمكن إضافة تحديث تلقائي للمخزون هنا
    console.log('تحديث تلقائي للمخزون');
}

// إعدادات متقدمة
function advancedSettings() {
    alert('سيتم إضافة الإعدادات المتقدمة قريباً');
}

// مساعدة
function showHelp() {
    alert('للمساعدة، يرجى التواصل مع فريق الدعم الفني');
}

// معلومات النظام
function systemInfo() {
    console.log('نظام إدارة المخزون - نظام المبيعات');
    console.log('الإصدار: 1.0.0');
    console.log('آخر تحديث:', new Date().toLocaleDateString('ar-SA'));
}
