import stripe
import os
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from models import User

subscription_bp = Blueprint('subscription', __name__, url_prefix='/subscription')

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@subscription_bp.route('/plans')
@login_required
def plans():
    return render_template('subscription/plans.html')

@subscription_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': request.form.get('price_id'),
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'subscription/cancel',
            customer_email=current_user.email,
        )
        return jsonify({'sessionId': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 403

@subscription_bp.route('/success')
@login_required
def success():
    session_id = request.args.get('session_id')
    if session_id:
        session = stripe.checkout.Session.retrieve(session_id)
        current_user.subscription_status = 'active'
        db.session.commit()
    return render_template('subscription/success.html')
