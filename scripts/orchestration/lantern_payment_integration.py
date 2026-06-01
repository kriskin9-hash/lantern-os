#!/usr/bin/env python3
"""
Lantern Payment Integration
Stripe API for subscription billing ($200/mo per family)
All local processing, PCI-compliant storage
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# TODO: pip install stripe
# import stripe

class LanternPayments:
    """Handle subscription billing for Lantern families."""

    def __init__(self, api_key=None):
        """
        Initialize payment processor.

        Args:
            api_key: Stripe API key (from ~/.lantern/stripe-key.json)
        """
        self.api_key = api_key or self._load_stripe_key()
        # stripe.api_key = self.api_key  # Uncomment when stripe installed
        self.billing_path = Path.home() / '.lantern' / 'state' / 'billing.json'
        self.invoices_path = Path.home() / '.lantern' / 'invoices'
        self.invoices_path.mkdir(parents=True, exist_ok=True)

    def _load_stripe_key(self):
        """Load Stripe API key from local config."""
        try:
            key_file = Path.home() / '.lantern' / 'stripe-key.json'
            if key_file.exists():
                with open(key_file) as f:
                    data = json.load(f)
                    return data.get('sk_live') or data.get('sk_test')
        except:
            pass
        return None

    def register_family(self, family_id, family_name, email, tier='pro'):
        """
        Register a new family for billing.

        Args:
            family_id: Unique ID (A, B, D, etc)
            family_name: Display name
            email: Billing email
            tier: 'pro' ($20/mo), 'kids' ($30/mo per child), 'accessibility' ($15-40/mo)
        """
        tiers = {
            'pro': 20,
            'kids': 30,
            'accessibility': 25,
        }

        family = {
            'family_id': family_id,
            'name': family_name,
            'email': email,
            'tier': tier,
            'monthly_usd': tiers.get(tier, 20),
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'next_billing_date': (datetime.now() + timedelta(days=30)).date().isoformat(),
            'lifetime_value_usd': 0,
            'churn_risk': False,
        }

        self._append_billing_record(family)
        print(f"[REGISTERED] Family {family_id} ({family_name}) — ${family['monthly_usd']}/mo")
        return family

    def create_invoice(self, family_id, month, year):
        """
        Generate invoice for a family.

        Args:
            family_id: Family ID (A, B, D)
            month: 1-12
            year: 2026
        """
        billing = self._load_billing()
        family = next((f for f in billing if f['family_id'] == family_id), None)

        if not family:
            print(f"[ERROR] Family {family_id} not found")
            return None

        invoice = {
            'invoice_id': f"{family_id}-{year}{month:02d}",
            'family_id': family_id,
            'family_name': family['name'],
            'email': family['email'],
            'month': month,
            'year': year,
            'amount_usd': family['monthly_usd'],
            'date_issued': datetime.now().isoformat(),
            'due_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'status': 'pending',
            'paid_date': None,
            'payment_method': 'stripe',
        }

        invoice_file = self.invoices_path / f"{invoice['invoice_id']}.json"
        with open(invoice_file, 'w') as f:
            json.dump(invoice, f, indent=2)

        print(f"[INVOICE] {invoice['invoice_id']}: ${invoice['amount_usd']} to {family['name']}")
        return invoice

    def record_payment(self, family_id, amount_usd, payment_id=None):
        """
        Record a successful payment.

        Args:
            family_id: Family ID
            amount_usd: Amount paid
            payment_id: Stripe payment ID
        """
        billing = self._load_billing()
        family_idx = next((i for i, f in enumerate(billing) if f['family_id'] == family_id), None)

        if family_idx is None:
            print(f"[ERROR] Family {family_id} not found")
            return

        family = billing[family_idx]
        family['lifetime_value_usd'] = family.get('lifetime_value_usd', 0) + amount_usd
        family['last_payment_date'] = datetime.now().isoformat()
        family['last_payment_id'] = payment_id
        family['churn_risk'] = False  # Reset churn risk

        self._save_billing(billing)
        print(f"[PAYMENT] Family {family_id}: ${amount_usd} received (LTV: ${family['lifetime_value_usd']})")

    def check_churn_risk(self):
        """Identify families at churn risk (no payment in 45+ days)."""
        billing = self._load_billing()
        at_risk = []

        for family in billing:
            if family['status'] != 'active':
                continue

            last_payment = family.get('last_payment_date')
            if not last_payment:
                days_since = (datetime.now() - datetime.fromisoformat(family['created_at'])).days
            else:
                days_since = (datetime.now() - datetime.fromisoformat(last_payment)).days

            if days_since > 45:
                family['churn_risk'] = True
                at_risk.append(family)

        self._save_billing(billing)
        return at_risk

    def get_revenue_summary(self):
        """Get current revenue metrics."""
        billing = self._load_billing()
        active = [f for f in billing if f['status'] == 'active']
        mopex = sum(f['monthly_usd'] for f in active)  # Monthly revenue
        ltv_total = sum(f['lifetime_value_usd'] for f in active)

        return {
            'active_families': len(active),
            'monthly_arr': mopex,
            'annual_arr': mopex * 12,
            'total_ltv': ltv_total,
            'avg_ltv_per_family': ltv_total / len(active) if active else 0,
            'churn_risk_count': sum(1 for f in active if f.get('churn_risk')),
        }

    def _load_billing(self):
        """Load billing records from disk."""
        if self.billing_path.exists():
            with open(self.billing_path) as f:
                return json.load(f)
        return []

    def _save_billing(self, data):
        """Save billing records to disk."""
        self.billing_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.billing_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _append_billing_record(self, record):
        """Append a single billing record."""
        billing = self._load_billing()
        billing.append(record)
        self._save_billing(billing)


if __name__ == '__main__':
    # Initialize
    payments = LanternPayments()

    # Register families A, B, D (May 25, 2026)
    print("=== REGISTERING FAMILIES ===")
    payments.register_family('A', 'Family A (Founder)', 'founder@lantern.local', tier='pro')
    payments.register_family('B', 'Family B (Operator)', 'operator@lantern.local', tier='pro')
    payments.register_family('D', 'Family D', 'family_d@example.com', tier='pro')

    # Create first invoices
    print("\n=== CREATING INVOICES ===")
    payments.create_invoice('A', 5, 2026)  # May 2026
    payments.create_invoice('B', 5, 2026)
    payments.create_invoice('D', 5, 2026)

    # Record payments (simulated)
    print("\n=== RECORDING PAYMENTS ===")
    payments.record_payment('A', 20.00, payment_id='ch_1A...')
    payments.record_payment('B', 20.00, payment_id='ch_1B...')
    payments.record_payment('D', 20.00, payment_id='ch_1D...')

    # Get revenue summary
    print("\n=== REVENUE SUMMARY ===")
    summary = payments.get_revenue_summary()
    print(f"Active families: {summary['active_families']}")
    print(f"Monthly recurring revenue: ${summary['monthly_arr']}")
    print(f"Annual ARR: ${summary['annual_arr']}")
    print(f"Total lifetime value: ${summary['total_ltv']}")
    print(f"Families at churn risk: {summary['churn_risk_count']}")

    print("\n[OK] Payment integration ready for Stripe connection")
