#!/usr/bin/env python3
"""
Lantern Billing Integration
Simple Stripe subscription management for $20/mo family plan.
"""

import json
import hmac
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class LanternBilling:
    """Manages Lantern billing and subscriptions."""

    def __init__(self):
        """Initialize billing system."""
        self.billing_dir = Path.home() / ".lantern" / "billing"
        self.billing_dir.mkdir(parents=True, exist_ok=True)

        self.customers_file = self.billing_dir / "customers.jsonl"
        self.payments_file = self.billing_dir / "payments.jsonl"
        self.subscriptions_file = self.billing_dir / "subscriptions.jsonl"

    def register_customer(self, customer_id: str, family_name: str,
                        email: str, plan: str = "family") -> Dict[str, Any]:
        """
        Register a new customer.

        Args:
            customer_id: Unique customer ID (can be UUID or Stripe customer ID)
            family_name: Family's name
            email: Family's email
            plan: Subscription plan (family=$20/mo, kids=$30/mo)

        Returns:
            Customer record
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "customer_id": customer_id,
            "family_name": family_name,
            "email": email,
            "plan": plan,
            "status": "active",
            "trial_starts": datetime.now().isoformat(),
            "trial_ends": (datetime.now() + timedelta(days=30)).isoformat()
        }

        with open(self.customers_file, 'a') as f:
            f.write(json.dumps(record) + '\n')

        return record

    def start_free_trial(self, customer_id: str, trial_days: int = 30) -> Dict[str, Any]:
        """Start a free trial for a customer."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "trial_start",
            "customer_id": customer_id,
            "trial_days": trial_days,
            "trial_ends": (datetime.now() + timedelta(days=trial_days)).isoformat()
        }

        with open(self.subscriptions_file, 'a') as f:
            f.write(json.dumps(record) + '\n')

        return record

    def process_payment(self, customer_id: str, amount: float, currency: str = "USD",
                       period: str = "monthly") -> Dict[str, Any]:
        """
        Process a payment (for Stripe webhook or manual processing).

        Args:
            customer_id: Customer ID
            amount: Payment amount
            currency: Currency code (USD, EUR, GBP, etc.)
            period: Billing period (monthly, yearly)

        Returns:
            Payment record
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "customer_id": customer_id,
            "amount": amount,
            "currency": currency,
            "period": period,
            "status": "succeeded",
            "next_billing_date": (datetime.now() + timedelta(days=30 if period == "monthly" else 365)).isoformat()
        }

        with open(self.payments_file, 'a') as f:
            f.write(json.dumps(record) + '\n')

        return record

    def get_customer_status(self, customer_id: str) -> Dict[str, Any]:
        """Get current status of a customer's subscription."""
        status = {
            "customer_id": customer_id,
            "active": False,
            "trial_active": False,
            "paid": False,
            "next_billing_date": None
        }

        # Check if trial is active
        if self.subscriptions_file.exists():
            with open(self.subscriptions_file) as f:
                for line in f:
                    record = json.loads(line)
                    if record.get('customer_id') == customer_id and record.get('event') == 'trial_start':
                        trial_end = datetime.fromisoformat(record['trial_ends'])
                        if datetime.now() < trial_end:
                            status["trial_active"] = True
                            status["trial_ends"] = record['trial_ends']

        # Check if payment made
        if self.payments_file.exists():
            with open(self.payments_file) as f:
                for line in f:
                    record = json.loads(line)
                    if record.get('customer_id') == customer_id:
                        if record.get('status') == 'succeeded':
                            status["paid"] = True
                            status["last_payment"] = record['timestamp']
                            status["next_billing_date"] = record.get('next_billing_date')

        status["active"] = status["trial_active"] or status["paid"]

        return status

    def create_payment_link(self, customer_id: str, family_name: str,
                           plan: str = "family") -> str:
        """
        Generate a Stripe payment link (mock for MVP).

        Real implementation would use Stripe API:
        https://stripe.com/docs/payments/payment-links

        Args:
            customer_id: Customer ID
            family_name: Family name
            plan: Plan type (family=$20, kids=$30)

        Returns:
            Payment link URL
        """
        price_map = {
            "family": "20",
            "kids": "30"
        }

        price = price_map.get(plan, "20")

        # Mock payment link (real would be from Stripe)
        link = (
            f"https://buy.stripe.com/test_lantern?customer_id={customer_id}"
            f"&family_name={family_name}&plan={plan}&price={price}"
        )

        # Log link creation
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "payment_link_created",
            "customer_id": customer_id,
            "family_name": family_name,
            "plan": plan,
            "price": price,
            "link": link
        }

        with open(self.subscriptions_file, 'a') as f:
            f.write(json.dumps(record) + '\n')

        return link

    @staticmethod
    def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
        """
        Verify a Stripe webhook signature (for real Stripe integration).

        Args:
            payload: Raw webhook payload
            signature: Signature from Stripe header
            secret: Your Stripe webhook secret

        Returns:
            True if signature is valid
        """
        computed = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed, signature)

    def handle_stripe_webhook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.

        Supported events:
        - payment_intent.succeeded
        - customer.subscription.created
        - customer.subscription.updated
        - customer.subscription.deleted
        - invoice.payment_succeeded
        - invoice.payment_failed

        Args:
            event: Stripe event object

        Returns:
            Response status
        """
        event_type = event.get('type')
        data = event.get('data', {}).get('object', {})

        if event_type == 'payment_intent.succeeded':
            customer_id = data.get('customer')
            amount = data.get('amount') / 100  # Stripe uses cents
            currency = data.get('currency').upper()

            self.process_payment(customer_id, amount, currency)
            return {"status": "processed", "event": event_type}

        elif event_type == 'customer.subscription.created':
            customer_id = data.get('customer')
            plan = "family" if data.get('metadata', {}).get('plan') == 'family' else 'kids'
            self.start_free_trial(customer_id, trial_days=0)  # Trial already started
            return {"status": "created", "event": event_type}

        elif event_type == 'customer.subscription.deleted':
            customer_id = data.get('customer')
            record = {
                "timestamp": datetime.now().isoformat(),
                "event": "subscription_cancelled",
                "customer_id": customer_id
            }
            with open(self.subscriptions_file, 'a') as f:
                f.write(json.dumps(record) + '\n')
            return {"status": "cancelled", "event": event_type}

        else:
            return {"status": "ignored", "event": event_type}

    def get_revenue_summary(self) -> Dict[str, Any]:
        """
        Get revenue summary (for Founder dashboard).

        Returns:
            Revenue stats
        """
        summary = {
            "total_customers": 0,
            "active_subscriptions": 0,
            "total_revenue_usd": 0.0,
            "monthly_recurring_revenue": 0.0,
            "customers": []
        }

        # Count customers
        if self.customers_file.exists():
            with open(self.customers_file) as f:
                for line in f:
                    record = json.loads(line)
                    if record.get('status') == 'active':
                        summary["total_customers"] += 1
                        summary["customers"].append({
                            "family_name": record.get('family_name'),
                            "email": record.get('email'),
                            "plan": record.get('plan'),
                            "trial_ends": record.get('trial_ends')
                        })

        # Count paid subscriptions
        if self.payments_file.exists():
            with open(self.payments_file) as f:
                for line in f:
                    record = json.loads(line)
                    if record.get('status') == 'succeeded':
                        amount = record.get('amount', 0)
                        summary["total_revenue_usd"] += amount
                        summary["monthly_recurring_revenue"] += amount  # Simplified

        summary["active_subscriptions"] = summary["total_customers"]

        return summary


# Example usage:

"""
from lantern_billing import LanternBilling

# Initialize
billing = LanternBilling()

# Register Family A
billing.register_customer(
    customer_id="family-a-001",
    family_name="Smith Family",
    email="smith@example.com",
    plan="family"
)

# Start free trial
billing.start_free_trial("family-a-001", trial_days=30)

# Get payment link to send to customer
link = billing.create_payment_link(
    customer_id="family-a-001",
    family_name="Smith Family",
    plan="family"
)
print(f"Send this link to customer: {link}")

# Check customer status
status = billing.get_customer_status("family-a-001")
print(f"Customer status: {status}")

# Process a payment (when webhook received or manual entry)
billing.process_payment(
    customer_id="family-a-001",
    amount=20.00,
    currency="USD",
    period="monthly"
)

# Get revenue summary
summary = billing.get_revenue_summary()
print(f"Revenue: ${summary['total_revenue_usd']:.2f}, MRR: ${summary['monthly_recurring_revenue']:.2f}")
"""
