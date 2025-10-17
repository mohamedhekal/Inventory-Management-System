# Sales Management System 🚀

<div align="center">
  <h2>نظام إدارة المبيعات والطلبات</h2>
  <p>A comprehensive sales and order management system built with modern web technologies</p>
</div>

---

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 🌟 Overview

### English
The Sales Management System is a comprehensive solution for managing sales operations, orders, and business processes. Built with modern web technologies, it's designed to efficiently manage products, orders, customers, and employees with a focus on user experience and performance.

### العربية
نظام إدارة المبيعات والطلبات هو نظام متكامل لإدارة عمليات البيع والطلبات التجارية. النظام مبني بتقنيات الويب الحديثة ومصمم لإدارة المنتجات والطلبات والعملاء والموظفين بكفاءة عالية.

---

## 🎯 Features

### 🔐 Authentication System
**English:**
- Professional and modern login interface
- Secure authentication system
- Responsive design for all devices
- Advanced user permission management

**العربية:**
- واجهة تسجيل دخول احترافية وعصرية
- نظام مصادقة آمن
- تصميم متجاوب مع جميع الأجهزة
- إدارة صلاحيات المستخدمين المتقدمة

### 📊 Dashboard
**English:**
- Real-time daily statistics
- Invoice and sales count display
- Employee and product statistics
- Quick actions for essential functions
- Live data updates

**العربية:**
- إحصائيات فورية لليوم
- عرض عدد الفواتير والمبيعات
- إحصائيات الموظفين والمنتجات
- إجراءات سريعة للوظائف الأساسية
- تحديث البيانات في الوقت الفعلي

### 🛒 Order & Invoice Management
**English:**
- Add new product orders
- View all orders with date filtering
- Automatic order numbering system
- Order status tracking (New, Processing, Shipped, Delivered, Cancelled)
- Payment status management (Pending, Paid, Refunded)
- Automatic shipping cost calculation
- Address and region management

**العربية:**
- إضافة طلبات جديدة للمنتجات
- عرض جميع الطلبات مع فلترة حسب التاريخ
- نظام ترقيم تلقائي للطلبات
- تتبع حالة الطلب (جديد، معالج، مرسل، مسلم، ملغي)
- إدارة حالة الدفع (معلق، مدفوع، مرتجع)
- حساب رسوم التوصيل التلقائي
- إدارة العناوين والمناطق

### 👥 Employee Management
**English:**
- Add and modify employee data
- Calculate salaries and commissions
- Track employee performance
- Manage departments and positions
- Employee performance reports

**العربية:**
- إضافة وتعديل بيانات الموظفين
- حساب الرواتب والعمولات
- تتبع أداء الموظفين
- إدارة الأقسام والمناصب
- تقارير أداء الموظفين

### 📦 Product Management
**English:**
- Inventory and cost management
- Product categorization (Machines, Accessories, etc.)
- Price and warranty tracking
- Detailed information (Weight, Dimensions, Description)
- Product category management

**العربية:**
- إدارة المخزون والتكلفة
- تصنيف المنتجات (ماكينات، ملحقات، إلخ)
- تتبع الأسعار والضمان
- معلومات تفصيلية (الوزن، الأبعاد، الوصف)
- إدارة فئات المنتجات

### 👤 Customer Management
**English:**
- Comprehensive customer database
- Contact information and addresses
- Transaction history tracking
- Customer data management

**العربية:**
- قاعدة بيانات شاملة للعملاء
- معلومات الاتصال والعناوين
- تتبع تاريخ التعامل
- إدارة بيانات العملاء

### 📈 Reports & Export
**English:**
- Export shipping files for logistics companies
- Human resources reports for employees
- Detailed statistics
- Excel format export
- Daily and monthly sales reports

**العربية:**
- تصدير ملفات الشحن لشركات النقل
- تقارير الموارد البشرية للموظفين
- إحصائيات مفصلة
- تصدير بتنسيق Excel
- تقارير مبيعات يومية وشهرية

### 🤖 Telegram Bot Integration
**English:**
- Receive orders via Telegram
- Automatic invoice processing
- Quick commands (/add, /stats, /exporttoday)
- Support for single messages with all data
- Remote order management

**العربية:**
- استقبال الطلبات عبر التلجرام
- معالجة تلقائية للفواتير
- أوامر سريعة (/add, /stats, /exporttoday)
- دعم الرسائل المفردة مع جميع البيانات
- إدارة الطلبات عن بُعد

---

## 🛠️ Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: Session and authentication management
- **SQLite**: Local database

### Frontend
- **HTML5**: Page structure
- **CSS3**: Design and animations
- **JavaScript**: Interactivity and functions
- **Font Awesome**: Icons

### Additional Libraries
- **pandas**: Data processing and export
- **openpyxl**: Excel file export
- **python-telegram-bot**: Telegram bot integration
- **APScheduler**: Task scheduling

---

## 🎨 Design & Interface

### Color Scheme
- **Background**: Black (#0a0a0a)
- **Elements**: Red (#ff0000)
- **Text**: White (#ffffff)
- **Gradients**: Red to light red

### Design Features
- Modern and sophisticated design
- Smooth and advanced animations
- Intuitive user interface
- Full responsiveness for all devices
- Advanced visual effects

---

## 🚀 Installation

### Requirements
```bash
Python 3.8+
pip
```

### Installation Steps
1. **Install Dependencies**
```bash
pip install -r requirements_web.txt
```

2. **Run Application**
```bash
python app.py
```

3. **Open Browser**
```
http://localhost:5000
```

### Default Login Credentials
- **Username**: admin
- **Password**: admin123

---

## 📱 Telegram Bot Usage

### Available Commands
- `/start` - Start the bot
- `/add` - Add a new invoice
- `/stats` - View today's statistics
- `/exporttoday` - Export today's files

### Invoice Format
```
Employee Name/Ahmed
Customer Name/Mohammed Ali
Governorate/Baghdad
Nearest Landmark/Rashid Street
Phone/07801234567
Quantity/2
Price/50000
Notes/Fast delivery
```

---

## 📁 Project Structure

```
sales_system/
├── app.py                 # Main application
├── requirements_web.txt   # Python requirements
├── templates/            # HTML templates
│   ├── login.html       # Login page
│   ├── dashboard.html   # Dashboard
│   ├── invoices.html    # Invoices page
│   ├── employees.html   # Employees page
│   ├── products.html    # Products page
│   ├── customers.html   # Customers page
│   └── reports.html     # Reports page
├── static/              # Static files
│   ├── css/
│   │   └── style.css    # Style file
│   └── js/              # JavaScript files
├── company_template/     # Company templates
├── company_logo/        # Company logo
└── exports/             # Export files
```

---

## ✨ Advanced Features

### Real-time Updates
- Instant statistics updates
- Real-time display
- Automatic data updates

### Responsiveness
- Responsive design for all devices
- Mobile and tablet support
- Mobile-optimized interface

### Performance
- Fast page loading
- Efficient data processing
- Optimized caching

### Security
- Secure user authentication
- Protection against common attacks
- Password encryption
- Advanced permission management

---

## 🔧 Troubleshooting

### Common Issues
1. **Application not working**: Ensure all requirements are installed
2. **Database error**: Check write permissions
3. **Bot not responding**: Verify Telegram token

### Quick Solutions
- Restart the application
- Check used ports
- Review error logs

---

## 📊 System Statistics

### Supported Data
- Product and order management
- Sales and revenue tracking
- Employee and salary management
- Customer database
- Reports and statistics

### Supported Exports
- Excel files (.xlsx)
- Shipping reports
- Human resources reports
- Sales statistics

---

## 🎯 Suitable Use Cases

- Retail stores
- Sales companies
- Product management
- Customer management systems
- Sales reporting

---

## 🤝 Contributing

We welcome contributions! Please feel free to submit pull requests or open issues for bugs and feature requests.

---

<div align="center">
  <h3>Sales Management System</h3>
  <p><em>A comprehensive solution for business management 🚀</em></p>
  <p><em>تم تطوير هذا النظام بأحدث التقنيات وأفضل الممارسات</em></p>
</div>
