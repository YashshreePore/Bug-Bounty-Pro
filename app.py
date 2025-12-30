from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required
from sqlalchemy import Numeric, func, DateTime
import os
from datetime import datetime, timedelta # 🔴 FIX: timedelta येथे असणे आवश्यक 🔴
import re
from flask import jsonify # 🔴 हे app.py च्या वरती imports मध्ये जोडा 🔴
import pytz # 🔴 FIX: Timezone conversion साठी 'pytz' जोडला 🔴
from functools import wraps # admin side banvtana jodle 
from sqlalchemy.orm import joinedload # 🔴 हे app.py च्या वरती imports mdhe (databse admin la fetch karnyasthi ) 🔴

# ॲप्लिकेशन तयार करणे
app = Flask(__name__)
# 🔴 तुमची गुप्त की 🔴
app.config['SECRET_KEY'] = 'your_strong_and_secret_key_for_bugbounty_pro' 

# -----------------
# 🔴 SQLite डाटाबेस कॉन्फिगरेशन 🔴
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bugbounty_pro.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -----------------
# 🔴 FIX: JINJA FILTER तयार करणे (वेळ स्थानिक करण्यासाठी) 🔴
# app.py मध्ये, convert_to_ist फंक्शन बदला.

@app.template_filter()
def convert_to_ist(utc_dt):
    """UTC datetime ला भारतीय प्रमाणवेळेत (IST) रूपांतरित करते."""
    
    # 🔴 FIX: None किंवा Non-datetime व्हॅल्यूज तपासा 🔴
    if utc_dt is None:
        return "N/A"
    if not isinstance(utc_dt, datetime):
        return str(utc_dt) # जर datetime नसेल तर स्ट्रिंगमध्ये परत करा
    # -----------------------------------
    
    # ... (इतर Logic जसाच्या तसा ठेवा) ...
    if utc_dt:
        try:
            # 1. Naive datetime ला UTC म्हणून मार्क करा 
            aware_dt = utc_dt.replace(tzinfo=pytz.utc) 
            # 2. IST मध्ये रूपांतरित करा
            ist_timezone = pytz.timezone('Asia/Kolkata')
            ist_dt = aware_dt.astimezone(ist_timezone)
            # 3. आकर्षक फॉर्मॅटमध्ये परत करा
            return ist_dt.strftime('%d %b %Y, %I:%M:%S %p IST')
        except Exception:
            return utc_dt.strftime('%Y-%m-%d %H:%M:%S') + " (Error/UTC)"
    return "N/A"


def admin_required(f):
    """तपासते की वर्तमान युजर ॲडमिन आहे की नाही."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # युजर लॉग-इन केलेला नाही किंवा ॲडमिन नाही
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied: You must be an administrator.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


# -----------------
# 🔴 Flask-Login सेटअप 🔴
# -----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===================================================================
# 🔴 DATA MODELS (FINAL 16 TABLES SCHEMA) 🔴
# ===================================================================

# 1. PROGRAMMING_LANGUAGES
class ProgrammingLanguage(db.Model):
    __tablename__ = 'programming_languages'
    language_id = db.Column(db.Integer, primary_key=True)
    language_name = db.Column(db.String(255), unique=True, nullable=False)
    version = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)

# 2. BUG_TYPES
class BugType(db.Model):
    __tablename__ = 'bug_types'
    bug_type_id = db.Column(db.Integer, primary_key=True)
    bug_name = db.Column(db.String(255), unique=True, nullable=False)
    bug_description = db.Column(db.Text, nullable=False)
    prevention_best_practices = db.Column(db.Text, nullable=True)

# 3. LEVELS
class Level(db.Model):
    __tablename__ = 'levels' 
    level_id = db.Column(db.Integer, primary_key=True)
    level_number = db.Column(db.Integer, unique=True, nullable=False)
    level_name = db.Column(db.String(255), unique=True, nullable=False)
    points_required = db.Column(db.Integer, nullable=False) 
    xp_required = db.Column(db.Integer, nullable=False, default=0) 
    programming_language_id = db.Column(db.Integer, db.ForeignKey('programming_languages.language_id'), nullable=False)
    users = db.relationship('User', backref='current_level', lazy='dynamic', foreign_keys='User.current_level_id')
    language_rel = db.relationship('ProgrammingLanguage', backref='levels', lazy=True)

# 4. BADGES
class Badge(db.Model):
    __tablename__ = 'badges'
    badge_id = db.Column(db.Integer, primary_key=True)
    badge_name = db.Column(db.String(255), unique=True, nullable=False)
    badge_description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

# 5. SUBSCRIPTION_PLANS
class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    plan_id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(255), unique=True, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    features = db.Column(db.Text, nullable=True)

# 6. USER (Authentication Model)
class User(UserMixin, db.Model): 
    __tablename__ = 'users' 
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, default=0, nullable=False)
    xp = db.Column(db.Integer, default=0, nullable=False)
    current_level_id = db.Column(db.Integer, db.ForeignKey('levels.level_id'), nullable=True)
    virtual_currency = db.Column(db.Integer, default=0, nullable=False)
    profile_picture_url = db.Column(db.String(255), nullable=True, default='/static/default_profile.png')
    registration_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    has_active_subscription = db.Column(db.Boolean, nullable=True, default=False) 
    is_admin = db.Column(db.Boolean, default=False) # 🔴 नवीन फील्ड जोडा Admin sathi🔴

    submissions = db.relationship('UserChallengeSubmission', backref='user', lazy='dynamic', foreign_keys='UserChallengeSubmission.user_id')
    badges_earned = db.relationship('UserBadge', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def get_id(self):
        return str(self.user_id)

# 7. CHALLENGES
class Challenge(db.Model):
    __tablename__ = 'challenges' 
    challenge_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty_level = db.Column(db.String(255), nullable=False)
    points_awarded = db.Column(db.Integer, nullable=False)
    currency_awarded = db.Column(db.Integer, nullable=False, default=0)
    time_limit_minutes = db.Column(db.Integer, nullable=True)
    is_premium = db.Column(db.Boolean, nullable=False, default=False)
    base_code = db.Column(db.Text, nullable=False)
    solution_code = db.Column(db.Text, nullable=False)
    xp_awarded = db.Column(db.Integer, nullable=False, default=0) 
    
    programming_language_id = db.Column(db.Integer, db.ForeignKey('programming_languages.language_id'), nullable=False)
    bug_type_id = db.Column(db.Integer, db.ForeignKey('bug_types.bug_type_id'), nullable=False)

    language_rel = db.relationship('ProgrammingLanguage', backref='challenges', lazy=True)
    bug_type_rel = db.relationship('BugType', backref='challenges', lazy=True)

# 8. USER_SUBSCRIPTIONS
class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    subscription_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.plan_id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    cancellation_date = db.Column(db.DateTime, nullable=True)

    plan_rel = db.relationship('SubscriptionPlan', backref='user_subscriptions', lazy=True)

# 9. PAYMENTS
class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('user_subscriptions.subscription_id'), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(50), nullable=False, default='USD')
    payment_gateway_ref_id = db.Column(db.String(255), nullable=True)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)

    # 🔴 FIX: 'user' रिलेशनशिप जोडा 🔴
    user = db.relationship('User', backref='payments')




# 10. USER_CHALLENGE_SUBMISSIONS
class UserChallengeSubmission(db.Model):
    __tablename__ = 'user_challenge_submissions'
    submission_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.challenge_id'), nullable=False)
    submitted_code = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    submission_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 🔴 FIX: 'challenge_rel' रिलेशनशिप जोडा 🔴
    challenge_rel = db.relationship('Challenge', backref='submissions')



# 11. HINTS
class Hint(db.Model):
    __tablename__ = 'hints'
    hint_id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.challenge_id'), nullable=False)
    hint_text = db.Column(db.Text, nullable=False)
    cost_in_currency = db.Column(db.Integer, nullable=False)
    challenge_rel = db.relationship('Challenge', backref='hints', lazy=True)

# 12. BADGES - Already defined above

# 13. USER_BADGES
class UserBadge(db.Model):
    __tablename__ = 'user_badges'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.badge_id'), primary_key=True)
    date_earned = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 14. LEADERBOARDS
class Leaderboard(db.Model):
    __tablename__ = 'leaderboards'
    leaderboard_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 🔴 FIX: 'user' रिलेशनशिप जोडा 🔴
    user = db.relationship('User', backref='leaderboard_entry', uselist=False)



# 15. FORUM_POSTS
class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    post_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.challenge_id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 16. FORUM_COMMENTS
class ForumComment(db.Model):
    __tablename__ = 'forum_comments'
    comment_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.post_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 17. NOTIFICATIONS (Optional but included for schema completeness)
class Notification(db.Model):
    __tablename__ = 'notifications'
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# ===================================================================
# 🔴 ROUTES (URLs) 🔴
# ===================================================================



@app.route('/')
@app.route('/home') # 🔴 FIX 1: Root URL '/' जोडला 🔴
@login_required 
def home():
    if current_user.is_authenticated:
        all_languages = ProgrammingLanguage.query.all()
        return render_template('index.html', 
                               title="Dashboard", 
                               user=current_user,
                               languages=all_languages)
    return redirect(url_for('login'))

@app.route('/profile')
@login_required 
def profile():
    return render_template('profile.html', title="User Profile")

@app.route('/leaderboard')
@login_required 
def leaderboard_list():
    top_users = User.query.order_by(User.xp.desc()).limit(10).all()
    return render_template('leaderboard.html', title="Leaderboard", top_users=top_users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or Email already exists.', 'danger')
            return redirect(url_for('register'))
        default_level = Level.query.filter_by(level_number=1).first()
        if not default_level:
            flash('Default level not found. Contact Admin.', 'danger')
            return redirect(url_for('register'))
        new_user = User(
            username=username, email=email, current_level_id=default_level.level_id,
            points=0, xp=0, virtual_currency=0,
            profile_picture_url='/static/default_profile.png', has_active_subscription=False,
            registration_date=datetime.utcnow()
        ) 
        new_user.set_password(password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login')) 
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration.', 'danger')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User.query.filter_by(email=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        flash('Login successful!', 'success')

        # 🔴 नवीन ॲडमिन चेक Logic 🔴
        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        # ---------------------------

        next_page = request.args.get('next')
        return redirect(next_page or url_for('home'))
    return render_template('login.html')



@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """ॲडमिनसाठी डेटा व्ह्यू आणि मॅनेजमेंट दाखवतो."""
    
    # 🔴 डेटाबेसमधून सर्व आवश्यक डेटा वाचा 🔴
    all_users = db.session.execute(db.select(User).order_by(User.user_id.asc())).scalars().all()
    all_challenges = db.session.execute(db.select(Challenge)).scalars().all()
    all_subs = db.session.execute(db.select(UserSubscription)).scalars().all()
    all_plans = db.session.execute(db.select(SubscriptionPlan)).scalars().all()
    
    return render_template('admin/admin_dashboard.html',
                           title='Admin Control Panel',
                           users=all_users,
                           challenges=all_challenges,
                           subscriptions=all_subs,
                           plans=all_plans)




@app.route('/admin/manage/<string:model_name>')
@login_required
@admin_required
def admin_manage_data(model_name):
    """टेबलच्या नावावरून डायनॅमिकली डेटा वाचतो आणि दाखवतो."""
    
    # 🔴 1. टेबल मॉडेल मॅप करा 🔴
    model_map = {
        'User': User, 'Challenge': Challenge, 'SubscriptionPlan': SubscriptionPlan,
        'UserSubscription': UserSubscription, 'ProgrammingLanguage': ProgrammingLanguage,
        'BugType': BugType, 'Level': Level, 'UserChallengeSubmission': UserChallengeSubmission,
        'Badge': Badge, 'UserBadge': UserBadge, 'Leaderboard': Leaderboard,
        'Hint': Hint, 'Payment': Payment, 'ForumPost': ForumPost,
        'ForumComment': ForumComment, 'Notification': Notification
    }
    
    ModelClass = model_map.get(model_name)
    if not ModelClass:
        flash(f"Error: Model '{model_name}' not found.", 'danger')
        return redirect(url_for('admin_dashboard'))

    # 🔴 2. Eager Loading Logic 🔴
    query = db.select(ModelClass)

    # 1. User मॉडेलसाठी, current_level लोड करा
    if ModelClass == User:
        query = db.select(User).options(joinedload(User.current_level))
        
    # 2. Subscription मॉडेलसाठी, Plan लोड करा
    elif ModelClass == UserSubscription:
        query = db.select(UserSubscription).options(joinedload(UserSubscription.plan_rel))
        
    # 3. Submissions मॉडेलसाठी, User आणि Challenge लोड करा
    elif ModelClass == UserChallengeSubmission:
         query = db.select(UserChallengeSubmission).options(joinedload(UserChallengeSubmission.user), 
                                                            joinedload(UserChallengeSubmission.challenge_rel))
    
    elif ModelClass == Challenge:
         # Challenge मॉडेलसाठी, Language आणि Bug Type लोड करा
         query = db.select(Challenge).options(joinedload(Challenge.language_rel), 
                                              joinedload(Challenge.bug_type_rel))
    
    elif ModelClass == Leaderboard:
         # Leaderboard मॉडेलसाठी, User लोड करा
         query = db.select(Leaderboard).options(joinedload(Leaderboard.user))
         
    elif ModelClass == Payment:
         # Payment मॉडेलसाठी, User लोड करा
         query = db.select(Payment).options(joinedload(Payment.user))

    # 🔴 3. डेटा Fetch करा 🔴
    all_data = db.session.execute(query).scalars().unique().all()
    
    # 4. कॉलम हेडिंग्स मिळवा
    column_names = [col.key for col in ModelClass.__table__.columns]
    
    return render_template('admin/admin_data_view.html',
                           title=f"Manage {model_name}",
                           model_name=model_name,
                           data=all_data,
                           columns=column_names)









@app.route('/logout')
@login_required 
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/challenges')
@app.route('/challenges/<string:language_name>')
@login_required 
def challenges_list(language_name=None):
    all_languages = ProgrammingLanguage.query.all()
    
    if language_name:
        lang = ProgrammingLanguage.query.filter_by(language_name=language_name).first()
        if lang:
            # 🔴 FIX: निवडलेल्या भाषेनुसार Levels फिल्टर करा 🔴
            all_levels = Level.query.filter_by(programming_language_id=lang.language_id).order_by(Level.level_number).all()
        else:
            all_levels = []
    else:
        all_levels = [] 
        
    return render_template('challenges.html', 
                           levels=all_levels,
                           all_languages=all_languages,
                           selected_language=language_name,
                           title=f"{language_name} Learning Path" if language_name else "Select Language")

# app.py मध्ये (routes विभागात)

# app.py मध्ये (challenges_list नंतर किंवा routes विभागात)
# app.py मध्ये (submit_solution रूट नंतर)

@app.route('/plans') # 🔴 1. plans_list रूट 🔴
def plans_list():
    # DataBase मधून प्लॅन्सचा डेटा वाचून plans.html ला पाठवा
    all_plans = SubscriptionPlan.query.all()
    # FIX: फक्त प्रीमियम प्लॅन्स दाखवण्यासाठी बेसिक प्लॅन फिल्टर करा
    premium_plans = [plan for plan in all_plans if plan.plan_name != 'Basic']
    return render_template('plans.html', plans=premium_plans)

@app.route('/start_trial/<int:plan_id>', methods=['POST']) # 🔴 2. start_trial रूट 🔴
@login_required
def start_trial(plan_id):
    trial_plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Validation Logic
    if trial_plan.price > 0.00:
        flash('Invalid trial plan selected. This is a paid plan.', 'danger')
        return redirect(url_for('plans_list'))
        
    if trial_plan.duration_days != 7:
        flash('Invalid trial plan selected. Duration must be 7 days.', 'danger')
        return redirect(url_for('plans_list'))

    # Subscription Logic
    current_user.has_active_subscription = True
    end_date = datetime.utcnow() + timedelta(days=trial_plan.duration_days)
    
    new_user_subscription = UserSubscription(
        user_id=current_user.user_id,
        plan_id=plan_id,
        start_date=datetime.utcnow(),
        end_date=end_date,
        is_active=True
    )
    db.session.add(new_user_subscription)
    db.session.commit()
    
    flash('🎉 Congratulations! 7-Day Pro Trial Activated. Enjoy premium challenges!', 'success')
    return redirect(url_for('home'))

@app.route('/challenge/<int:challenge_id>')
@login_required
def challenge_detail(challenge_id):
    # Challenge ID नुसार डेटाबेस मधून Challenge शोधतो
    challenge = Challenge.query.get_or_404(challenge_id)
    # challenge_editor.html हे पेज render करतो आणि त्याला challenge चा डेटा पाठवतो
    return render_template('challenge_editor.html', challenge=challenge)

# **(येथे तुमचा नवीन Submission Code येईल)**

# app.py मध्ये (Challenge Editor नंतर हा कोड जोडा)



# app.py मध्ये, @app.route('/submit_solution/<int:challenge_id>') फंक्शन पूर्णपणे बदला.

# app.py मध्ये, @app.route('/submit_solution/<int:challenge_id>') फंक्शन पूर्णपणे बदला.

@app.route('/submit_solution/<int:challenge_id>', methods=['POST'])
@login_required
def submit_solution(challenge_id):
    """
    युजर कोड स्वीकारतो, मूल्यांकन करतो आणि Gamification Logic चालवतो.
    XP/Points फक्त पहिल्या यशस्वी प्रयत्नासाठी दिले जातात. पुढील यशस्वी प्रयत्न रेकॉर्ड होत नाहीत.
    """
    challenge = Challenge.query.get_or_404(challenge_id)
    user_code = request.form.get('code')
    
    if not user_code:
        flash('Code submission cannot be empty.', 'danger')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))

    import re
    # Whitespace काढून अचूक तुलना करा
    clean_user_code = re.sub(r'\s+', '', user_code).strip()
    clean_solution_code = re.sub(r'\s+', '', challenge.solution_code).strip()
    is_correct = (clean_user_code == clean_solution_code)
    
    # 🔴 १. मागील यशस्वी प्रयत्नाची नोंद तपासा 🔴
    already_solved_successfully = UserChallengeSubmission.query.filter_by(
        user_id=current_user.user_id,
        challenge_id=challenge_id,
        is_correct=True
    ).first()
    
    score_awarded = 0
    xp_awarded = 0
    
    # डेटाबेस कमिट लॉजिक (Commit Logic)
    try:
        # 🔴 २. Gamification Logic (XP/Points) 🔴
        if is_correct:
            if not already_solved_successfully:
                score_awarded = challenge.points_awarded
                xp_awarded = challenge.xp_awarded
                
                # XP/Points वाढवा आणि Leaderboard अपडेट करा
                current_user.points += score_awarded
                current_user.xp += xp_awarded
                
                leaderboard_entry = Leaderboard.query.filter_by(user_id=current_user.user_id).first()
                if leaderboard_entry:
                    leaderboard_entry.score = current_user.xp
                    leaderboard_entry.last_updated = datetime.utcnow()
                else:
                    db.session.add(Leaderboard(
                        user_id=current_user.user_id, score=current_user.xp, ranking=0, last_updated=datetime.utcnow()
                    ))
                
                flash(f'Challenge "{challenge.title}" Completed! You earned {xp_awarded} XP and {score_awarded} Pts! 🎉', 'success')
            else:
                # FIX: पुढील यशस्वी प्रयत्नासाठी स्पष्ट संदेश (Clear Message for Repeated Success)
                flash(f'✅ Correct! Challenge "{challenge.title}" passed again. No additional XP/Points awarded (already solved).', 'info')
                
        else:
            # कोड चुकला (Failed Submission)
            flash(f'❌ Incorrect! Challenge "{challenge.title}" failed. Please review your code and try again.', 'danger')

        # 🔴 ३. SUBMISSION डेटा सेव्ह करा (Best Practice) 🔴
        # जर यशस्वी सबमिशन पुन्हा येत असेल, तर त्याची नोंदणी (Record) टाळा.
        # फक्त अयशस्वी प्रयत्न (Failed Attempts) किंवा पहिला यशस्वी प्रयत्न रेकॉर्ड होईल.
        if not (already_solved_successfully and is_correct):
            submission = UserChallengeSubmission(
                user_id=current_user.user_id,
                challenge_id=challenge_id,
                submitted_code=user_code,
                is_correct=is_correct,
                score=score_awarded, 
                submission_date=datetime.utcnow()
            )
            db.session.add(submission)
        
        # 🔴 ४. एकाच वेळी कमिट करा (Commit Once) 🔴
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        # Rollback नंतर error message द्या.
        flash(f'A critical database error occurred: {e}', 'danger')
    
    return redirect(url_for('challenge_detail', challenge_id=challenge_id))
    







# app.py मध्ये, Hint API Logic जोडा

@app.route('/use_hint/<int:challenge_id>', methods=['POST'])
@login_required
def use_hint(challenge_id):
    """Hint वापरल्यास युजरकडून Coins वजा करतो."""
    challenge = Challenge.query.get_or_404(challenge_id)
    hint = Hint.query.filter_by(challenge_id=challenge.challenge_id).first()
    
    if not hint:
        return jsonify({'status': 'error', 'message': 'No hint available for this challenge.'}), 404
        
    hint_cost = hint.cost_in_currency
    
    if current_user.virtual_currency < hint_cost:
        return jsonify({'status': 'error', 'message': 'Insufficient Virtual Currency.'}), 403

    # कॉइन्स वजा करा
    current_user.virtual_currency -= hint_cost
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'new_currency': current_user.virtual_currency,
            'hint_text': hint.hint_text
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Database error.'}), 500
    




# app.py मधील level_detail route (UNIT ID शोधण्यासाठी सुधारित)

@app.route('/level/<int:level_id>')
@login_required
def level_detail(level_id):
    level = Level.query.get_or_404(level_id)
    
    # C भाषेसाठी आवश्यक ID शोधा (कारण आपण C लेव्हल्स तयार केल्या आहेत)
    lang_c_id = ProgrammingLanguage.query.filter_by(language_name='C').first().language_id
    
    # 🔴 FIX: Units मध्ये Challenge ID जोडणे 🔴
    units_data = []
    
    # Level 1 Logic
    if level.level_number == 1 and level.programming_language_id == lang_c_id:
        units_map = [
            ("Variables & Data Types", "C: Basic Calculator"), # Challenge Title 
            ("Operators & Expressions", "C: Basic Calculator"), 
            ("Input/Output (I/O)", "C: Basic Calculator"),
        ]
        
        # DataBase मधून Challenge ID शोधणे
        c_challenge = Challenge.query.filter_by(title="C: Basic Calculator").first()
        c_id = c_challenge.challenge_id if c_challenge else 0

        for name, _ in units_map:
            units_data.append({
                "name": name, 
                "challenge_id": c_id # 🔴 येथे Challenge ID जोडला 🔴
            })
    
    elif level.level_number == 2:
        units_data = [
            {"name": "Conditional Statements", "url": "#unit/cond", "challenge_id": 0},
            {"name": "Looping Structures", "url": "#unit/loops", "challenge_id": 0},
            {"name": "Switch Statement", "url": "#unit/switch", "challenge_id": 0},
        ]
    elif level.level_number == 3:
        units_data = [
            {"name": "Functions (Prototyping)", "url": "#unit/func", "challenge_id": 0},
            {"name": "Recursion", "url": "#unit/recur", "challenge_id": 0},
            {"name": "MINI-BOSS REWARD", "is_reward": True, "challenge_id": 0},
        ]
    # ... बाकीचे Levels 4, 5, 6 साठी डेटा...
    elif level.level_number == 4:
        units_data = [
            {"name": "Arrays (1D & Multi-dim.)", "url": "#unit/arr", "challenge_id": 0},
            {"name": "Strings", "url": "#unit/str", "challenge_id": 0},
            {"name": "Structures & Unions", "url": "#unit/struct", "challenge_id": 0},
        ]
    elif level.level_number == 5:
        units_data = [
            {"name": "Pointers (Fundamentals)", "url": "#unit/ptr", "challenge_id": 0},
            {"name": "Dynamic Memory", "url": "#unit/dyn", "challenge_id": 0},
            {"name": "Pointers to Arrays & Strings", "url": "#unit/ptr_arr", "challenge_id": 0},
        ]
    elif level.level_number == 6:
        units_data = [
            {"name": "File Input/Output", "url": "#unit/file", "challenge_id": 0},
            {"name": "Preprocessor Directives", "url": "#unit/pre", "challenge_id": 0},
            {"name": "MEGA-BOSS REWARD", "is_reward": True, "challenge_id": 0},
        ]

    return render_template('level_detail.html', 
                           level=level, 
                           units=units_data,
                           title=level.level_name)

# ===================================================================
# 🔴 APP STARTUP LOGIC आणि Default Data 🔴
# ===================================================================
if __name__ == '__main__':
    # जुनी DB फाईल डिलीट करा (नवीन 16-टेबल मॉडेल तयार करण्यासाठी)
    if os.path.exists('bugbounty_pro.db'):
        os.remove('bugbounty_pro.db')
        print("Old bugbounty_pro.db file removed.")
        
    with app.app_context():
        db.create_all() 
        print("Database tables created (16-table schema initialized).")
        
        # -------------------
        # Default Data (Foreign Keys साठी आवश्यक)
        # -------------------

        # 2. Languages इन्सर्ट करा (आधी कारण Levels ला Language ID हवा)
        if ProgrammingLanguage.query.count() == 0:
            lang_c = ProgrammingLanguage(language_name='C', version='C18', image_url='icons/c.png')
            lang_cpp = ProgrammingLanguage(language_name='C++', version='C++20', image_url='icons/cpp.png')
            lang_dsa = ProgrammingLanguage(language_name='DSA', version='Algorithms', image_url='icons/dsa.png')
            lang_csharp = ProgrammingLanguage(language_name='C#', version='9.0', image_url='icons/csharp.png')
            lang_py = ProgrammingLanguage(language_name='Python', version='3.10', image_url='icons/python.png')
            lang_java = ProgrammingLanguage(language_name='Java', version='17', image_url='icons/java.png')
            lang_go = ProgrammingLanguage(language_name='Go', version='1.18', image_url='icons/go.png')
            lang_ruby = ProgrammingLanguage(language_name='Ruby', version='3.0', image_url='icons/ruby.png')

            db.session.add_all([lang_c, lang_cpp, lang_dsa, lang_csharp, lang_py, lang_java, lang_go, lang_ruby])
            db.session.commit()
            print("Default Languages created.")
        
        # 1. Level 1 इन्सर्ट करा.
        if Level.query.filter_by(level_number=1).first() is None:
            # C भाषेसाठी आवश्यक ID शोधा
            lang_c_id = ProgrammingLanguage.query.filter_by(language_name='C').first().language_id
            
            # 🔴 FIX: 6 C-Language Levels DataBase मध्ये इन्सर्ट करा 🔴
            levels_to_add = [
                Level(level_number=1, level_name='L1: Basic Fundamentals', points_required=0, xp_required=0, programming_language_id=lang_c_id),
                Level(level_number=2, level_name='L2: Control Flow', points_required=100, xp_required=150, programming_language_id=lang_c_id),
                Level(level_number=3, level_name='L3: Functions & Structure', points_required=300, xp_required=350, programming_language_id=lang_c_id), 
                Level(level_number=4, level_name='L4: Data Structures (Basic)', points_required=600, xp_required=550, programming_language_id=lang_c_id),
                Level(level_number=5, level_name='L5: Memory Management', points_required=1000, xp_required=800, programming_language_id=lang_c_id),
                Level(level_number=6, level_name='L6: File Handling & Advanced', points_required=1500, xp_required=1200, programming_language_id=lang_c_id),
            ]
            db.session.add_all(levels_to_add)
            db.session.commit()
            print("All 6 C-Language Levels created.")
            
        # 3. Bug Types इन्सर्ट करा.
        if BugType.query.count() == 0:
            b1 = BugType(bug_name='SQL Injection', bug_description='Vulnerability due to unvalidated user input in SQL query.', prevention_best_practices='Use Parameterized Queries.')
            b2 = BugType(bug_name='Race Condition', bug_description='Timing issue in multithreaded systems.', prevention_best_practices='Use locks or synchronization blocks.')
            b3 = BugType(bug_name='XSS', bug_description='Cross-Site Scripting vulnerability.', prevention_best_practices='Sanitize and escape user input before rendering.')
            db.session.add_all([b1, b2, b3])
            db.session.commit()
        
        # app.py मध्ये, APP STARTUP LOGIC विभागाच्या आत (Subsciption Plans चा भाग)

       # 4. Subscription Plans इन्सर्ट करा.
        if SubscriptionPlan.query.count() == 0:
            p_trial = SubscriptionPlan(plan_name="Free Trial (7 Days)", price=0.00, duration_days=7, features="Full access to all challenges for 7 days.", description="Trial Access.")
            p_weekly = SubscriptionPlan(plan_name="Weekly Pro", price=99.00, duration_days=7, features="Full access, Advanced tools, No Ads.", description="Short-term intensive access.")
            p_monthly = SubscriptionPlan(plan_name="Monthly Pro", price=299.00, duration_days=30, features="Full access, Advanced tools, No Ads.", description="Standard monthly access.")
            p_annual = SubscriptionPlan(plan_name="Annual Pro", price=2999.00, duration_days=365, features="Full access, Advanced tools, No Ads, 15% discount.", description="Best long-term value.")

            db.session.add_all([p_trial, p_weekly, p_monthly, p_annual])
            db.session.commit()
            print("Default Subscription Plans created.")

        # 5. डमी चॅलेंजेस इन्सर्ट करा (C भाषेचे चॅलेंजेस जोडले)
        if Challenge.query.count() == 0:
            lang_py_id = ProgrammingLanguage.query.filter_by(language_name='Python').first().language_id
            bug_sql_id = BugType.query.filter_by(bug_name='SQL Injection').first().bug_type_id
            
            c1 = Challenge(title="SQL Injection Fix", description="Fix the Python login function.", difficulty_level="Hard", 
                           points_awarded=150, xp_awarded=50, currency_awarded=10, programming_language_id=lang_py_id, bug_type_id=bug_sql_id,
                           base_code="# VULNERABLE PYTHON CODE", solution_code="# FIXED PYTHON CODE", is_premium=False, time_limit_minutes=30)
            
            lang_c_id = ProgrammingLanguage.query.filter_by(language_name='C').first().language_id
            bug_logic_id = BugType.query.filter_by(bug_name='Race Condition').first().bug_type_id 
            
            c_c1 = Challenge(title="C: Basic Calculator", 
                             description="Fix the syntax error in the C program that prevents it from correctly calculating the sum of two integers.", 
                             difficulty_level="Beginner", points_awarded=50, xp_awarded=20, currency_awarded=5, 
                             programming_language_id=lang_c_id, bug_type_id=bug_logic_id,
                             base_code='#include <stdio.h>\n\nint main() {\n    int a = 10;\n    int b = 5;\n    printf("Sum is: %d\\n", a, b);\n    return 0;\n}',
                             solution_code='#include <stdio.h>\n\nint main() {\n    int a = 10;\n    int b = 5;\n    printf("Sum is: %d\\n", a + b);\n    return 0;\n}',
                             is_premium=False, time_limit_minutes=15)
                             
            c_c4 = Challenge(title="C: File Access Permission", 
                             description="The program attempts to read a file but fails due to incorrect file opening mode. Fix the file mode to allow both read and write operations.", 
                             difficulty_level="Intermediate", points_awarded=150, xp_awarded=60, currency_awarded=15, 
                             programming_language_id=lang_c_id, bug_type_id=bug_logic_id,
                             base_code='#include <stdio.h>\n\nint main() {\n    FILE *fp = fopen("data.txt", "r"); // ❌ Incorrect mode\n    // ... rest of the code attempts to write\n    return 0;\n}',
                             solution_code='#include <stdio.h>\n\nint main() {\n    FILE *fp = fopen("data.txt", "r+"); // ✅ Corrected mode\n    // ...\n    return 0;\n}',
                             is_premium=False, time_limit_minutes=45)

            db.session.add_all([c1, c_c1, c_c4])
            db.session.commit()
            print("Default Challenges created.")


             # 🔴 डीफॉल्ट ॲडमिन युजर तयार करा 🔴
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                # 1 हा मूलभूत लेव्हल आयडी आहे
                default_level = Level.query.filter_by(level_number=1).first() 
                
                admin_user = User(username='admin', 
                                email='admin@bugbountypro.com', 
                                points=1000, 
                                xp=1000, 
                                current_level_id=default_level.level_id, 
                                virtual_currency=500,
                                registration_date=datetime.utcnow(),
                                has_active_subscription=True,
                                is_admin=True) # ॲडमिन म्हणून सेट करा
                
                # 🔴 पासवर्ड हॅश करा 🔴
                admin_user.set_password('AdminPass@123') 
                
                db.session.add(admin_user)
                db.session.commit()
                print("Default Admin User created: admin / AdminPass@123")

    app.run(debug=True)


