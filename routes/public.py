from flask import Blueprint, render_template, request, abort
from models import db, BlogPost, Speciality, Service, Testimonial

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    testimonials = Testimonial.query.filter_by(is_approved=True).order_by(Testimonial.created_at.desc()).limit(6).all()
    blogs = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).limit(3).all()
    specialities = Speciality.query.filter_by(is_active=True).limit(8).all()
    return render_template('index.html', testimonials=testimonials, blogs=blogs, specialities=specialities)

@public_bp.route('/about')
def about():
    return render_template('about.html')

@public_bp.route('/specialities')
def specialities():
    specs = Speciality.query.filter_by(is_active=True).all()
    return render_template('specialities.html', specialities=specs)

@public_bp.route('/specialities/<slug>')
def speciality_detail(slug):
    spec = Speciality.query.filter_by(slug=slug, is_active=True).first_or_404()
    return render_template('speciality_detail.html', speciality=spec)

@public_bp.route('/services')
def services():
    svcs = Service.query.filter_by(is_active=True).all()
    return render_template('services.html', services=svcs)

@public_bp.route('/blog')
def blog():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    query = BlogPost.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(BlogPost.title.ilike(f'%{search}%'))
    posts = query.order_by(BlogPost.published_at.desc()).paginate(page=page, per_page=6, error_out=False)
    categories = db.session.query(BlogPost.category).distinct().filter(BlogPost.is_published==True).all()
    return render_template('blog.html', posts=posts, categories=categories, search=search, current_category=category)

@public_bp.route('/blog/<slug>')
def blog_post(slug):
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    post.views += 1
    db.session.commit()
    related = BlogPost.query.filter_by(category=post.category, is_published=True).filter(BlogPost.id != post.id).limit(3).all()
    return render_template('blog_post.html', post=post, related=related)

@public_bp.route('/contact')
def contact():
    return render_template('contact.html')

@public_bp.route('/contact', methods=['POST'])
def contact_submit():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    message = request.form.get('message')
    from flask import flash, redirect, url_for
    flash('Thank you! Your message has been received. We will contact you shortly.', 'success')
    return redirect(url_for('public.contact'))
