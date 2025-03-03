from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Cần thiết cho session và flash messages
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Chỉ định route login

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Thêm sau khai báo login_manager
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bạn không có quyền truy cập trang này.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Check for registration success and display message
    if session.pop('registration_success', False):
        flash('Tài khoản đã được tạo! Bạn có thể đăng nhập ngay bây giờ.', 'success')
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            # Kiểm tra xem tài khoản có bị khóa không
            if user.is_blocked:
                flash('Tài khoản của bạn đã bị khóa.', 'danger')
                return render_template('login.html')
                
            login_user(user)
            next_page = request.args.get('next')
            flash('Đăng nhập thành công!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Đăng nhập thất bại. Kiểm tra lại email và mật khẩu.', 'danger')
    
    return render_template('login.html')

@app.route('/login_as_admin')
def login_as_admin():
    # Kiểm tra tài khoản admin mặc định
    admin = User.query.filter_by(email='admin@example.com').first()
    if admin:
        # Kiểm tra nếu tài khoản admin bị khóa
        if admin.is_blocked:
            flash('Tài khoản admin đã bị khóa.', 'danger')
            return redirect(url_for('login'))
        
        # Đăng nhập với tài khoản admin
        login_user(admin)
        flash('Đăng nhập với tài khoản admin thành công!', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Không tìm thấy tài khoản admin mặc định.', 'danger')
        return redirect(url_for('login'))

# XÓA PHIÊN BẢN CŨ CỦA ROUTE INDEX Ở ĐÂY

@app.route('/')
@app.route('/page/<int:page>')
def index(page=1):
    per_page = 10
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

@app.route('/create', methods=['GET', 'POST'])
@login_required  # Yêu cầu đăng nhập để đăng bài
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = Post(title=title, content=content, author=current_user)
        db.session.add(new_post)
        db.session.commit()
        flash('Bài viết đã được tạo!', 'success')
        return redirect(url_for('index'))
    return render_template('create_post.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Kiểm tra user/email đã tồn tại chưa
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        
        if user_exists:
            flash('Tên đăng nhập đã tồn tại!', 'danger')
        elif email_exists:
            flash('Email đã được sử dụng!', 'danger')
        else:
            # Tạo user mới
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            
            # Use session instead of flash to avoid duplicate messages
            session['registration_success'] = True
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất!', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/block_user/<int:user_id>')
@login_required
@admin_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('Bạn không thể khóa tài khoản của chính mình.', 'danger')
    else:
        user.is_blocked = True
        db.session.commit()
        flash(f'Tài khoản {user.username} đã bị khóa.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/unblock_user/<int:user_id>')
@login_required
@admin_required
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blocked = False
    db.session.commit()
    flash(f'Tài khoản {user.username} đã được mở khóa.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reset_password/<int:user_id>')
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    # Tạo mật khẩu ngẫu nhiên
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    # Hash mật khẩu mới
    hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
    user.password = hashed_password
    db.session.commit()
    flash(f'Mật khẩu cho {user.username} đã được đặt lại thành: {new_password}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/manage_posts')
@login_required
def manage_posts():
    # Lấy tất cả bài viết của người dùng hiện tại
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.date_posted.desc()).all()
    return render_template('manage_posts.html', posts=posts, title='Quản lý bài viết')

@app.route('/delete_posts', methods=['POST'])
@login_required
def delete_posts():
    # Lấy danh sách ID bài viết đã chọn từ form
    post_ids = request.form.getlist('post_ids')
    
    if not post_ids:
        flash('Không có bài viết nào được chọn để xóa.', 'warning')
        return redirect(url_for('manage_posts'))
    
    # Đếm số bài viết đã xóa
    deleted_count = 0
    
    # Xóa từng bài viết đã chọn (chỉ của người dùng hiện tại)
    for post_id in post_ids:
        post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
        if post:
            db.session.delete(post)
            deleted_count += 1
    
    db.session.commit()
    flash(f'Đã xóa {deleted_count} bài viết thành công.', 'success')
    return redirect(url_for('manage_posts'))

# ...existing code stays the same...

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Tạo tài khoản admin nếu chưa có
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin = User(username='admin', email='admin@example.com', 
                         password=hashed_password, is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print('Tài khoản admin đã được tạo!')
    
    # Change this line to bind to all network interfaces
    app.run(host='0.0.0.0', debug=True)