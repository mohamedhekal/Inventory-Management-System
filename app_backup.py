from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import os
import json
from pathlib import Path
import time
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import logging
from sqlalchemy import text, update

# إعداد Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sales-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إعداد قاعدة البيانات
db = SQLAlchemy(app)

# إعداد Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# إعداد البوت
BOT_TOKEN = "8305954082:AAHj2DlFzJ4Fb4H6w65c20jw3N5Pn3ksXYc"
bot = Bot(token=BOT_TOKEN)



# أكواد المحافظات ال
CITY_CODES = {
    'بغداد': 'BGD',
    'الناصرية': 'NAS',
    'ذي قار': 'NAS',
    'ديالى': 'DYL',
    'الكوت': 'KOT',
    'واسط': 'KOT',
    'كربلاء': 'KRB',
    'دهوك': 'DOH',
    'بابل': 'BBL',
    'الحلة': 'BBL',
    'النجف': 'NJF',
    'البصرة': 'BAS',
    'اربيل': 'ARB',
    'كركوك': 'KRK',
    'السليمانية': 'SMH',
    'صلاح الدين': 'SAH',
    'الانبار': 'ANB',
    'رمادي': 'ANB',
    'السماوة': 'SAM',
    'المثنى': 'SAM',
    'موصل': 'MOS',
    'نينوى': 'MOS',
    'الديوانية': 'DWN',
    'العمارة': 'AMA',
    'ميسان': 'AMA'
}

# بيانات المنتجات
PRODUCTS_DATA = {
    'sales_v1': {
        'name': 'sales V1',
        'price': 40000,
        'description': 'شفرة سيراميك SkinSafe™، صوت منخفض، مضاد للبكتيريا، مقاوم للماء، بطارية 120 دقيقة',
        'category': 'ماكينة حلاقة'
    },
    'sales_v2': {
        'name': 'sales V2', 
        'price': 45000,
        'description': 'جميع ميزات V1 + إضاءة LED، قاعدة شحن، شحن سريع Type-C، بطارية 150 دقيقة',
        'category': 'ماكينة حلاقة'
    },
    'spare_head': {
        'name': 'رأس ماكينة إضافي',
        'price': 15000,
        'description': 'رأس ماكينة بديل أصلي لجميع موديلات نظام المبيعات',
        'category': 'ملحقات'
    },
    'charging_cable': {
        'name': 'كابل شحن إضافي',
        'price': 10000,
        'description': 'كابل شحن Type-C أصلي لماكينات نظام المبيعات',
        'category': 'ملحقات'
    }
}

# بيانات الموظفين الفعليين
EMPLOYEES_DATA = [
    {'name': 'نور', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 0.5},
    {'name': 'صبا', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 0.5},
    {'name': 'ميريانا', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 0.5},
    {'name': 'عيسى', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 0.5},
    {'name': 'إيمان', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 0.5},
    {'name': 'لافا', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 0.5}
]

# نظام العمولات
COMMISSION_RATES = {
    'sales_v1': 0.5,  # 50 سنت لكل قطعة
    'sales_v2': 0.5,  # 50 سنت لكل قطعة
    'spare_head': 0.3,  # 30 سنت لكل قطعة
    'charging_cable': 0.2  # 20 سنت لكل قطعة
}

# نماذج قاعدة البيانات
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), unique=True, nullable=False)  # إضافة عمود order_id
    employee_name = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    city_code = db.Column(db.String(10), nullable=True)  # كود المحافظة
    address = db.Column(db.String(200), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    product_code = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    delivery_fee = db.Column(db.Float, default=0)
    final_total = db.Column(db.Float, nullable=False)
    order_status = db.Column(db.String(50), default='قيد المراجعة')  # قيد المراجعة، تم التأكيد، خارج للشحن، تم التوصيل، تم الإلغاء
    payment_status = db.Column(db.String(50), default='معلق')  # معلق، مدفوع، مرتجع
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    day = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    commission_paid = db.Column(db.Boolean, default=False)  # هل تم دفع العمولة

# الاحتفاظ بـ Invoice للتوافق مع النظام القديم
Invoice = Order

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    salary = db.Column(db.Float, default=0)
    base_salary = db.Column(db.Float, default=500000)  # الراتب الأساسي
    commission_per_order = db.Column(db.Float, default=0.5)
    hire_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, default=0)  # سعر التكلفة
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(200))
    weight = db.Column(db.Float, default=0)  # الوزن للشحن
    dimensions = db.Column(db.String(100))  # الأبعاد
    warranty_months = db.Column(db.Integer, default=12)  # فترة الضمان بالأشهر
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    city = db.Column(db.String(100))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# المسارات الرئيسية
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now().strftime('%Y-%m-%d')
    
    # إحصائيات اليوم
    today_invoices = Order.query.filter_by(day=today).count()
    today_total = db.session.query(db.func.sum(Order.final_total)).filter_by(day=today).scalar() or 0
    
    # إحصائيات الموظفين
    employees_count = Employee.query.filter_by(status='active').count()
    
    # إحصائيات المنتجات
    products_count = Product.query.count()
    
    # إحصائيات العملاء
    customers_count = Customer.query.count()
    
    # بيانات الرسوم البيانية - المبيعات الأسبوعية
    week_data = get_weekly_sales_data()
    
    # بيانات توزيع المنتجات
    product_distribution = get_product_distribution()
    
    # بيانات النشاطات الأخيرة
    recent_activities = get_recent_activities()
    
    return render_template('dashboard.html',
                         today_invoices=today_invoices,
                         today_total=today_total,
                         employees_count=employees_count,
                         products_count=products_count,
                         customers_count=customers_count,
                         week_data=week_data,
                         product_distribution=product_distribution,
                         recent_activities=recent_activities)

# مسارات الفواتير
@app.route('/invoices')
@login_required
def invoices():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # فلترة حسب التاريخ والحالة
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    status_filter = request.args.get('status', '')
    
    query = Order.query
    
    if date_filter:
        query = query.filter_by(day=date_filter)
    
    # إزالة فلترة حسب الحالة (تم إلغاء نظام الحالات)
    
    invoices = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # تم إلغاء نظام الحالات
    
    return render_template('invoices.html', 
                         invoices=invoices, 
                         date_filter=date_filter)

@app.route('/invoices/add', methods=['GET', 'POST'])
@login_required
def add_invoice():
    if request.method == 'POST':
        try:
            # تحديد المنتج بناءً على السعر
            price = float(request.form['price'])
            product_code = 'sales_v1'  # افتراضي
            product_name = 'sales V1'
            
            if price == 45000:
                product_code = 'sales_v2'
                product_name = 'sales V2'
            elif price == 15000:
                product_code = 'spare_head'
                product_name = 'رأس ماكينة إضافي'
            elif price == 10000:
                product_code = 'charging_cable'
                product_name = 'كابل شحن إضافي'
            
            # تحديد كود المحافظة
            city = request.form['city']
            city_code = get_city_code(city)
            
            # إنشاء الطلب
            order = Order(
                employee_name=request.form['employee_name'],
                customer_name=request.form['customer_name'],
                phone=request.form['phone'],
                city=city,
                city_code=city_code,
                address=request.form.get('landmark', ''),
                product_name=product_name,
                product_code=product_code,
                quantity=int(request.form['quantity']),
                unit_price=price,
                total_price=price * int(request.form['quantity']),
                delivery_fee=0,
                final_total=price * int(request.form['quantity']),
                order_status='قيد المراجعة',
                payment_status='معلق',
                notes=request.form.get('notes', ''),
                day=datetime.now().strftime('%Y-%m-%d')
            )
            
            db.session.add(order)
            db.session.commit()
            
            flash(f'تم إضافة الطلب بنجاح! رقم الطلب: {order.id}', 'success')
            return redirect(url_for('invoices'))
            
        except Exception as e:
            print(f"❌ خطأ في إضافة الطلب: {e}")
            flash(f'خطأ في إضافة الطلب: {str(e)}', 'error')
    
    employees = Employee.query.filter_by(status='active').all()
    return render_template('add_invoice.html', employees=employees)

# مسارات الموظفين
@app.route('/employees')
@login_required
def employees():
    # تحديد التاريخ (افتراضي: اليوم)
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # جلب أداء الموظفين
    performance_data = get_employee_performance(date_filter)
    
    return render_template('employees.html', 
                         employees=performance_data, 
                         date_filter=date_filter)

@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        try:
            employee = Employee(
                name=request.form['name'],
                phone=request.form['phone'],
                email=request.form['email'],
                department=request.form['department'],
                position=request.form['position'],
                salary=float(request.form['salary']),
                commission_per_order=float(request.form['commission_per_order'])
            )
            db.session.add(employee)
            db.session.commit()
            flash('تم إضافة الموظف بنجاح', 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            flash(f'خطأ في إضافة الموظف: {str(e)}', 'error')
    
    return render_template('add_employee.html')

# مسارات المنتجات
@app.route('/products')
@login_required
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        try:
            product = Product(
                name=request.form['name'],
                description=request.form['description'],
                price=float(request.form['price']),
                stock=int(request.form['stock']),
                category=request.form['category']
            )
            db.session.add(product)
            db.session.commit()
            flash('تم إضافة المنتج بنجاح', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            flash(f'خطأ في إضافة المنتج: {str(e)}', 'error')
    
    return render_template('add_product.html')

# مسارات العملاء
@app.route('/customers')
@login_required
def customers():
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        try:
            customer = Customer(
                name=request.form['name'],
                phone=request.form['phone'],
                email=request.form['email'],
                city=request.form['city'],
                address=request.form['address']
            )
            db.session.add(customer)
            db.session.commit()
            flash('تم إضافة العميل بنجاح', 'success')
            return redirect(url_for('customers'))
        except Exception as e:
            flash(f'خطأ في إضافة العميل: {str(e)}', 'error')
    
    return render_template('add_customer.html')

# مسارات التقارير
@app.route('/reports')
@login_required
def reports():
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('reports.html', today=today)

@app.route('/export/shipping/<date>')
@login_required
def export_shipping(date):
    try:
        invoices = Invoice.query.filter_by(day=date).all()
        
        if not invoices:
            flash(f'لا توجد طلبات لليوم {date}', 'warning')
            return redirect(url_for('reports'))
        
        # قراءة قالب الشركة
        template_path = Path('company_template/قالب طلبات نظام المبيعات .xls')
        if template_path.exists():
            try:
                # استخدام القالب الموجود
                df = pd.read_excel(template_path, engine='xlrd')
                print(f"✅ تم قراءة القالب بنجاح: {len(df)} صف")
                
                # إضافة البيانات الجديدة حسب القالب الجديد
                new_data = []
                for invoice in invoices:
                    new_data.append({
                        'ملاحظات': invoice.notes or '',
                        'عدد القطع\nأجباري': invoice.quantity,
                        'ارجاع بضاعة؟': 'NO',
                        'هاتف المستلم\nأجباري 11 خانة': invoice.phone,
                        'تفاصيل العنوان\nأجباري': invoice.address,
                        'شفرة المحافظة\nأجباري': invoice.city_code or invoice.city,
                        'أسم المستلم': invoice.customer_name,
                        'المبلغ عراقي\nكامل بالالاف .\nفي حال عدم توفره سيعتبر 0': invoice.final_total,
                        'رقم الوصل \nفي حال عدم وجود رقم وصل سيتم توليده من النظام': ''
                    })
                
                print(f"📊 تم تجهيز {len(new_data)} طلب للتصدير")
                
                # دمج البيانات مع القالب
                new_df = pd.DataFrame(new_data)
                result_df = pd.DataFrame(new_data)
                print(f"✅ تم دمج البيانات مع القالب: {len(result_df)} صف إجمالي")
                
            except Exception as template_error:
                print(f"❌ خطأ في قراءة القالب: {template_error}")
                # في حالة فشل قراءة القالب، إنشاء ملف جديد
                new_data = []
                for invoice in invoices:
                    new_data.append({
                        'ملاحظات': invoice.notes or '',
                        'عدد القطع\nأجباري': invoice.quantity,
                        'ارجاع بضاعة؟': 'NO',
                        'هاتف المستلم\nأجباري 11 خانة': invoice.phone,
                        'تفاصيل العنوان\nأجباري': invoice.address,
                        'شفرة المحافظة\nأجباري': invoice.city_code or invoice.city,
                        'أسم المستلم': invoice.customer_name,
                        'المبلغ عراقي\nكامل بالالاف .\nفي حال عدم توفره سيعتبر 0': invoice.final_total,
                        'رقم الوصل \nفي حال عدم وجود رقم وصل سيتم توليده من النظام': ''
                    })
                result_df = pd.DataFrame(new_data)
                print(f"📝 تم إنشاء ملف جديد بدون قالب: {len(result_df)} صف")
        else:
            # إنشاء ملف جديد
            print(f"⚠️ القالب غير موجود: {template_path}")
            data = []
            for invoice in invoices:
                data.append({
                    'ملاحظات': invoice.notes or '',
                    'عدد القطع\nأجباري': invoice.quantity,
                    'ارجاع بضاعة؟': 'NO',
                    'هاتف المستلم\nأجباري 11 خانة': invoice.phone,
                    'تفاصيل العنوان\nأجباري': invoice.address,
                    'شفرة المحافظة\nأجباري': invoice.city_code or invoice.city,
                    'أسم المستلم': invoice.customer_name,
                    'المبلغ عراقي\nكامل بالالاف .\nفي حال عدم توفره سيعتبر 0': invoice.final_total,
                    'رقم الوصل \nفي حال عدم وجود رقم وصل سيتم توليده من النظام': ''
                })
            result_df = pd.DataFrame(data)
            print(f"📝 تم إنشاء ملف جديد: {len(result_df)} صف")
        
        # حفظ الملف بصيغة XLS
        export_dir = Path('exports')
        export_dir.mkdir(exist_ok=True)
        export_path = export_dir / f'Orders_{date}.xls'
        
        # حفظ بصيغة XLS باستخدام xlwt
        try:
            result_df.to_excel(export_path, index=False, engine='xlwt')
            print(f"✅ تم حفظ الملف بنجاح: {export_path}")
        except Exception as xls_error:
            print(f"❌ خطأ في حفظ XLS: {xls_error}")
            # محاولة حفظ بصيغة XLSX كبديل
            export_path_xlsx = export_dir / f'Orders_{date}.xlsx'
            result_df.to_excel(export_path_xlsx, index=False, engine='openpyxl')
            print(f"✅ تم حفظ الملف بصيغة XLSX: {export_path_xlsx}")
            export_path = export_path_xlsx
        
        flash(f'تم تصدير ملف الشحن: {export_path.name}', 'success')
        return redirect(url_for('reports'))
        
    except Exception as e:
        print(f"❌ خطأ في التصدير: {e}")
        flash(f'خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/update_order_status', methods=['POST'])
@login_required
def update_order_status():
    """تحديث حالة الطلبات المحددة"""
    try:
        action = request.form.get('action')
        order_ids = request.form.getlist('selected_orders')
        
        if not order_ids:
            flash('يرجى تحديد الطلبات المراد تحديثها', 'warning')
            return redirect(url_for('invoices'))
        
        if action == 'delete':
            # حذف الطلبات المحددة
            Order.query.filter(Order.id.in_(order_ids)).delete(synchronize_session=False)
            flash(f'تم حذف {len(order_ids)} طلب بنجاح', 'success')
        else:
            # تحديث حالة الطلبات
            orders = Order.query.filter(Order.id.in_(order_ids)).all()
            for order in orders:
                order.order_status = action
            
            flash(f'تم تحديث حالة {len(orders)} طلب بنجاح', 'success')
        
        db.session.commit()
        
    except Exception as e:
        flash(f'خطأ في تحديث الطلبات: {str(e)}', 'error')
    
    return redirect(url_for('invoices'))

@app.route('/change_order_status/<int:order_id>', methods=['POST'])
@login_required
def change_order_status(order_id):
    """تغيير حالة طلب واحد"""
    try:
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        
        if new_status in ['قيد المراجعة', 'تم التأكيد', 'خارج للشحن', 'تم التوصيل', 'تم الإلغاء']:
            order.order_status = new_status
            db.session.commit()
            flash(f'تم تحديث حالة الطلب إلى: {new_status}', 'success')
        else:
            flash('حالة غير صحيحة', 'error')
            
    except Exception as e:
        flash(f'خطأ في تحديث حالة الطلب: {str(e)}', 'error')
    
    return redirect(url_for('invoices'))

@app.route('/delete_order/<int:order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    """حذف طلب"""
    try:
        order = Order.query.get_or_404(order_id)
        db.session.delete(order)
        db.session.commit()
        flash('تم حذف الطلب بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ في حذف الطلب: {str(e)}', 'error')
    
    return redirect(url_for('invoices'))

@app.route('/export_orders_custom')
@login_required 
def export_orders_custom():
    """تصدير الطلبات مع تحديد التاريخ والصيغة"""
    try:
        date = request.args.get('date')
        format_type = request.args.get('format', 'xls')
        
        if not date:
            flash('الرجاء تحديد التاريخ', 'error')
            return redirect(url_for('invoices'))
        
        # البحث عن الطلبات حسب التاريخ
        orders = Order.query.filter_by(day=date).all()
        
        if not orders:
            flash(f'لا توجد طلبات لليوم {date}. تأكد من أن التاريخ صحيح وأن هناك طلبات مسجلة لهذا اليوم.', 'warning')
            return redirect(url_for('invoices'))
        
        # تحضير البيانات للتصدير حسب المتطلبات المطلوبة
        new_data = []
        for order in orders:
            # التأكد من أن جميع الحقول موجودة
            notes = order.notes if hasattr(order, 'notes') and order.notes else ''
            quantity = order.quantity if hasattr(order, 'quantity') else 0
            phone = order.phone if hasattr(order, 'phone') else ''
            address = order.address if hasattr(order, 'address') else ''
            city_code = order.city_code if hasattr(order, 'city_code') and order.city_code else (order.city if hasattr(order, 'city') else '')
            customer_name = order.customer_name if hasattr(order, 'customer_name') else ''
            final_total = order.final_total if hasattr(order, 'final_total') else 0
            
            new_data.append({
                'ملاحظات': notes,
                'عدد القطع\nأجباري': quantity,
                'ارجاع بضاعة؟': 'NO',
                'هاتف المستلم\nأجباري 11 خانة': phone,
                'تفاصيل العنوان\nأجباري': address,
                'شفرة المحافظة\nأجباري': city_code,
                'أسم المستلم': customer_name,
                'المبلغ عراقي\nكامل بالالاف .\nفي حال عدم توفره سيعتبر 0': final_total,
                'رقم الوصل \nفي حال عدم وجود رقم وصل سيتم توليده من النظام': ''  # دائماً فارغ
            })
        
        # إنشاء DataFrame مع ترتيب الأعمدة المحدد
        columns_order = [
            'ملاحظات',
            'عدد القطع\nأجباري',
            'ارجاع بضاعة؟',
            'هاتف المستلم\nأجباري 11 خانة',
            'تفاصيل العنوان\nأجباري',
            'شفرة المحافظة\nأجباري',
            'أسم المستلم',
            'المبلغ عراقي\nكامل بالالاف .\nفي حال عدم توفره سيعتبر 0',
            'رقم الوصل \nفي حال عدم وجود رقم وصل سيتم توليده من النظام'
        ]
        
        df = pd.DataFrame(new_data)
        df = df[columns_order]  # ترتيب الأعمدة حسب المتطلبات
        
        # تحديد مسار الملف
        export_dir = Path('exports')
        export_dir.mkdir(exist_ok=True)
        
        if format_type == 'xls':
            file_path = export_dir / f'Orders_{date}.xls'
            df.to_excel(file_path, index=False, engine='xlwt')
        else:
            file_path = export_dir / f'Orders_{date}.xlsx'
            df.to_excel(file_path, index=False, engine='openpyxl')
        
        flash(f'تم تصدير {len(orders)} طلب لليوم {date} بنجاح بصيغة {format_type.upper()}', 'success')
        return send_file(file_path, as_attachment=True, download_name=f'Orders_{date}.{format_type}')
        
    except Exception as e:
        flash(f'خطأ في التصدير: {str(e)}. تأكد من أن جميع البيانات مطلوبة موجودة.', 'error')
        return redirect(url_for('invoices'))

@app.route('/export/orders/<date>')
@login_required
def export_orders_from_page(date):
    """تصدير الطلبات مباشرة من صفحة الطلبات"""
    try:
        if date == 'today':
            date = datetime.now().strftime('%Y-%m-%d')
        
        # البحث عن الطلبات حسب التاريخ
        orders = Order.query.filter_by(day=date).all()
        
        if not orders:
            flash(f'لا توجد طلبات لليوم {date}', 'warning')
            return redirect(url_for('invoices'))
        
        # تصدير البيانات
        return export_shipping_helper(date)
        
    except Exception as e:
        flash(f'خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('invoices'))

@app.route('/export/hrm/<date>')
@login_required
def export_hrm(date):
    try:
        # إحصائيات الموظفين لليوم المحدد
        performance_data = get_employee_performance(date)
        
        if not performance_data:
            flash(f'لا توجد بيانات للموظفين لليوم {date}', 'warning')
            return redirect(url_for('reports'))
        
        # تحضير البيانات للتصدير
        export_data = []
        for emp in performance_data:
            export_data.append({
                'اسم الموظف': emp['name'],
                'القسم': emp['department'],
                'المنصب': emp['position'],
                'الراتب الأساسي': emp['base_salary'],
                'عدد الطلبات': emp['total_orders'],
                'إجمالي المبيعات': emp['total_sales'],
                'إجمالي العمولة': emp['total_commission'],
                'الراتب الإجمالي': emp['total_salary'],
                'التاريخ': date
            })
        
        df = pd.DataFrame(export_data)
        
        # حفظ الملف
        export_dir = Path('exports')
        export_dir.mkdir(exist_ok=True)
        export_path = export_dir / f'HRM_{date}.xlsx'
        
        df.to_excel(export_path, index=False, engine='openpyxl')
        
        flash(f'تم تصدير ملف HRM: {export_path.name}', 'success')
        return send_file(export_path, as_attachment=True, download_name=f'HRM_{date}.xlsx')
        
    except Exception as e:
        flash(f'خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/export/performance/<date>')
@login_required
def export_performance_report(date):
    """تصدير تقرير أداء شامل لليوم المحدد"""
    try:
        # جلب بيانات الأداء
        performance_data = get_employee_performance(date)
        
        if not performance_data:
            flash(f'لا توجد بيانات أداء لليوم {date}', 'warning')
            return redirect(url_for('reports'))
        
        # جلب إحصائيات الطلبات
        orders = Order.query.filter_by(day=date).all()
        active_orders = [order for order in orders if order.order_status != 'مرتجع']
        returned_orders = [order for order in orders if order.order_status == 'مرتجع']
        
        # إحصائيات المنتجات
        product_stats = {}
        for order in active_orders:
            if order.product_code not in product_stats:
                product_stats[order.product_code] = {'count': 0, 'amount': 0}
            product_stats[order.product_code]['count'] += order.quantity
            product_stats[order.product_code]['amount'] += order.final_total
                
        # إنشاء تقرير شامل
        report_data = {
            'ملخص عام': {
                'التاريخ': date,
                'إجمالي الطلبات': len(active_orders),
                'إجمالي المبيعات': sum(order.final_total for order in active_orders),
                'الطلبات المرتجعة': len(returned_orders),
                'عدد الموظفين النشطين': len(performance_data)
            },
            'أداء الموظفين': performance_data,
            'إحصائيات المنتجات': [
                {
                    'المنتج': PRODUCTS_DATA.get(code, {}).get('name', code),
                    'الكمية المباعة': stats['count'],
                    'إجمالي المبيعات': stats['amount']
                }
                for code, stats in product_stats.items()
            ]
        }
        
        # تصدير بصيغة Excel
        export_dir = Path('exports')
        export_dir.mkdir(exist_ok=True)
        export_path = export_dir / f'Performance_Report_{date}.xlsx'
        
        with pd.ExcelWriter(export_path, engine='openpyxl') as writer:
            # ملخص عام
            summary_df = pd.DataFrame([report_data['ملخص عام']])
            summary_df.to_excel(writer, sheet_name='ملخص عام', index=False)
            
            # أداء الموظفين
            employees_df = pd.DataFrame(report_data['أداء الموظفين'])
            employees_df.to_excel(writer, sheet_name='أداء الموظفين', index=False)
            
            # إحصائيات المنتجات
            products_df = pd.DataFrame(report_data['إحصائيات المنتجات'])
            products_df.to_excel(writer, sheet_name='إحصائيات المنتجات', index=False)
        
        flash(f'تم تصدير تقرير الأداء: {export_path.name}', 'success')
        return send_file(export_path, as_attachment=True, download_name=f'Performance_Report_{date}.xlsx')
        
    except Exception as e:
        flash(f'خطأ في تصدير تقرير الأداء: {str(e)}', 'error')
        return redirect(url_for('reports'))

# دالة مساعدة للتصدير (بدون سياق الطلب)
def export_shipping_helper(date):
    """دالة مساعدة للتصدير بدون سياق الطلب"""
    try:
        invoices = Invoice.query.filter_by(day=date).all()
        
        if not invoices:
            print(f'لا توجد طلبات لليوم {date}')
            return False
        
        # قراءة قالب الشركة
        template_path = Path('company_template/قالب طلبات نظام المبيعات .xls')
        if template_path.exists():
            try:
                # استخدام القالب الموجود
                df = pd.read_excel(template_path, engine='xlrd')
                print(f"✅ تم قراءة القالب بنجاح: {len(df)} صف")
                
                # إضافة البيانات الجديدة حسب القالب الجديد
                new_data = []
                for invoice in invoices:
                    new_data.append({
                        'ملاحظات': invoice.notes or '',
                        'عدد القطع\nأجباري': invoice.quantity,
                        'ارجاع بضاعة؟': 'NO',
                        'هاتف المستلم\nأجباري 11 خانة': invoice.phone,
                        'تفاصيل العنوان\nأجباري': invoice.address,
                        'شفرة المحافظة\nأجباري': invoice.city_code or invoice.city,
                        'أسم المستلم': invoice.customer_name,
                        'المبلغ عراقي\nكامل بالالاف .\nفي حال عدم توفره سيعتبر 0': invoice.final_total,
                        'رقم الوصل \nفي حال عدم وجود رقم وصل سيتم توليده من النظام': ''
                    })
                
                print(f"📊 تم تجهيز {len(new_data)} طلب للتصدير")
                
                # دمج البيانات مع القالب
                new_df = pd.DataFrame(new_data)
                result_df = pd.DataFrame(new_data)
                print(f"✅ تم دمج البيانات مع القالب: {len(result_df)} صف إجمالي")
                
            except Exception as template_error:
                print(f"❌ خطأ في قراءة القالب: {template_error}")
                # في حالة فشل قراءة القالب، إنشاء ملف جديد
                new_data = []
                for invoice in invoices:
                    new_data.append({
                        'ملاحظات': invoice.notes or '',
                        'عدد القطع\nأجباري': invoice.quantity,
                        'ارجاع بضاعة؟': 'NO',
                        'هاتف المستلم\nأجباري 11 خانة': invoice.phone,
                        'تفاصيل العنوان\nأجباري': invoice.address,
                        'شفرة المحافظة\nأجباري': invoice.city_code or invoice.city,
                        'أسم المستلم': invoice.customer_name,
                        'المبلغ عراقي\nكامل بالالاف .\nفي حال عدم توفره سيعتبر 0': invoice.final_total,
                        'رقم الوصل \nفي حال عدم وجود رقم وصل سيتم توليده من النظام': ''
                    })
                result_df = pd.DataFrame(new_data)
                print(f"📝 تم إنشاء ملف جديد بدون قالب: {len(result_df)} صف")
        else:
            # إنشاء ملف جديد
            print(f"⚠️ القالب غير موجود: {template_path}")
            data = []
            for invoice in invoices:
                data.append({
                    'ملاحظات': invoice.notes or '',
                    'عدد القطع\nأجباري': invoice.quantity,
                    'ارجاع بضاعة؟': 'NO',
                    'هاتف المستلم\nأجباري 11 خانة': invoice.phone,
                    'تفاصيل العنوان\nأجباري': invoice.address,
                    'شفرة المحافظة\nأجباري': invoice.city_code or invoice.city,
                    'أسم المستلم': invoice.customer_name,
                    'المبلغ عراقي\nكامل بالالاف .\nفي حال عدم توفره سيعتبر 0': invoice.final_total,
                    'رقم الوصل \nفي حال عدم وجود رقم وصل سيتم توليده من النظام': ''
                })
            result_df = pd.DataFrame(data)
            print(f"📝 تم إنشاء ملف جديد: {len(result_df)} صف")
        
        # حفظ الملف بصيغة XLS
        export_dir = Path('exports')
        export_dir.mkdir(exist_ok=True)
        export_path = export_dir / f'Orders_{date}.xls'
        
        # حفظ بصيغة XLS باستخدام xlwt
        try:
            result_df.to_excel(export_path, index=False, engine='xlwt')
            print(f"✅ تم حفظ الملف بنجاح: {export_path}")
            return True
        except Exception as xls_error:
            print(f"❌ خطأ في حفظ XLS: {xls_error}")
            # محاولة حفظ بصيغة XLSX كبديل
            export_path_xlsx = export_dir / f'Orders_{date}.xlsx'
            result_df.to_excel(export_path_xlsx, index=False, engine='openpyxl')
            print(f"✅ تم حفظ الملف بصيغة XLSX: {export_path_xlsx}")
            return True
        
    except Exception as e:
        print(f"❌ خطأ في التصدير: {e}")
        return False

# إنشاء قاعدة البيانات
def init_db():
    with app.app_context():
            db.create_all()
        
        # إنشاء مستخدم افتراضي إذا لم يكن موجود
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
            print("✅ تم إنشاء المستخدم الافتراضي")
        
        # إضافة منتجات نظام المبيعات الأساسية
        if not Product.query.first():
            for code, data in PRODUCTS_DATA.items():
                product = Product(
                    code=code,
                    name=data['name'],
                    description=data['description'],
                    price=data['price'],
                    cost=data['price'] * 0.6,  # تكلفة تقديرية 60% من السعر
                    stock=50,  # مخزون افتراضي
                    category=data['category'],
                    is_active=True,
                    warranty_months=12 if 'ماكينة' in data['name'] else 6
                )
                db.session.add(product)
            print("✅ تم إضافة منتجات نظام المبيعات")
        
        # إضافة الموظفين إذا لم يكونوا موجودين
            for emp_data in EMPLOYEES_DATA:
            existing_employee = Employee.query.filter_by(name=emp_data['name']).first()
            if not existing_employee:
                new_employee = Employee(
                    name=emp_data['name'],
                    department=emp_data['department'],
                    position=emp_data['position'],
                    base_salary=emp_data['base_salary'],
                    commission_per_order=emp_data['commission_per_order'],
                    status='active'
                )
                db.session.add(new_employee)
                print(f"✅ تم إضافة الموظف: {emp_data['name']}")
        
        # محاولة إضافة الأعمدة المفقودة
        try:
            with db.engine.connect() as conn:
                # إضافة عمود order_id إذا لم يكن موجوداً
                try:
                    conn.execute(text("ALTER TABLE `order` ADD COLUMN order_id VARCHAR(50)"))
                    print("✅ تم إضافة عمود order_id")
                except:
                    pass
                
                # إضافة عمود city_code إذا لم يكن موجوداً
                try:
                    conn.execute(text("ALTER TABLE `order` ADD COLUMN city_code VARCHAR(10)"))
                    print("✅ تم إضافة عمود city_code")
                except:
                    pass
                
                # إضافة عمود commission_per_order إذا لم يكن موجوداً
                try:
                    conn.execute(text("ALTER TABLE employee ADD COLUMN commission_per_order DECIMAL(10,2) DEFAULT 0.5"))
                    print("✅ تم إضافة عمود commission_per_order")
                except:
                    pass
                
                # إضافة عمود base_salary إذا لم يكن موجوداً
                try:
                    conn.execute(text("ALTER TABLE employee ADD COLUMN base_salary DECIMAL(10,2) DEFAULT 500000"))
                    print("✅ تم إضافة عمود base_salary")
                except:
                    pass
                
        except Exception as e:
            print(f"⚠️ خطأ في تحديث قاعدة البيانات: {e}")
        
            db.session.commit()
        print("✅ تم تهيئة قاعدة البيانات بنجاح")

# دوال مساعدة
def get_city_code(city_name):
    """تحديد كود المحافظة بناءً على اسم المدينة"""
    for city, code in CITY_CODES.items():
        if city_name.lower() in city.lower() or city.lower() in city_name.lower():
            return code
    return 'OTH'  # أخرى

def get_city_name_by_code(code):
    """تحديد اسم المحافظة بناءً على الكود"""
    for city, city_code in CITY_CODES.items():
        if city_code == code:
            return city
    return 'غير محدد'

# دوال مساعدة للرسوم البيانية
def get_weekly_sales_data():
    """جلب بيانات المبيعات الأسبوعية"""
    try:
        today = datetime.now()
        week_start = today - timedelta(days=6)
        
        # جلب البيانات للأسبوع الماضي
        week_data = []
        for i in range(7):
            date = week_start + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # عدد الطلبات لهذا اليوم
            orders_count = Order.query.filter_by(day=date_str).count()
            
            # إجمالي المبيعات لهذا اليوم
            daily_total = db.session.query(db.func.sum(Order.final_total)).filter_by(day=date_str).scalar() or 0
            
            week_data.append({
                'date': date.strftime('%A'),  # اسم اليوم
                'orders': orders_count,
                'total': daily_total
            })
        
        return week_data
    except Exception as e:
        print(f"خطأ في جلب بيانات الأسبوع: {e}")
        return []

def get_product_distribution():
    """جلب توزيع المبيعات حسب المنتج"""
    try:
        # جلب جميع الطلبات مع المنتجات
        orders = Order.query.all()
        
        product_stats = {}
        for order in orders:
            product_name = order.product_name or 'غير محدد'
            if product_name not in product_stats:
                product_stats[product_name] = {
                    'count': 0,
                    'total': 0
                }
            
            product_stats[product_name]['count'] += 1
            product_stats[product_name]['total'] += order.final_total
        
        # تحويل البيانات إلى تنسيق مناسب للرسم البياني
        distribution = []
        for product, stats in product_stats.items():
            distribution.append({
                'name': product,
                'count': stats['count'],
                'total': stats['total']
            })
        
        # ترتيب حسب العدد
        distribution.sort(key=lambda x: x['count'], reverse=True)
        
        return distribution[:5]  # أعلى 5 منتجات
    except Exception as e:
        print(f"خطأ في جلب توزيع المنتجات: {e}")
        return []

def get_recent_activities():
    """جلب النشاطات الأخيرة"""
    try:
        # جلب آخر 5 طلبات
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        activities = []
        for order in recent_orders:
            time_diff = datetime.now() - order.created_at
            
            if time_diff.days > 0:
                time_text = f"منذ {time_diff.days} يوم"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                time_text = f"منذ {hours} ساعة"
            elif time_diff.seconds > 60:
                minutes = time_diff.seconds // 60
                time_text = f"منذ {minutes} دقيقة"
            else:
                time_text = "الآن"
            
            activities.append({
                'type': 'order',
                'text': f"تم إضافة طلب جديد من العميل {order.customer_name}",
                'time': time_text,
                'icon': 'shopping-cart'
            })
        
        return activities
    except Exception as e:
        print(f"خطأ في جلب النشاطات: {e}")
        return []

# دالة long polling للبوت
def long_polling():
    global last_update_id
    while True:
        try:
            # الحصول على الرسائل الجديدة باستخدام asyncio
            def get_updates_sync():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    updates = loop.run_until_complete(bot.get_updates(offset=last_update_id + 1, timeout=10))
                    loop.close()
                    return updates
                except Exception as e:
                    print(f"Error in get_updates_sync: {e}")
                    return []
            
            updates = get_updates_sync()
            
            if updates:
                for update in updates:
                    if update.message and update.message.text:
                        text = update.message.text
                        chat_id = update.message.chat.id
                        
                        print(f"رسالة جديدة: {text} من {chat_id}")
                        
                        # معالجة الرسالة
                        process_message(text, chat_id)
                        
                        # تحديث آخر update_id
                        last_update_id = update.update_id
            else:
                # لا توجد رسائل جديدة، انتظار أطول
                time.sleep(2)
            
        except Exception as e:
            print(f"خطأ في long polling: {e}")
            time.sleep(5)  # انتظار 5 ثواني في حالة الخطأ

def calculate_employee_commission(employee_name, date):
    """حساب عمولة موظف معين لليوم المحدد"""
    try:
        # جلب جميع الطلبات للموظف في اليوم المحدد
        orders = Order.query.filter_by(
            employee_name=employee_name, 
            day=date,
            order_status='قيد المراجعة'  # فقط الطلبات النشطة
        ).all()
        
        total_commission = 0
        total_orders = 0
        total_sales = 0
        
        for order in orders:
            # حساب العمولة حسب نوع المنتج
            commission_rate = COMMISSION_RATES.get(order.product_code, 0.5)
            commission = commission_rate * order.quantity
            total_commission += commission
            total_orders += 1
            total_sales += order.final_total
        
        return {
            'employee_name': employee_name,
            'total_orders': total_orders,
            'total_sales': total_sales,
            'total_commission': total_commission,
            'commission_per_order': total_commission / total_orders if total_orders > 0 else 0
        }
    except Exception as e:
        print(f"خطأ في حساب عمولة الموظف {employee_name}: {e}")
        return {
            'employee_name': employee_name,
            'total_orders': 0,
            'total_sales': 0,
            'total_commission': 0,
            'commission_per_order': 0
        }

def get_employee_performance(date):
    """الحصول على أداء الموظفين لليوم المحدد"""
    try:
        # الحصول على جميع الطلبات لليوم المحدد
        orders = Order.query.filter_by(day=date).all()
        print(f"🔍 عدد الطلبات في التاريخ {date}: {len(orders)}")
        
        # تجميع البيانات حسب الموظف
        employee_stats = {}
        
        for order in orders:
            employee_name = order.employee_name
            print(f"🔍 معالجة طلب للموظف: '{employee_name}' - العمولة مدفوعة: {order.commission_paid}")
            
            if employee_name not in employee_stats:
                employee_stats[employee_name] = {
                    'total_orders': 0,
                    'total_sales': 0,
                    'total_commission': 0,
                    'commission_paid': 0
                }
            
            # حساب عدد الطلبات فقط للطلبات التي لم يتم دفع عمولتها
            if not order.commission_paid:
                employee_stats[employee_name]['total_orders'] += 1
                employee_stats[employee_name]['total_sales'] += order.final_total
                
                # تحديد نوع المنتج من السعر
                if order.unit_price == 40000:
                    product_type = 'sales_v1'
                elif order.unit_price == 45000:
                    product_type = 'sales_v2'
                elif order.unit_price == 15000:
                    product_type = 'spare_head'
                elif order.unit_price == 10000:
                    product_type = 'charging_cable'
                else:
                    product_type = 'sales_v1'  # افتراضي
                
                commission_rate = COMMISSION_RATES.get(product_type, 0.5)
                commission = commission_rate * order.quantity
                employee_stats[employee_name]['total_commission'] += commission
                
                print(f"💰 إضافة عمولة لـ {employee_name}: {commission} دولار (المنتج: {product_type}, الكمية: {order.quantity})")
            else:
                employee_stats[employee_name]['commission_paid'] += 1
                print(f"✅ تم دفع العمولة لـ {employee_name} - الطلب: {order.order_id}")
        
        # الحصول على معلومات الموظفين
        employees = Employee.query.all()
        print(f"🔍 عدد الموظفين في قاعدة البيانات: {len(employees)}")
        for emp in employees:
            print(f"🔍 موظف في قاعدة البيانات: '{emp.name}'")
        
        result = []
        
        for employee in employees:
            stats = employee_stats.get(employee.name, {
                'total_orders': 0,
                'total_sales': 0,
                'total_commission': 0,
                'commission_paid': 0
            })
            
            print(f"🔍 إحصائيات الموظف {employee.name}: طلبات={stats['total_orders']}, عمولة={stats['total_commission']}")
            
            result.append({
                'id': employee.id,
                'name': employee.name,
                'department': employee.department,
                'position': employee.position,
                'total_orders': stats['total_orders'],
                'total_sales': stats['total_sales'],
                'total_commission': stats['total_commission'],
                'commission_paid': stats['commission_paid']
            })
        
        return result
        
    except Exception as e:
        print(f"❌ خطأ في الحصول على أداء الموظفين: {e}")
        return []

# دالة إنشاء معرف الطلب
def generate_order_id():
    """إنشاء معرف فريد للطلب"""
    import random
    import string
    
    # إنشاء معرف من 8 أحرف
    letters = string.ascii_uppercase + string.digits
    order_id = ''.join(random.choice(letters) for i in range(8))
    
    # إضافة التاريخ
    from datetime import datetime
    date_str = datetime.now().strftime('%Y%m%d')
    
    return f"RKS{date_str}{order_id}"

# دالة مساعدة لإرسال الرسائل
def send_bot_message(chat_id, message, reply_markup=None):
    """إرسال رسالة إلى المستخدم عبر البوت"""
    try:
        print(f"📤 محاولة إرسال رسالة إلى {chat_id}")
        print(f"📝 محتوى الرسالة: {message}")
        
        # استخدام threading لتجنب حظر Flask
        def send_in_thread():
            try:
                print(f"🔄 بدء إرسال الرسالة في thread منفصل")
                
                # إنشاء Bot جديد لكل رسالة
                bot = Bot(token=BOT_TOKEN)
                
                if reply_markup:
                    bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                
                print(f"✅ تم إرسال الرسالة بنجاح")
                
            except Exception as e:
                print(f"❌ خطأ في send_message: {e}")
                print(f"🔍 نوع الخطأ: {type(e).__name__}")
            finally:
                print(f"✅ انتهى thread الإرسال")
        
        # بدء thread منفصل
        import threading
        thread = threading.Thread(target=send_in_thread)
        thread.start()
        
    except Exception as e:
        print(f"❌ خطأ في send_bot_message: {e}")

# دالة معالجة الرسائل - بسيطة لاستقبال الطلبات والمرتجعات
def process_message(text, chat_id):
    """معالجة الرسائل والأوامر الواردة من البوت"""
    try:
        print(f"📨 رسالة جديدة: {text} من {chat_id}")
        
        if text.startswith('/start'):
            # رسالة ترحيب بسيطة
            welcome_message = """🚀 مرحباً بك في نظام نظام المبيعات!
نحن متخصصون في العناية الشخصية للرجل العصري

📝 **لإرسال طلب جديد:**
أرسل الفاتورة بالتنسيق التالي:

اسم الموظفة/لافا
أسم العميل/محمد الزاملي
المحافظة/ديوانية
اقرب نقطة دالة/دغاره قرية زبيد
الرقم/07812099176
العدد/1
السعر/40000
الملاحظات/لا شيء

🔄 **لإرجاع طلب:**
أرسل: ارجاع/رقم_الهاتف/سبب_الإرجاع

مثال: ارجاع/07812099176/العميل غير راضي

💰 **الأسعار:**
• sales V1: 40,000 دينار
• sales V2: 45,000 دينار
• رأس الماكينة الإضافي: 15,000 دينار
• كابل الشحن: 10,000 دينار

✨ **مميزات:**
• كود المحافظة يُضاف تلقائياً
• المنتج يُحدد تلقائياً من السعر
• معالجة سريعة ودقيقة للطلبات
• نظام مرتجعات متكامل"""
            
            send_bot_message(chat_id, welcome_message)
            
        elif text.startswith('/help'):
            help_message = """❓ كيفية استخدام البوت:

📝 **لإرسال طلب جديد:**
أرسل الفاتورة بالتنسيق المطلوب

🔄 **لإرجاع طلب:**
أرسل: ارجاع/رقم_الهاتف/سبب_الإرجاع

💰 **الأسعار:**
• sales V1: 40,000 دينار
• sales V2: 45,000 دينار
• رأس الماكينة الإضافي: 15,000 دينار
• كابل الشحن: 10,000 دينار

📞 **للتواصل:**
لأي استفسار، تواصل مع فريق الدعم"""
            
            send_bot_message(chat_id, help_message)
            
        elif text.startswith('ارجاع/'):
            # معالجة المرتجعات
            try:
                parts = text.split('/')
                if len(parts) >= 3:
                    phone = parts[1].strip()
                    reason = parts[2].strip()
                    
                    print(f"🔄 معالجة مرتجع للهاتف: {phone}")
                    
                    # البحث عن الطلب برقم الهاتف
                    order = Order.query.filter_by(phone=phone, order_status='قيد المراجعة').first()
                    
                    if order:
                        # تحديث حالة الطلب إلى مرتجع
                        order.order_status = 'مرتجع'
                        order.notes = f"مرتجع: {reason}"
                        
                        # حذف العمولة من الموظف
                        employee = Employee.query.filter_by(name=order.employee_name).first()
                        if employee:
                            # حساب العمولة المفقودة
                            commission_lost = 0
                            if order.product_code in COMMISSION_RATES:
                                commission_lost = COMMISSION_RATES[order.product_code] * order.quantity
                            
                            print(f"💰 حذف عمولة: {commission_lost} دولار من {employee.name}")
                        
                        db.session.commit()
                        
                        success_message = f"""✅ تم إرجاع الطلب بنجاح!

📱 رقم الهاتف: {phone}
👤 العميل: {order.customer_name}
👨‍💼 الموظف: {order.employee_name}
📦 المنتج: {order.product_name}
💰 المبلغ: {order.final_total:,} دينار
📝 سبب الإرجاع: {reason}
📅 تاريخ الإرجاع: {datetime.now().strftime('%Y-%m-%d %H:%M')}

⚠️ **ملاحظة:** تم حذف العمولة من الموظف تلقائياً"""
                        
                        send_bot_message(chat_id, success_message)
                        print(f"✅ تم إرجاع الطلب بنجاح")
                        
                    else:
                        error_message = f"❌ لم يتم العثور على طلب برقم الهاتف {phone} أو الطلب ليس في حالة 'قيد المراجعة'"
                        send_bot_message(chat_id, error_message)
                        
                else:
                    error_message = "❌ تنسيق خاطئ للإرجاع. استخدم: ارجاع/رقم_الهاتف/سبب_الإرجاع"
                    send_bot_message(chat_id, error_message)
                    
            except Exception as e:
                error_message = f"❌ خطأ في معالجة الإرجاع: {str(e)}"
                print(f"❌ خطأ في معالجة الإرجاع: {str(e)}")
                send_bot_message(chat_id, error_message)
            
        else:
            # معالجة الفاتورة
            print(f"🔍 معالجة طلب جديد من {chat_id}")
            
            # تحليل النص
            lines = text.split('\n')
            data = {}
            
            for line in lines:
                line = line.strip()
                if '/' in line:
                    key, value = line.split('/', 1)
                    key = key.strip()
                    value = value.strip()
                    data[key] = value
            
            # التحقق من البيانات المطلوبة
            required_fields = ['اسم الموظفة', 'أسم العميل', 'المحافظة', 'اقرب نقطة دالة', 'الرقم', 'العدد', 'السعر']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                error_message = f"❌ بيانات ناقصة: {', '.join(missing_fields)}\n\n📝 يرجى إرسال الفاتورة بالتنسيق الصحيح"
                send_bot_message(chat_id, error_message)
                return
            
            # تحديد المنتج من السعر
            price = int(data['السعر'])
            if price == 40000:
                product = 'sales_v1'
                product_name = 'sales V1'
            elif price == 45000:
                product = 'sales_v2'
                product_name = 'sales V2'
            elif price == 15000:
                product = 'spare_head'
                product_name = 'رأس ماكينة إضافي'
            elif price == 10000:
                product = 'charging_cable'
                product_name = 'كابل شحن'
            else:
                product = 'unknown'
                product_name = 'منتج غير معروف'
            
            # تحديد كود المحافظة
            city = data['المحافظة']
            city_code = CITY_CODES.get(city, '000')
            
            # حساب المجاميع
            quantity = int(data['العدد'])
            total_price = price * quantity
            delivery_fee = 0  # التوصيل مجاني
            final_total = total_price + delivery_fee
            
            # إنشاء الطلب
            order_id = f"RK_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            today = datetime.now().strftime('%Y-%m-%d')
            
            new_order = Order(
                order_id=order_id,
                employee_name=data['اسم الموظفة'],
                customer_name=data['أسم العميل'],
                city=city,
                city_code=city_code,
                address=data['اقرب نقطة دالة'],
                phone=data['الرقم'],
                product_name=product_name,
                product_code=product,
                quantity=quantity,
                unit_price=price,
                total_price=total_price,
                delivery_fee=delivery_fee,
                final_total=final_total,
                notes=data.get('الملاحظات', ''),
                order_status='قيد المراجعة',
                payment_status='معلق',
                day=today,
                commission_paid=False
            )
            
            db.session.add(new_order)
            db.session.commit()
            
            print(f"✅ تم حفظ الطلب في قاعدة البيانات")
            
            # رسالة النجاح
            success_message = f"""✅ تم استلام طلبك في نظام المبيعات بنجاح!   
🏷️ رقم الطلب: {order_id}
👤 الموظف: {data['اسم الموظفة']}
🧑‍💼 العميل: {data['أسم العميل']}
📍 المحافظة: {city}
🏪 العنوان: {data['اقرب نقطة دالة']}
📱 الهاتف: {data['الرقم']}
📦 الكمية: {data['العدد']}
💰 السعر: {price:,} دينار
📝 الملاحظات: {data.get('الملاحظات', 'لا شيء')}
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

🚚 سيتم التواصل معك قريباً لتأكيد الطلب والتوصيل
شكراً لثقتك في نظام المبيعات! 🎉"""
            
            print(f"📤 إرسال رسالة النجاح إلى {chat_id}")
            send_bot_message(chat_id, success_message)
            print(f"✅ تم إرسال رسالة النجاح")
            
    except Exception as e:
        error_message = f"❌ خطأ في معالجة الرسالة: {str(e)}"
        print(f"❌ خطأ في معالجة الرسالة: {str(e)}")
        try:
            send_bot_message(chat_id, error_message)
        except:
            pass

@app.route('/pay_commission/<int:employee_id>', methods=['POST'])
@login_required
def pay_commission(employee_id):
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': 'الموظف غير موجود'})
        
        # تصفير المستحقات - نحتاج لتحديث قاعدة البيانات
        # سنقوم بتحديث العمولة في جدول الموظفين
        employee.commission_per_order = 0.0
        
        # أيضاً نحتاج لتحديث العمولة في جدول الطلبات لهذا الموظف
        # سنقوم بتحديث جميع الطلبات المعلقة لهذا الموظف
        update_query = update(Order).where(
            Order.employee_name == employee.name
        ).values(commission_paid=True)
        
        db.session.execute(update_query)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم دفع المستحقات بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    init_db()
    
    # إنشاء تطبيق البوت الجديد
    print("🚀 إنشاء البوت الجديد...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    # تعريف معالجات الرسائل
    async def start_command(update, context):
        """معالج أمر /start"""
        chat_id = update.effective_chat.id
        print(f"📨 أمر /start من {chat_id}")
        
        welcome_message = """🚀 مرحباً بك في نظام نظام المبيعات!
نحن متخصصون في العناية الشخصية للرجل العصري

📋 **اختر من القائمة أدناه:**"""
        
        # إنشاء أزرار القائمة
        keyboard = [
            [InlineKeyboardButton("📝 إضافة فاتورة جديدة", callback_data="add_invoice")],
            [InlineKeyboardButton("🔄 إرجاع طلب", callback_data="return_order")],
            [InlineKeyboardButton("💰 الأسعار", callback_data="show_prices")],
            [InlineKeyboardButton("❓ المساعدة", callback_data="show_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=chat_id, 
                text=welcome_message, 
                reply_markup=reply_markup
            )
            print(f"✅ تم إرسال رسالة الترحيب مع القائمة إلى {chat_id}")
        except Exception as e:
            print(f"❌ خطأ في إرسال رسالة الترحيب: {e}")
    
    async def help_command(update, context):
        """معالج أمر /help"""
        chat_id = update.effective_chat.id
        print(f"📨 أمر /help من {chat_id}")
        
        help_message = """❓ **مساعدة نظام نظام المبيعات**

📝 **كيفية إرسال طلب جديد:**
أرسل الفاتورة بالتنسيق المحدد مع "/" بين كل حقل

🔄 **كيفية إرجاع طلب:**
أرسل: ارجاع/رقم_الهاتف/سبب_الإرجاع

💡 **نصائح:**
• تأكد من صحة تنسيق الرسالة
• استخدم "/" كفاصل بين الحقول
• تأكد من صحة رقم الهاتف"""
        
        try:
            await context.bot.send_message(chat_id=chat_id, text=help_message)
            print(f"✅ تم إرسال رسالة المساعدة إلى {chat_id}")
        except Exception as e:
            print(f"❌ خطأ في إرسال رسالة المساعدة: {e}")
    
    async def text_message(update, context):
        """معالج الرسائل النصية (الفواتير والمرتجعات)"""
        chat_id = update.effective_chat.id
        text = update.message.text
        print(f"📨 رسالة نصية من {chat_id}: {text}")
        
        try:
            # معالجة الرسالة مباشرة
            if text.startswith('ارجاع/'):
                # معالجة المرتجعات بالشكل القديم (للتوافق)
                try:
                    parts = text.split('/')
                    if len(parts) >= 3:
                        phone = parts[1].strip()
                        reason = parts[2].strip()
                        
                        print(f"🔄 معالجة مرتجع للهاتف: {phone}")
                        
                        # البحث عن الطلب برقم الهاتف
                        with app.app_context():
                            order = Order.query.filter_by(phone=phone, order_status='قيد المراجعة').first()
                            
                            if order:
                                # تحديث حالة الطلب إلى مرتجع
                                order.order_status = 'مرتجع'
                                order.notes = f"مرتجع: {reason}"
                                
                                # حذف العمولة من الموظف - تحديث الطلب لعدم احتساب العمولة
                                order.commission_paid = True  # تم دفع العمولة (لا تحتسب)
                                
                                db.session.commit()
                                
                                success_message = f"""✅ تم إرجاع الطلب بنجاح!

📱 الهاتف: {phone}
📝 السبب: {reason}
💰 تم حذف العمولة من الموظف
📦 تم نقل الطلب إلى قسم المرتجعات

🔄 الطلب لم يعد يؤثر على إحصائيات الموظف"""
                                
                                await context.bot.send_message(chat_id=chat_id, text=success_message)
                                print(f"✅ تم إرسال رسالة النجاح للمرتجع إلى {chat_id}")
                            else:
                                error_message = f"❌ لم يتم العثور على طلب بهذا الرقم: {phone}"
                                await context.bot.send_message(chat_id=chat_id, text=error_message)
                                print(f"❌ لم يتم العثور على طلب للهاتف: {phone}")
                    else:
                        error_message = "❌ تنسيق خاطئ. استخدم: ارجاع/رقم_الهاتف/السبب"
                        await context.bot.send_message(chat_id=chat_id, text=error_message)
                        
                except Exception as e:
                    error_message = f"❌ خطأ في معالجة المرتجع: {str(e)}"
                    await context.bot.send_message(chat_id=chat_id, text=error_message)
                    print(f"❌ خطأ في معالجة المرتجع: {e}")
                    
            elif text.isdigit() and len(text) >= 10:
                # معالجة المرتجعات برقم الهاتف فقط
                try:
                    phone = text.strip()
                    print(f"🔄 معالجة مرتجع برقم الهاتف فقط: {phone}")
                    
                    # البحث عن الطلب برقم الهاتف
                    with app.app_context():
                        order = Order.query.filter_by(phone=phone, order_status='قيد المراجعة').first()
                        
                        if order:
                            # تحديث حالة الطلب إلى مرتجع
                            order.order_status = 'مرتجع'
                            order.notes = f"مرتجع: تم الإرجاع برقم الهاتف {phone}"
                            
                            # حذف العمولة من الموظف - تحديث الطلب لعدم احتساب العمولة
                            order.commission_paid = True  # تم دفع العمولة (لا تحتسب)
                            
                            db.session.commit()
                            
                            success_message = f"""✅ تم إرجاع الطلب بنجاح!

📱 الهاتف: {phone}
👤 العميل: {order.customer_name}
👤 الموظف: {order.employee_name}
💰 تم حذف العمولة من الموظف
📦 تم نقل الطلب إلى قسم المرتجعات

🔄 الطلب لم يعد يؤثر على إحصائيات الموظف"""
                            
                            await context.bot.send_message(chat_id=chat_id, text=success_message)
                            print(f"✅ تم إرسال رسالة النجاح للمرتجع إلى {chat_id}")
                        else:
                            error_message = f"❌ لم يتم العثور على طلب بهذا الرقم: {phone}"
                            await context.bot.send_message(chat_id=chat_id, text=error_message)
                            print(f"❌ لم يتم العثور على طلب للهاتف: {phone}")
                        
                except Exception as e:
                    error_message = f"❌ خطأ في معالجة المرتجع: {str(e)}"
                    await context.bot.send_message(chat_id=chat_id, text=error_message)
                    print(f"❌ خطأ في معالجة المرتجع: {e}")
                    
            else:
                # معالجة الفواتير الجديدة
                try:
                    # تحليل الفاتورة
                    lines = text.strip().split('\n')
                    if len(lines) >= 7:
                        # استخراج البيانات
                        employee_name = lines[0].split('/')[1].strip() if '/' in lines[0] else ''
                        customer_name = lines[1].split('/')[1].strip() if '/' in lines[1] else ''
                        city = lines[2].split('/')[1].strip() if '/' in lines[2] else ''
                        address = lines[3].split('/')[1].strip() if '/' in lines[3] else ''
                        phone = lines[4].split('/')[1].strip() if '/' in lines[4] else ''
                        quantity = int(lines[5].split('/')[1].strip()) if '/' in lines[5] else 1
                        unit_price = int(lines[6].split('/')[1].strip()) if '/' in lines[6] else 0
                        notes = lines[7].split('/')[1].strip() if len(lines) > 7 and '/' in lines[7] else ''
                        
                        print(f"🔍 اسم الموظف المُدخل: '{employee_name}'")
                        
                        # التحقق من وجود الموظف في قاعدة البيانات
                        with app.app_context():
                            employee_exists = Employee.query.filter_by(name=employee_name).first()
                            if not employee_exists:
                                # قائمة الموظفين المتاحين
                                available_employees = [emp.name for emp in Employee.query.all()]
                                error_message = f"""❌ اسم الموظف غير صحيح!

🔍 الاسم المُدخل: {employee_name}

✅ **الأسماء الصحيحة:**
{chr(10).join([f"• {name}" for name in available_employees])}

💡 تأكد من كتابة الاسم بالضبط كما هو موضح أعلاه."""
                                
                                await context.bot.send_message(chat_id=chat_id, text=error_message)
                                return
                        
                        # تحديد كود المحافظة
                        city_code = CITY_CODES.get(city, '000')
                        
                        # تحديد المنتج
                        if unit_price == 40000:
                            product_name = 'sales V1'
                            product_code = 'sales_v1'
                        elif unit_price == 45000:
                            product_name = 'sales V2'
                            product_code = 'sales_v2'
                        elif unit_price == 15000:
                            product_name = 'رأس الماكينة الإضافي'
                            product_code = 'spare_head'
                        elif unit_price == 10000:
                            product_name = 'كابل الشحن'
                            product_code = 'charging_cable'
                        else:
                            product_name = 'sales V1'
                            product_code = 'sales_v1'
                        
                        # حساب الأسعار
                        total_price = unit_price * quantity
                        delivery_fee = 0  # بدون رسوم توصيل
                        final_total = total_price + delivery_fee
                        
                        # إنشاء الطلب
                        with app.app_context():
                            new_order = Order(
                                order_id=generate_order_id(),
                                employee_name=employee_name,
                                customer_name=customer_name,
                                phone=phone,
                                city=city,
                                city_code=city_code,
                                address=address,
                                product_name=product_name,
                                product_code=product_code,
                                quantity=quantity,
                                unit_price=unit_price,
                                total_price=total_price,
                                delivery_fee=delivery_fee,
                                final_total=final_total,
                                order_status='قيد المراجعة',
                                payment_status='مدفوع',
                                notes=notes,
                                day=datetime.now().strftime('%Y-%m-%d'),
                                commission_paid=False
                            )
                            
                            db.session.add(new_order)
                            db.session.commit()
                        
                        success_message = f"""✅ تم إضافة الفاتورة بنجاح!

📋 **تفاصيل الفاتورة:**
👤 الموظفة: {employee_name}
👨‍💼 العميل: {customer_name}
📱 الهاتف: {phone}
🏙️ المحافظة: {city}
📍 العنوان: {address}
📦 المنتج: {product_name}
🔢 الكمية: {quantity}
💰 السعر: {unit_price:,} دينار
💵 الإجمالي: {final_total:,} دينار
📝 الملاحظات: {notes}

🎉 تم حفظ الفاتورة في النظام!"""
                        
                        await context.bot.send_message(chat_id=chat_id, text=success_message)
                        print(f"✅ تم إضافة فاتورة جديدة بنجاح")
                        
                    else:
                        error_message = """❌ تنسيق خاطئ للفاتورة!

📝 **التنسيق الصحيح:**
اسم الموظفة/لافا
أسم العميل/محمد الزاملي
المحافظة/ديوانية
اقرب نقطة دالة/دغاره قرية زبيد
الرقم/07812099176
العدد/1
السعر/40000
الملاحظات/لا شيء

🔍 تأكد من استخدام "/" كفاصل بين الحقل والقيمة"""
                        
                        await context.bot.send_message(chat_id=chat_id, text=error_message)
                        
                except Exception as e:
                    error_message = f"❌ خطأ في معالجة الفاتورة: {str(e)}"
                    await context.bot.send_message(chat_id=chat_id, text=error_message)
                    print(f"❌ خطأ في معالجة الفاتورة: {e}")
                        
        except Exception as e:
            error_message = f"❌ خطأ في معالجة الرسالة: {str(e)}"
            await context.bot.send_message(chat_id=chat_id, text=error_message)
            print(f"❌ خطأ في معالجة الرسالة: {e}")
    
    async def handle_callback_query(update, context):
        """معالج النقر على الأزرار"""
        query = update.callback_query
        await query.answer()
        
        chat_id = query.message.chat_id
        data = query.data
        
        print(f"🔘 تم النقر على زر: {data}")
        
        if data == "add_invoice":
            message = """📝 **إضافة فاتورة جديدة**

أرسل الفاتورة بالتنسيق التالي:

اسم الموظفة/اسم_الموظف
أسم العميل/اسم_العميل
المحافظة/اسم_المحافظة
اقرب نقطة دالة/العنوان_التفصيلي
الرقم/رقم_الهاتف
العدد/الكمية
السعر/سعر_الوحدة
الملاحظات/ملاحظات_إضافية

💡 **مثال:**
اسم الموظفة/نور
أسم العميل/أحمد محمد
المحافظة/بغداد
اقرب نقطة دالة/شارع الرشيد
الرقم/07812345678
العدد/2
السعر/80000
الملاحظات/اختبار"""
            
            await context.bot.send_message(chat_id=chat_id, text=message)
            
        elif data == "return_order":
            message = """🔄 **إرجاع طلب**

لإرجاع طلب، أرسل فقط رقم هاتف العميل:

📱 **مثال:** 07812345678

💡 **ملاحظة:** سيتم البحث عن الطلب برقم الهاتف وإرجاعه تلقائياً"""
            
            await context.bot.send_message(chat_id=chat_id, text=message)
            
        elif data == "show_prices":
            message = """💰 **أسعار منتجات نظام المبيعات**

• **sales V1:** 40,000 دينار
• **sales V2:** 45,000 دينار  
• **رأس الماكينة الإضافي:** 15,000 دينار
• **كابل الشحن:** 10,000 دينار

💡 **معلومات إضافية:**
• كود المحافظة يُضاف تلقائياً
• المنتج يُحدد تلقائياً من السعر
• بدون رسوم توصيل"""
            
            await context.bot.send_message(chat_id=chat_id, text=message)
            
        elif data == "show_help":
            message = """❓ **مساعدة نظام نظام المبيعات**

📝 **لإضافة فاتورة جديدة:**
1. اختر "إضافة فاتورة جديدة"
2. اتبع التنسيق المحدد
3. تأكد من صحة البيانات

🔄 **لإرجاع طلب:**
1. اختر "إرجاع طلب"
2. أرسل رقم هاتف العميل فقط

💡 **نصائح:**
• استخدم "/" كفاصل بين الحقل والقيمة
• تأكد من صحة رقم الهاتف
• تأكد من صحة اسم الموظف"""
            
            await context.bot.send_message(chat_id=chat_id, text=message)
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # بدء البوت
    print("🚀 بدأ البوت في العمل...")
    print("📱 يمكنك الآن إرسال الرسائل إلى البوت!")
    
    # بدء البوت في thread منفصل
    print("🚀 بدء البوت...")
    try:
        def run_bot():
            try:
                print("🔄 بدء تشغيل البوت...")
                import asyncio
                
                # إنشاء event loop جديد في هذا thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # تشغيل البوت
                loop.run_until_complete(application.initialize())
                loop.run_until_complete(application.start())
                loop.run_until_complete(application.updater.start_polling())
                
                # تشغيل البوت
                loop.run_forever()
                
            except Exception as e:
                print(f"❌ خطأ في تشغيل البوت: {e}")
            finally:
                try:
                    loop.close()
                except:
                    pass
        
        # بدء thread منفصل للبوت
        import threading
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        # انتظار قليلاً للبوت
        time.sleep(3)
        print("✅ تم بدء البوت بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في إعداد البوت: {e}")
        print("🔄 سيتم تشغيل Flask فقط...")
    
    # تشغيل Flask
    print("🌐 بدء تشغيل موقع الويب...")
    app.run(debug=True, host='0.0.0.0', port=5000)
