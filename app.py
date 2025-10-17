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
from functools import wraps

# إعداد Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sales-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# سيتم إضافة دالة has_permission إلى Jinja2 context بعد تعريفها

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
    {'name': 'نور', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 500},
    {'name': 'صبا', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 500},
    {'name': 'ميريانا', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 500},
    {'name': 'عيسى', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 500},
    {'name': 'إيمان', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 500},
    {'name': 'لافا', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 500},
    {'name': 'نغم', 'department': 'مبيعات', 'position': 'مندوب مبيعات', 'base_salary': 500000, 'commission_per_order': 500}
]

# نظام العمولات
COMMISSION_RATES = {
    'sales_v1': 500,  # 500 دينار لكل قطعة
    'sales_v2': 500,  # 500 دينار لكل قطعة
    'spare_head': 300,  # 300 دينار لكل قطعة
    'charging_cable': 200  # 200 دينار لكل قطعة
}

# نماذج قاعدة البيانات
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default='user')  # super_admin, admin, user
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقة مع الموظف
    employee = db.relationship('Employee', backref='user', uselist=False)
    
    # العلاقة مع الصلاحيات
    permissions = db.relationship('UserPermission', backref='user', lazy='dynamic', foreign_keys='UserPermission.user_id')

class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
    module = db.Column(db.String(50), nullable=False)  # invoices, employees, products, customers, reports
    action = db.Column(db.String(50), nullable=False)  # view, add, edit, delete, export
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserPermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'), nullable=False)
    granted = db.Column(db.Boolean, default=True)
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    permission = db.relationship('Permission', backref='user_permissions')
    granted_by_user = db.relationship('User', foreign_keys=[granted_by], backref='granted_permissions')

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
    commission_per_order = db.Column(db.Float, default=500)
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

# دوال إدارة الصلاحيات
def has_permission(user, module, action):
    """التحقق من صلاحية المستخدم"""
    if not user or not user.is_active:
        return False
    
    # السوبر أدمن له جميع الصلاحيات
    if user.role == 'super_admin':
        return True
    
    # البحث عن الصلاحية
    permission = Permission.query.filter_by(module=module, action=action).first()
    if not permission:
        return False
    
    # التحقق من وجود الصلاحية للمستخدم
    user_permission = UserPermission.query.filter_by(
        user_id=user.id,
        permission_id=permission.id,
        granted=True
    ).first()
    
    return user_permission is not None

def require_permission(module, action):
    """ديكوريتور للتحقق من الصلاحيات"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            
            if not has_permission(current_user, module, action):
                flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def init_permissions():
    """تهيئة الصلاحيات الأساسية"""
    permissions_data = [
        # صلاحيات الطلبات
        ('invoices_view', 'عرض الطلبات', 'invoices', 'view'),
        ('invoices_add', 'إضافة طلبات', 'invoices', 'add'),
        ('invoices_edit', 'تعديل الطلبات', 'invoices', 'edit'),
        ('invoices_delete', 'حذف الطلبات', 'invoices', 'delete'),
        ('invoices_export', 'تصدير الطلبات', 'invoices', 'export'),
        
        # صلاحيات الموظفين
        ('employees_view', 'عرض الموظفين', 'employees', 'view'),
        ('employees_add', 'إضافة موظفين', 'employees', 'add'),
        ('employees_edit', 'تعديل الموظفين', 'employees', 'edit'),
        ('employees_delete', 'حذف الموظفين', 'employees', 'delete'),
        ('employees_export', 'تصدير الموظفين', 'employees', 'export'),
        
        # صلاحيات المنتجات
        ('products_view', 'عرض المنتجات', 'products', 'view'),
        ('products_add', 'إضافة منتجات', 'products', 'add'),
        ('products_edit', 'تعديل المنتجات', 'products', 'edit'),
        ('products_delete', 'حذف المنتجات', 'products', 'delete'),
        ('products_export', 'تصدير المنتجات', 'products', 'export'),
        
        # صلاحيات العملاء
        ('customers_view', 'عرض العملاء', 'customers', 'view'),
        ('customers_add', 'إضافة عملاء', 'customers', 'add'),
        ('customers_edit', 'تعديل العملاء', 'customers', 'edit'),
        ('customers_delete', 'حذف العملاء', 'customers', 'delete'),
        ('customers_export', 'تصدير العملاء', 'customers', 'export'),
        
        # صلاحيات التقارير
        ('reports_view', 'عرض التقارير', 'reports', 'view'),
        ('reports_export', 'تصدير التقارير', 'reports', 'export'),
        
        # صلاحيات إدارة المستخدمين
        ('users_view', 'عرض المستخدمين', 'users', 'view'),
        ('users_add', 'إضافة مستخدمين', 'users', 'add'),
        ('users_edit', 'تعديل المستخدمين', 'users', 'edit'),
        ('users_delete', 'حذف المستخدمين', 'users', 'delete'),
        ('users_permissions', 'إدارة صلاحيات المستخدمين', 'users', 'permissions'),
    ]
    
    for perm_name, perm_desc, module, action in permissions_data:
        permission = Permission.query.filter_by(name=perm_name).first()
        if not permission:
            permission = Permission(
                name=perm_name,
                description=perm_desc,
                module=module,
                action=action
            )
            db.session.add(permission)
    
    db.session.commit()
    print("✅ تم تهيئة الصلاحيات الأساسية")

def create_super_admin():
    """إنشاء مستخدم سوبر أدمن"""
    super_admin = User.query.filter_by(role='super_admin').first()
    if not super_admin:
        super_admin = User(
            username='admin',
            email='admin@sales.com',
            full_name='مدير النظام',
            role='super_admin',
            is_active=True
        )
        super_admin.password_hash = generate_password_hash('admin123')
        db.session.add(super_admin)
        db.session.commit()
        print("✅ تم إنشاء مستخدم سوبر أدمن")
    return super_admin

# إضافة دالة has_permission إلى Jinja2 context
app.jinja_env.globals['has_permission'] = has_permission

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
            if not user.is_active:
                flash('الحساب معطل، يرجى التواصل مع المدير', 'error')
                return redirect(url_for('login'))
            
            # تحديث آخر دخول
            user.last_login = datetime.utcnow()
            db.session.commit()
            
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

# مسارات إدارة المستخدمين
@app.route('/users')
@login_required
@require_permission('users', 'view')
def users():
    """صفحة إدارة المستخدمين"""
    users_list = User.query.all()
    employees = Employee.query.filter_by(status='active').all()
    return render_template('users.html', users=users_list, employees=employees)

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
@require_permission('users', 'add')
def add_user():
    """إضافة مستخدم جديد"""
    if request.method == 'POST':
        try:
            # التحقق من عدم تكرار اسم المستخدم
            existing_user = User.query.filter_by(username=request.form['username']).first()
            if existing_user:
                flash('اسم المستخدم موجود مسبقاً', 'error')
                return redirect(url_for('add_user'))
            
            # إنشاء المستخدم الجديد
            user = User(
                username=request.form['username'],
                email=request.form['email'],
                full_name=request.form['full_name'],
                role=request.form['role'],
                employee_id=request.form.get('employee_id') or None,
                is_active=True
            )
            user.password_hash = generate_password_hash(request.form['password'])
            
            db.session.add(user)
            db.session.commit()
            
            flash('تم إضافة المستخدم بنجاح', 'success')
            return redirect(url_for('users'))
            
        except Exception as e:
            flash(f'خطأ في إضافة المستخدم: {str(e)}', 'error')
    
    employees = Employee.query.filter_by(status='active').all()
    return render_template('add_user.html', employees=employees)

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@require_permission('users', 'edit')
def edit_user(user_id):
    """تعديل مستخدم"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            user.username = request.form['username']
            user.email = request.form['email']
            user.full_name = request.form['full_name']
            user.role = request.form['role']
            user.employee_id = request.form.get('employee_id') or None
            user.is_active = request.form.get('is_active') == 'on'
            
            if request.form.get('password'):
                user.password_hash = generate_password_hash(request.form['password'])
            
            db.session.commit()
            flash('تم تحديث المستخدم بنجاح', 'success')
            return redirect(url_for('users'))
            
        except Exception as e:
            flash(f'خطأ في تحديث المستخدم: {str(e)}', 'error')
    
    employees = Employee.query.filter_by(status='active').all()
    return render_template('edit_user.html', user=user, employees=employees)

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@require_permission('users', 'delete')
def delete_user(user_id):
    """حذف مستخدم"""
    try:
        user = User.query.get_or_404(user_id)
        
        # منع حذف السوبر أدمن
        if user.role == 'super_admin':
            flash('لا يمكن حذف مستخدم سوبر أدمن', 'error')
            return redirect(url_for('users'))
        
        # حذف صلاحيات المستخدم
        UserPermission.query.filter_by(user_id=user_id).delete()
        
        db.session.delete(user)
        db.session.commit()
        
        flash('تم حذف المستخدم بنجاح', 'success')
        
    except Exception as e:
        flash(f'خطأ في حذف المستخدم: {str(e)}', 'error')
    
    return redirect(url_for('users'))

@app.route('/users/permissions/<int:user_id>', methods=['GET', 'POST'])
@login_required
@require_permission('users', 'permissions')
def user_permissions(user_id):
    """إدارة صلاحيات المستخدم"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            # حذف الصلاحيات الحالية
            UserPermission.query.filter_by(user_id=user_id).delete()
            
            # إضافة الصلاحيات الجديدة
            for permission_id in request.form.getlist('permissions'):
                user_permission = UserPermission(
                    user_id=user_id,
                    permission_id=int(permission_id),
                    granted=True,
                    granted_by=current_user.id
                )
                db.session.add(user_permission)
            
            db.session.commit()
            flash('تم تحديث صلاحيات المستخدم بنجاح', 'success')
            return redirect(url_for('users'))
            
        except Exception as e:
            flash(f'خطأ في تحديث الصلاحيات: {str(e)}', 'error')
    
    # جلب جميع الصلاحيات
    permissions = Permission.query.order_by(Permission.module, Permission.action).all()
    
    # جلب صلاحيات المستخدم الحالية
    user_permissions = UserPermission.query.filter_by(user_id=user_id, granted=True).all()
    user_permission_ids = [up.permission_id for up in user_permissions]
    
    return render_template('user_permissions.html', 
                         user=user, 
                         permissions=permissions, 
                         user_permission_ids=user_permission_ids)

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
@require_permission('invoices', 'view')
def invoices():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # فلترة حسب التاريخ والحالة
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    status_filter = request.args.get('status', '')
    
    query = Order.query
    
    if date_filter:
        query = query.filter_by(day=date_filter)
    
    # فلترة الفواتير الخاطئة
    query = query.filter(
        (Order.unit_price <= 100000) &  # سعر منطقي
        (Order.phone != '') &  # هاتف غير فارغ
        (Order.phone.isnot(None)) &  # هاتف غير فارغ
        (Order.customer_name != '') &  # اسم عميل غير فارغ
        (Order.customer_name.isnot(None))  # اسم عميل غير فارغ
    )
    
    # فلترة الطلبات - إخفاء الطلبات بحالة "خارج للشحن"
    query = query.filter(Order.order_status != 'خارج للشحن')
    
    invoices = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # تم إلغاء نظام الحالات
    
    return render_template('invoices.html', 
                         invoices=invoices, 
                         date_filter=date_filter)

@app.route('/invoices/add', methods=['GET', 'POST'])
@login_required
@require_permission('invoices', 'add')
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
                order_id=generate_order_id(),
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
            
            # إضافة العمولة للموظف
            try:
                employee = Employee.query.filter_by(name=request.form['employee_name']).first()
                if employee:
                    commission_rate = COMMISSION_RATES.get(product_code, 500)
                    commission_amount = commission_rate * int(request.form['quantity'])
                    employee.commission_per_order += commission_amount
                    db.session.commit()
                    print(f"✅ تم إضافة العمولة للموظف {employee.name}: {commission_amount} دينار")
            except Exception as e:
                print(f"❌ خطأ في إضافة العمولة: {e}")
            
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
@require_permission('employees', 'view')
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
@require_permission('employees', 'add')
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
@require_permission('products', 'view')
def products():
    products = Product.query.all()
    
    # حساب الإحصائيات المطلوبة
    total_stock = sum(product.stock for product in products)
    total_returns = 0  # Product model doesn't have returns field
    low_stock_products = [p for p in products if p.stock <= 10]
    total_inventory_value = sum(product.price * product.stock for product in products)
    
    return render_template('products.html', 
                         products=products,
                         total_stock=total_stock,
                         total_returns=total_returns,
                         low_stock_products=low_stock_products,
                         total_inventory_value=total_inventory_value)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
@require_permission('products', 'add')
def add_product():
    if request.method == 'POST':
        try:
            # إنشاء كود فريد للمنتج
            import uuid
            product_code = f"PROD_{uuid.uuid4().hex[:8].upper()}"
            
            product = Product(
                code=product_code,
                name=request.form['name'],
                description=request.form.get('description', ''),
                price=float(request.form['price']),
                stock=int(request.form['stock']),
                category=request.form.get('category', 'عام'),
                cost=float(request.form.get('cost', 0)),
                returns=int(request.form.get('returns', 0)),
                weight=float(request.form.get('weight', 0)),
                dimensions=request.form.get('dimensions', ''),
                warranty_months=int(request.form.get('warranty_months', 12))
            )
            db.session.add(product)
            db.session.commit()
            flash('تم إضافة المنتج بنجاح', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إضافة المنتج: {str(e)}', 'error')
    
    return render_template('add_product.html')

# مسارات العملاء
@app.route('/customers')
@login_required
@require_permission('customers', 'view')
def customers():
    # عرض الطلبات بحالة "خارج للشحن" بدلاً من العملاء
    orders = Order.query.filter_by(order_status='خارج للشحن').filter(
        (Order.unit_price <= 100000) &  # سعر منطقي
        (Order.phone != '') &  # هاتف غير فارغ
        (Order.phone.isnot(None)) &  # هاتف غير فارغ
        (Order.customer_name != '') &  # اسم عميل غير فارغ
        (Order.customer_name.isnot(None))  # اسم عميل غير فارغ
    ).order_by(Order.created_at.desc()).all()
    
    return render_template('customers.html', orders=orders, customers=[])

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
@require_permission('customers', 'add')
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
@require_permission('reports', 'view')
def reports():
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('reports.html', today=today)

@app.route('/export/shipping/<date>')
@login_required
@require_permission('invoices', 'export')
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
@require_permission('invoices', 'delete')
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

@app.route('/return_order/<int:order_id>', methods=['POST'])
@login_required
@require_permission('invoices', 'edit')
def return_order(order_id):
    """إرجاع طلب - خصم العمولة من الموظف وتغيير الحالة وزيادة المخزون"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # التحقق من أن الطلب قابل للإرجاع
        if order.order_status == 'تم الإلغاء':
            flash('هذا الطلب تم إلغاؤه مسبقاً', 'error')
            return redirect(url_for('invoices'))
        
        if order.order_status == 'تم الإرجاع':
            flash('هذا الطلب تم إرجاعه مسبقاً', 'error')
            return redirect(url_for('invoices'))
        
        # حساب العمولة المطلوب خصمها
        commission_rate = COMMISSION_RATES.get(order.product_code, 500)  # افتراضي 500 دينار
        total_commission = commission_rate * order.quantity
        
        # خصم العمولة من الموظف
        employee = Employee.query.filter_by(name=order.employee_name).first()
        if employee:
            # خصم العمولة المضافة مسبقاً (حتى لو لم تكن مدفوعة)
            employee.commission_per_order -= total_commission
            order.commission_paid = False
            flash(f'تم خصم العمولة من الموظف: {total_commission} دينار', 'info')
        
        # تغيير حالة الطلب إلى "تم الإرجاع"
        order.order_status = 'تم الإرجاع'
        order.payment_status = 'مرتجع'
        
        # زيادة المخزون
        product = Product.query.filter_by(code=order.product_code).first()
        if product:
            product.stock += order.quantity
            flash(f'تم إضافة {order.quantity} قطعة إلى مخزون {product.name}', 'success')
        else:
            # إنشاء منتج جديد إذا لم يكن موجوداً
            new_product = Product(
                code=order.product_code,
                name=order.product_name,
                price=order.unit_price,
                stock=order.quantity,
                category='ماكينة حلاقة' if 'sales' in order.product_code else 'ملحقات'
            )
            db.session.add(new_product)
            flash(f'تم إنشاء منتج جديد {order.product_name} مع {order.quantity} قطعة في المخزون', 'success')
        
        # حفظ التغييرات
        db.session.commit()
        
        flash(f'✅ تم إرجاع الطلب بنجاح! رقم الطلب: {order.id}', 'success')
        flash(f'💰 تم خصم العمولة: {total_commission} دينار', 'info')
        flash(f'📦 تم إضافة {order.quantity} قطعة إلى المخزون', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ في إرجاع الطلب: {str(e)}', 'error')
        print(f"❌ خطأ في إرجاع الطلب: {e}")
    
    return redirect(url_for('invoices'))

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
@require_permission('invoices', 'edit')
def cancel_order(order_id):
    """إلغاء طلب - خصم العمولة من الموظف وتغيير الحالة"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # التحقق من أن الطلب قابل للإلغاء
        if order.order_status == 'تم الإلغاء':
            flash('هذا الطلب تم إلغاؤه مسبقاً', 'error')
            return redirect(url_for('invoices'))
        
        if order.order_status == 'تم الإرجاع':
            flash('هذا الطلب تم إرجاعه مسبقاً', 'error')
            return redirect(url_for('invoices'))
        
        # حساب العمولة المطلوب خصمها
        commission_rate = COMMISSION_RATES.get(order.product_code, 500)  # افتراضي 500 دينار
        total_commission = commission_rate * order.quantity
        
        # خصم العمولة من الموظف
        employee = Employee.query.filter_by(name=order.employee_name).first()
        if employee:
            # خصم العمولة المضافة مسبقاً (حتى لو لم تكن مدفوعة)
            employee.commission_per_order -= total_commission
            order.commission_paid = False
            flash(f'تم خصم العمولة من الموظف: {total_commission} دينار', 'info')
        
        # تغيير حالة الطلب إلى "تم الإلغاء"
        order.order_status = 'تم الإلغاء'
        order.payment_status = 'ملغي'
        
        # حفظ التغييرات
        db.session.commit()
        
        flash(f'❌ تم إلغاء الطلب بنجاح! رقم الطلب: {order.id}', 'success')
        flash(f'💰 تم خصم العمولة: {total_commission} دينار', 'info')
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ في إلغاء الطلب: {str(e)}', 'error')
        print(f"❌ خطأ في إلغاء الطلب: {e}")
    
    return redirect(url_for('invoices'))

@app.route('/pay_commission/<int:order_id>', methods=['POST'])
@login_required
@require_permission('invoices', 'edit')
def pay_commission(order_id):
    """دفع العمولة للموظف على طلب معين"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # التحقق من أن الطلب مؤهل للعمولة
        if order.commission_paid:
            flash('تم دفع العمولة لهذا الطلب مسبقاً', 'warning')
            return redirect(url_for('invoices'))
        
        if order.order_status in ['تم الإلغاء', 'تم الإرجاع']:
            flash('لا يمكن دفع العمولة للطلبات الملغاة أو المرتجعة', 'error')
            return redirect(url_for('invoices'))
        
        # حساب العمولة
        commission_rate = COMMISSION_RATES.get(order.product_code, 500)  # افتراضي 500 دينار
        total_commission = commission_rate * order.quantity
        
        # إضافة العمولة للموظف
        employee = Employee.query.filter_by(name=order.employee_name).first()
        if employee:
            employee.commission_per_order += total_commission
            order.commission_paid = True
            
            # حفظ التغييرات
            db.session.commit()
            
            flash(f'✅ تم دفع العمولة بنجاح! المبلغ: {total_commission} دينار', 'success')
            flash(f'👤 الموظف: {employee.name}', 'info')
        else:
            flash('لم يتم العثور على الموظف', 'error')
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ في دفع العمولة: {str(e)}', 'error')
        print(f"❌ خطأ في دفع العمولة: {e}")
    
    return redirect(url_for('invoices'))

@app.route('/pay_all_commissions/<employee_name>', methods=['POST'])
@login_required
def pay_all_commissions(employee_name):
    """دفع جميع العمولات المستحقة لموظف معين"""
    try:
        # البحث عن الطلبات المؤهلة للعمولة
        eligible_orders = Order.query.filter_by(
            employee_name=employee_name,
            commission_paid=False
        ).filter(
            Order.order_status.notin_(['تم الإلغاء', 'تم الإرجاع'])
        ).all()
        
        if not eligible_orders:
            flash(f'لا توجد عمولات مستحقة للموظف {employee_name}', 'warning')
            return redirect(url_for('employees'))
        
        # حساب إجمالي العمولة
        total_commission = 0
        for order in eligible_orders:
            commission_rate = COMMISSION_RATES.get(order.product_code, 500)
            order_commission = commission_rate * order.quantity
            total_commission += order_commission
            order.commission_paid = True
        
        # إضافة العمولة للموظف
        employee = Employee.query.filter_by(name=employee_name).first()
        if employee:
            employee.commission_per_order += total_commission
            db.session.commit()
            
            flash(f'✅ تم دفع جميع العمولات بنجاح!', 'success')
            flash(f'👤 الموظف: {employee_name}', 'info')
            flash(f'💰 إجمالي العمولة: {total_commission} دينار', 'info')
            flash(f'📋 عدد الطلبات: {len(eligible_orders)}', 'info')
        else:
            flash('لم يتم العثور على الموظف', 'error')
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ في دفع العمولات: {str(e)}', 'error')
        print(f"❌ خطأ في دفع العمولات: {e}")
    
    return redirect(url_for('employees'))

@app.route('/calculate_commissions/<employee_name>')
@login_required
def calculate_commissions(employee_name):
    """حساب العمولات المستحقة لموظف معين"""
    try:
        # البحث عن الطلبات المؤهلة للعمولة
        eligible_orders = Order.query.filter_by(
            employee_name=employee_name,
            commission_paid=False
        ).filter(
            Order.order_status.notin_(['تم الإلغاء', 'تم الإرجاع'])
        ).all()
        
        # حساب إجمالي العمولة
        total_commission = 0
        commission_details = []
        
        for order in eligible_orders:
            commission_rate = COMMISSION_RATES.get(order.product_code, 500)
            order_commission = commission_rate * order.quantity
            total_commission += order_commission
            
            commission_details.append({
                'order_id': order.id,
                'customer_name': order.customer_name,
                'product_name': order.product_name,
                'quantity': order.quantity,
                'commission_rate': commission_rate,
                'order_commission': order_commission,
                'date': order.created_at.strftime('%Y-%m-%d')
            })
        
        return jsonify({
            'success': True,
            'employee_name': employee_name,
            'total_commission': total_commission,
            'orders_count': len(eligible_orders),
            'commission_details': commission_details
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/export_orders_custom')
@login_required
@require_permission('invoices', 'export')
def export_orders_custom():
    """تصدير الطلبات مع تحديد التاريخ والصيغة"""
    try:
        date = request.args.get('date')
        format_type = request.args.get('format', 'xls')
        
        if not date:
            flash('الرجاء تحديد التاريخ', 'error')
            return redirect(url_for('invoices'))
        
        # البحث عن الطلبات حسب التاريخ
        orders = Order.query.filter_by(day=date).filter(
            (Order.unit_price <= 100000) &  # سعر منطقي
            (Order.phone != '') &  # هاتف غير فارغ
            (Order.phone.isnot(None)) &  # هاتف غير فارغ
            (Order.customer_name != '') &  # اسم عميل غير فارغ
            (Order.customer_name.isnot(None))  # اسم عميل غير فارغ
        ).filter(Order.order_status != 'خارج للشحن').all()
        
        if not orders:
            flash(f'لا توجد طلبات صحيحة لليوم {date}. تأكد من أن التاريخ صحيح وأن هناك طلبات مسجلة لهذا اليوم.', 'warning')
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

@app.route('/transfer_orders_to_customers')
@login_required
def transfer_orders_to_customers():
    """نقل الطلبات المصدرة إلى صفحة العملاء بحالة 'خارج للشحن'"""
    try:
        date = request.args.get('date')
        
        if not date:
            flash('الرجاء تحديد التاريخ', 'error')
            return redirect(url_for('invoices'))
        
        # البحث عن الطلبات حسب التاريخ
        orders = Order.query.filter_by(day=date).filter(
            (Order.unit_price <= 100000) &  # سعر منطقي
            (Order.phone != '') &  # هاتف غير فارغ
            (Order.phone.isnot(None)) &  # هاتف غير فارغ
            (Order.customer_name != '') &  # اسم عميل غير فارغ
            (Order.customer_name.isnot(None))  # اسم عميل غير فارغ
        ).all()
        
        if not orders:
            flash(f'لا توجد طلبات صحيحة لليوم {date} للنقل.', 'warning')
            return redirect(url_for('invoices'))
        
        # تحديث حالة الطلبات إلى 'خارج للشحن'
        updated_count = 0
        for order in orders:
            if hasattr(order, 'order_status'):
                order.order_status = 'خارج للشحن'
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            flash(f'✅ تم نقل {updated_count} طلب بنجاح إلى حالة "خارج للشحن" لليوم {date}', 'success')
        else:
            flash(f'⚠️ لا توجد طلبات قابلة للتحديث لليوم {date}', 'warning')
        
        # إعادة توجيه إلى صفحة العملاء
        return redirect(url_for('customers'))
        
    except Exception as e:
        flash(f'❌ خطأ في نقل الطلبات: {str(e)}', 'error')
        return redirect(url_for('invoices'))

@app.route('/export/orders/<date>')
@login_required
@require_permission('invoices', 'export')
def export_orders_from_page(date):
    """تصدير الطلبات مباشرة من صفحة الطلبات"""
    try:
        if date == 'today':
            date = datetime.now().strftime('%Y-%m-%d')
        
        # البحث عن الطلبات حسب التاريخ
        orders = Order.query.filter_by(day=date).filter(
            (Order.unit_price <= 100000) &  # سعر منطقي
            (Order.phone != '') &  # هاتف غير فارغ
            (Order.phone.isnot(None)) &  # هاتف غير فارغ
            (Order.customer_name != '') &  # اسم عميل غير فارغ
            (Order.customer_name.isnot(None))  # اسم عميل غير فارغ
        ).all()
        
        if not orders:
            flash(f'لا توجد طلبات صحيحة لليوم {date}', 'warning')
            return redirect(url_for('invoices'))
        
        # تصدير البيانات
        return export_shipping_helper(date)
        
    except Exception as e:
        flash(f'خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('invoices'))

@app.route('/export/hrm/<date>')
@login_required
@require_permission('employees', 'export')
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
@require_permission('reports', 'export')
def export_performance_report(date):
    """تصدير تقرير أداء شامل لليوم المحدد"""
    try:
        # جلب بيانات الأداء
        performance_data = get_employee_performance(date)
        
        if not performance_data:
            flash(f'لا توجد بيانات أداء لليوم {date}', 'warning')
            return redirect(url_for('reports'))
        
        # جلب إحصائيات الطلبات
        orders = Order.query.filter_by(day=date).filter(
            (Order.unit_price <= 100000) &  # سعر منطقي
            (Order.phone != '') &  # هاتف غير فارغ
            (Order.phone.isnot(None)) &  # هاتف غير فارغ
            (Order.customer_name != '') &  # اسم عميل غير فارغ
            (Order.customer_name.isnot(None))  # اسم عميل غير فارغ
        ).all()
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
                    conn.execute(text("ALTER TABLE employee ADD COLUMN commission_per_order DECIMAL(10,2) DEFAULT 500"))
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
        
        # تهيئة الصلاحيات
        init_permissions()
        
        # إنشاء سوبر أدمن
        create_super_admin()
        
        print("✅ تم تهيئة قاعدة البيانات بنجاح")

# دوال مساعدة
def clean_invalid_orders():
    """تنظيف الفواتير الخاطئة من قاعدة البيانات"""
    try:
        with app.app_context():
            # البحث عن الفواتير الخاطئة
            invalid_orders = Order.query.filter(
                (Order.unit_price > 100000) |  # سعر غير منطقي
                (Order.phone == '') |  # هاتف فارغ
                (Order.phone.is_(None)) |  # هاتف فارغ
                (Order.customer_name == '') |  # اسم عميل فارغ
                (Order.customer_name.is_(None))  # اسم عميل فارغ
            ).all()
            
            if invalid_orders:
                print(f"🧹 تم العثور على {len(invalid_orders)} فاتورة خاطئة")
                
                for order in invalid_orders:
                    print(f"❌ فاتورة خاطئة: ID={order.id}, السعر={order.unit_price}, الهاتف='{order.phone}'")
                    db.session.delete(order)
                
                db.session.commit()
                print(f"✅ تم حذف {len(invalid_orders)} فاتورة خاطئة")
                return len(invalid_orders)
            else:
                print("✅ لا توجد فواتير خاطئة")
                return 0
                
    except Exception as e:
        print(f"❌ خطأ في تنظيف الفواتير: {e}")
        return 0

def normalize_arabic_name(name):
    """تطبيع الأسماء العربية - إزالة التشكيل والتباينات في الكتابة"""
    # إزالة التشكيل
    name = name.replace('َ', '').replace('ُ', '').replace('ِ', '').replace('ْ', '').replace('ّ', '')
    
    # تطبيع الحروف المتشابهة
    name = name.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    name = name.replace('ة', 'ه')
    name = name.replace('ى', 'ي')
    
    # إزالة المسافات الزائدة
    name = ' '.join(name.split())
    
    return name.strip()

def find_employee_by_name(input_name):
    """البحث عن الموظف بالاسم مع دعم صيغ الكتابة المختلفة"""
    if not input_name:
            return None
        
    # تطبيع الاسم المدخل
    normalized_input = normalize_arabic_name(input_name)
    
    # البحث في قاعدة البيانات
    # البحث المباشر أولاً
    employee = Employee.query.filter_by(name=input_name).first()
    if employee:
        return employee
    
    # البحث بالاسم المطبيع
    for emp in Employee.query.all():
        normalized_emp_name = normalize_arabic_name(emp.name)
        if normalized_input == normalized_emp_name:
            return emp
    
    # البحث الجزئي
    for emp in Employee.query.all():
        normalized_emp_name = normalize_arabic_name(emp.name)
        if (normalized_input in normalized_emp_name or 
            normalized_emp_name in normalized_input):
            return emp
    
    # البحث المتقدم - دعم "مريانا" و "ميريانا"
    if normalized_input in ['مريانا', 'ميريانا']:
        for emp in Employee.query.all():
            if 'ميريانا' in emp.name:
                return emp
    
    return None

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
            commission_rate = COMMISSION_RATES.get(order.product_code, 500)
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
                
                commission_rate = COMMISSION_RATES.get(product_type, 500)
                commission = commission_rate * order.quantity
                employee_stats[employee_name]['total_commission'] += commission
                
                print(f"💰 إضافة عمولة لـ {employee_name}: {commission} دينار (المنتج: {product_type}, الكمية: {order.quantity})")
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
                            
                            print(f"💰 حذف عمولة: {commission_lost} دينار من {employee.name}")
                        
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

@app.route('/pay_employee_commission/<int:employee_id>', methods=['POST'])
@login_required
def pay_employee_commission(employee_id):
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
    # إنشاء تطبيق البوت الجديد
    print("🚀 إنشاء البوت الجديد...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    # تهيئة قاعدة البيانات
    print("🗄️ تهيئة قاعدة البيانات...")
    init_db()
    
    # تنظيف الفواتير الخاطئة
    print("🧹 تنظيف الفواتير الخاطئة...")
    cleaned_count = clean_invalid_orders()
    if cleaned_count > 0:
        print(f"✅ تم تنظيف {cleaned_count} فاتورة خاطئة")
    
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
• تأكد من صحة رقم الهاتف

👥 **النظام يدعم صيغ الكتابة المختلفة للأسماء:**
• "إيمان" أو "أيمان" أو "ايمان"
• "ميريانا" أو "مريانا"
• "نور" أو "صبا" أو "عيسى" أو "لافا" أو "نغم" """
        
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
                            order = Order.query.filter_by(phone=phone).filter(
                                Order.order_status.notin_(['تم الإلغاء', 'تم الإرجاع'])
                            ).first()
                            
                            if order:
                                # تحديث حالة الطلب إلى مرتجع
                                order.order_status = 'مرتجع'
                                order.notes = f"مرتجع: {reason}"
                                
                                # حذف العمولة من الموظف
                                try:
                                    employee = Employee.query.filter_by(name=order.employee_name).first()
                                    if employee:
                                        commission_rate = COMMISSION_RATES.get(order.product_code, 500)
                                        commission_amount = commission_rate * order.quantity
                                        employee.commission_per_order -= commission_amount
                                        print(f"✅ تم خصم العمولة من الموظف {employee.name}: {commission_amount} دينار")
                                except Exception as e:
                                    print(f"❌ خطأ في خصم العمولة: {e}")
                                
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
                                # البحث عن جميع الطلبات بهذا الرقم للتشخيص
                                with app.app_context():
                                    all_orders = Order.query.filter_by(phone=phone).all()
                                    if all_orders:
                                        statuses = [order.order_status for order in all_orders]
                                        error_message = f"""❌ لم يتم العثور على طلب قابل للإرجاع بهذا الرقم: {phone}

📋 الطلبات الموجودة:
{chr(10).join([f'• الطلب {order.id}: {order.order_status}' for order in all_orders])}

💡 يمكن إرجاع الطلبات بحالات: قيد المراجعة، تم التأكيد، خارج للشحن، تم التوصيل
❌ لا يمكن إرجاع الطلبات بحالات: تم الإلغاء، تم الإرجاع"""
                                    else:
                                        error_message = f"❌ لم يتم العثور على أي طلب بهذا الرقم: {phone}"
                                
                                await context.bot.send_message(chat_id=chat_id, text=error_message)
                                print(f"❌ لم يتم العثور على طلب قابل للإرجاع للهاتف: {phone}")
                    else:
                        error_message = "❌ تنسيق خاطئ. استخدم: ارجاع/رقم_الهاتف/السبب"
                        await context.bot.send_message(chat_id=chat_id, text=error_message)
                        
                except Exception as e:
                    error_message = f"❌ خطأ في معالجة المرتجع: {str(e)}"
                    print(f"❌ خطأ في معالجة المرتجع: {e}")
                    print(f"🔍 نوع الخطأ: {type(e).__name__}")
                    print(f"🔍 تفاصيل الخطأ: {str(e)}")
                    
                    # إرسال رسالة خطأ للمستخدم
                    try:
                        await context.bot.send_message(chat_id=chat_id, text=error_message)
                    except Exception as send_error:
                        print(f"❌ خطأ في إرسال رسالة الخطأ: {send_error}")
                    
            elif text.isdigit() and len(text) >= 10:
                # معالجة المرتجعات برقم الهاتف فقط
                try:
                    phone = text.strip()
                    print(f"🔄 معالجة مرتجع برقم الهاتف فقط: {phone}")
                    
                    # البحث عن الطلب برقم الهاتف
                    with app.app_context():
                        order = Order.query.filter_by(phone=phone).filter(
                            Order.order_status.notin_(['تم الإلغاء', 'تم الإرجاع'])
                        ).first()
                        
                        if order:
                            # تحديث حالة الطلب إلى مرتجع
                            order.order_status = 'مرتجع'
                            order.notes = f"مرتجع: تم الإرجاع برقم الهاتف {phone}"
                            
                            # حذف العمولة من الموظف
                            try:
                                employee = Employee.query.filter_by(name=order.employee_name).first()
                                if employee:
                                    commission_rate = COMMISSION_RATES.get(order.product_code, 500)
                                    commission_amount = commission_rate * order.quantity
                                    employee.commission_per_order -= commission_amount
                                    print(f"✅ تم خصم العمولة من الموظف {employee.name}: {commission_amount} دينار")
                            except Exception as e:
                                print(f"❌ خطأ في خصم العمولة: {e}")
                            
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
                            # البحث عن جميع الطلبات بهذا الرقم للتشخيص
                            with app.app_context():
                                all_orders = Order.query.filter_by(phone=phone).all()
                                if all_orders:
                                    statuses = [order.order_status for order in all_orders]
                                    error_message = f"""❌ لم يتم العثور على طلب قابل للإرجاع بهذا الرقم: {phone}

📋 الطلبات الموجودة:
{chr(10).join([f'• الطلب {order.id}: {order.order_status}' for order in all_orders])}

💡 يمكن إرجاع الطلبات بحالات: قيد المراجعة، تم التأكيد، خارج للشحن، تم التوصيل
❌ لا يمكن إرجاع الطلبات بحالات: تم الإلغاء، تم الإرجاع"""
                                else:
                                    error_message = f"❌ لم يتم العثور على أي طلب بهذا الرقم: {phone}"
                            
                            await context.bot.send_message(chat_id=chat_id, text=error_message)
                            print(f"❌ لم يتم العثور على طلب قابل للإرجاع للهاتف: {phone}")
                    
                except Exception as e:
                    error_message = f"❌ خطأ في معالجة المرتجع: {str(e)}"
                    print(f"❌ خطأ في معالجة المرتجع: {e}")
                    print(f"🔍 نوع الخطأ: {type(e).__name__}")
                    print(f"🔍 تفاصيل الخطأ: {str(e)}")
                    
                    # إرسال رسالة خطأ للمستخدم
                    try:
                        await context.bot.send_message(chat_id=chat_id, text=error_message)
                    except Exception as send_error:
                        print(f"❌ خطأ في إرسال رسالة الخطأ: {send_error}")
                    
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
                        
                        # معالجة الكمية - إزالة المسافات الزائدة
                        quantity_str = lines[5].split('/')[1].strip() if '/' in lines[5] else '1'
                        quantity = int(quantity_str) if quantity_str.isdigit() else 1
                        
                        # معالجة السعر - إزالة المسافات الزائدة
                        price_str = lines[6].split('/')[1].strip() if '/' in lines[6] else '40000'
                        unit_price = int(price_str) if price_str.isdigit() else 40000
                        
                        # معالجة الملاحظات
                        notes = lines[7].split('/')[1].strip() if len(lines) > 7 and '/' in lines[7] else ''
                        
                        # التحقق من صحة البيانات
                        if not phone or phone == '':
                            error_message = """❌ **رقم الهاتف مطلوب!**

📱 تأكد من إدخال رقم الهاتف بشكل صحيح
💡 مثال: الرقم/07812345678"""
                            await context.bot.send_message(chat_id=chat_id, text=error_message)
                            return
                        
                        if unit_price <= 0 or unit_price > 100000:
                            error_message = """❌ **السعر غير صحيح!**

💰 الأسعار المتاحة:
• sales V1: 40,000 دينار
• sales V2: 45,000 دينار
• رأس الماكينة: 15,000 دينار
• كابل الشحن: 10,000 دينار"""
                            await context.bot.send_message(chat_id=chat_id, text=error_message)
                            return
                        
                        print(f"🔍 اسم الموظف المُدخل: '{employee_name}'")
                        
                        # البحث عن الموظف باستخدام النظام الذكي
                        with app.app_context():
                            employee = find_employee_by_name(employee_name)
                            if not employee:
                                # قائمة الموظفين المتاحين
                                available_employees = [emp.name for emp in Employee.query.all()]
                                error_message = f"""❌ اسم الموظف غير صحيح!

🔍 الاسم المُدخل: {employee_name}

✅ **الأسماء الصحيحة:**
{chr(10).join([f"• {name}" for name in available_employees])}

💡 **نصائح للكتابة:**
• يمكن كتابة "إيمان" أو "أيمان" أو "ايمان"
• يمكن كتابة "ميريانا" أو "مريانا"
• تأكد من صحة الاسم من القائمة أعلاه"""
                                
                                await context.bot.send_message(chat_id=chat_id, text=error_message)
                                return
                            
                            # استخدام اسم الموظف الصحيح من قاعدة البيانات
                            employee_name = employee.name
                        
                        # التحقق من عدم تكرار الفاتورة
                        with app.app_context():
                            # التحقق من تكرار الفاتورة بناءً على رقم الهاتف والعميل
                            existing_order = Order.query.filter_by(
                                phone=phone,
                                customer_name=customer_name,
                                day=datetime.now().strftime('%Y-%m-%d')
                            ).first()
                            
                            if existing_order:
                                error_message = f"""⚠️ **فاتورة مكررة!**

📱 الهاتف: {phone}
👤 العميل: {customer_name}
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d')}

❌ **هذه الفاتورة موجودة مسبقاً في النظام**
💡 **لا يمكن إضافة نفس الفاتورة مرتين في نفس اليوم**"""
                                
                                await context.bot.send_message(chat_id=chat_id, text=error_message)
                                return
                            
                            # التحقق من تكرار الفاتورة بناءً على رقم الهاتف فقط (للمزيد من الأمان)
                            existing_phone_order = Order.query.filter_by(
                                phone=phone,
                                day=datetime.now().strftime('%Y-%m-%d')
                            ).first()
                            
                            if existing_phone_order:
                                error_message = f"""⚠️ **فاتورة مكررة!**

📱 الهاتف: {phone}
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d')}

❌ **هذا الرقم موجود مسبقاً في النظام اليوم**
💡 **لا يمكن إضافة فاتورة لنفس الرقم مرتين في نفس اليوم**"""
                                
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
                            
                            # إضافة العمولة للموظف
                            try:
                                employee = Employee.query.filter_by(name=employee_name).first()
                                if employee:
                                    commission_rate = COMMISSION_RATES.get(product_code, 500)
                                    commission_amount = commission_rate * quantity
                                    employee.commission_per_order += commission_amount
                                    db.session.commit()
                                    print(f"✅ تم إضافة العمولة للموظف {employee.name}: {commission_amount} دينار")
                            except Exception as e:
                                print(f"❌ خطأ في إضافة العمولة: {e}")
                        
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
                    print(f"❌ خطأ في معالجة الفاتورة: {e}")
                    print(f"🔍 نوع الخطأ: {type(e).__name__}")
                    print(f"🔍 تفاصيل الخطأ: {str(e)}")
                    
                    # إرسال رسالة خطأ للمستخدم
                    try:
                        await context.bot.send_message(chat_id=chat_id, text=error_message)
                    except Exception as send_error:
                        print(f"❌ خطأ في إرسال رسالة الخطأ: {send_error}")
                        
        except Exception as e:
            error_message = f"❌ خطأ في معالجة الرسالة: {str(e)}"
            print(f"❌ خطأ في معالجة الرسالة: {e}")
            print(f"🔍 نوع الخطأ: {type(e).__name__}")
            print(f"🔍 تفاصيل الخطأ: {str(e)}")
            
            # إرسال رسالة خطأ للمستخدم
            try:
                await context.bot.send_message(chat_id=chat_id, text=error_message)
            except Exception as send_error:
                print(f"❌ خطأ في إرسال رسالة الخطأ: {send_error}")
    
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
السعر/40000
الملاحظات/توصيل سريع

👥 **الموظفون المتاحون:**
• نور، صبا، ميريانا، عيسى، إيمان، لافا، نغم
• **النظام يدعم صيغ الكتابة المختلفة:**
  - "إيمان" أو "أيمان" أو "ايمان"
  - "ميريانا" أو "مريانا"

⚠️ **منع التكرار:**
• لا يمكن إضافة نفس الفاتورة مرتين في نفس اليوم """
            
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
• بدون رسوم توصيل

👥 **الموظفون المتاحون:**
• نور، صبا، ميريانا، عيسى، إيمان، لافا، نغم
• **النظام يدعم صيغ الكتابة المختلفة**"""
            
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
• **النظام يدعم صيغ الكتابة المختلفة للأسماء:**
  - "إيمان" أو "أيمان" أو "ايمان"
  - "ميريانا" أو "مريانا"
  - "نور" أو "صبا" أو "عيسى" أو "لافا" أو "نغم"

⚠️ **منع التكرار:**
• لا يمكن إضافة نفس الفاتورة مرتين في نفس اليوم
• النظام يتحقق من رقم الهاتف والعميل لمنع التكرار """
            
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
    app.run(debug=True, host='0.0.0.0', port=8080)
