import stripe
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, current_app, url_for
from flask_login import login_required, current_user
from app import db
from models import User

subscription_bp = Blueprint('subscription', __name__, url_prefix='/subscription')

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@subscription_bp.route('/config')
def get_publishable_key():
    return jsonify({
        'publishableKey': os.environ.get('STRIPE_PUBLISHABLE_KEY')
    })

@subscription_bp.route('/plans')
@login_required
def plans():
    return render_template('subscription/plans.html')

@subscription_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        price_id = request.form.get('price_id')
        if not price_id:
            return jsonify({'error': 'Price ID is required'}), 400

        # Map frontend price IDs to actual Stripe price IDs
        price_map = {
            'price_pro': os.environ.get('STRIPE_PRO_PRICE_ID', 'price_pro'),
            'price_enterprise': os.environ.get('STRIPE_ENTERPRISE_PRICE_ID', 'price_enterprise')
        }

        actual_price_id = price_map.get(price_id)
        if not actual_price_id:
            return jsonify({'error': 'Invalid price ID'}), 400

        success_url = url_for('subscription.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = url_for('subscription.plans', _external=True)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': actual_price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=current_user.email,
            metadata={
                'user_id': current_user.id
            }
        )
        return jsonify({'sessionId': checkout_session.id})
    except Exception as e:
        current_app.logger.error(f"Stripe session creation error: {str(e)}")
        return jsonify({'error': str(e)}), 403

@subscription_bp.route('/success')
@login_required
def success():
    session_id = request.args.get('session_id')
    if session_id:
        try:
            # Verify the session
            session = stripe.checkout.Session.retrieve(session_id)

            # Update user's subscription status
            if session.payment_status == 'paid':
                current_user.subscription_status = 'active'
                # Set subscription end date to 30 days from now
                current_user.subscription_end = datetime.utcnow() + timedelta(days=30)
                db.session.commit()

                return render_template('subscription/success.html', 
                                     status='success',
                                     message='Your subscription has been activated successfully!')
        except Exception as e:
            current_app.logger.error(f"Stripe success verification error: {str(e)}")
            return render_template('subscription/success.html', 
                                 status='error',
                                 message='There was an error verifying your payment.')

    return render_template('subscription/success.html', 
                         status='error',
                         message='Invalid session ID.')

@subscription_bp.route('/cancel')
@login_required
def cancel():
    return render_template('subscription/plans.html', 
                         error='The subscription process was cancelled.')