#!/usr/bin/env python3
"""BetterSafe Social Services — Eligibility matching (local only)"""

import logging
import json

logger = logging.getLogger('BetterSafe.SocialServices')


class SocialServicesEligibility:
    """Match users to eligible social services."""

    def __init__(self, db, config):
        self.db = db
        self.config = config
        logger.info("Social Services Eligibility initialized")

    def find_eligible_services(self, user_profile):
        """
        Find eligible services based on user profile.

        Args:
            user_profile: {
                'age': int,
                'income_annual': float,
                'county': str,
                'disability': bool,
                'employment_status': str
            }

        Returns:
            List of eligible services with match scores
        """
        eligible = []

        self.db.cursor.execute('SELECT * FROM social_services_registry WHERE is_active = 1')
        services = self.db.cursor.fetchall()

        for service in services:
            match_score = self._score_match(user_profile, service)
            if match_score >= 2:  # At least 2 criteria match
                eligible.append({
                    'service_name': service[1],
                    'category': service[2],
                    'phone': service[5],
                    'website': service[6],
                    'match_score': match_score,
                    'programs': json.loads(service[8])
                })

        logger.info(f"Found {len(eligible)} eligible services for user")
        return eligible

    def _score_match(self, user_profile, service):
        """Score how well user matches service criteria."""
        score = 0

        # Parse eligibility criteria
        try:
            criteria = json.loads(service[7])
        except:
            criteria = {}

        # Age check
        if criteria.get('age_min') is not None:
            if user_profile['age'] >= criteria['age_min']:
                score += 1

        # Income check
        if criteria.get('income_based'):
            # Placeholder: real implementation would parse threshold
            if user_profile.get('income_annual', 0) < 50000:
                score += 1

        # County check
        if service[3] == user_profile.get('county'):
            score += 1

        return score

    def get_service_by_id(self, service_id):
        """Get details for a specific service."""
        return self.db.get_by_id('social_services_registry', service_id)

    def get_all_services(self, county=None, category=None):
        """Get all services, optionally filtered."""
        self.db.cursor.execute('SELECT * FROM social_services_registry WHERE is_active = 1')
        services = self.db.cursor.fetchall()

        if county:
            services = [s for s in services if s[3] == county]

        if category:
            services = [s for s in services if s[2] == category]

        return services
