# Social Services Registry — Waynesville & Spring Valley, Ohio

**Data Source:** Public service directories (health departments, school districts, social services)  
**Storage:** Local JSON + SQLite (no external API calls)  
**Updated:** 2026-05-25  
**Scope:** Wayne County (Waynesville) & Greene County (Spring Valley)

---

## Registry Structure

### Service Categories

#### 1. Health & Medical
- **County Health Department** (primary care coordination)
- **Medicaid office** (income-based health insurance)
- **Mental health services** (counseling, therapy, crisis support)
- **Senior health** (Medicare counseling, wellness programs)
- **Maternal/child health** (WIC, prenatal, pediatric)

#### 2. Education & Schools
- **School District Office** (enrollment, special education, free lunch)
- **Adult Education** (GED, vocational training)
- **Public Library** (community resources, internet access)

#### 3. Disability & Accessibility
- **Vocational Rehabilitation** (job training for people with disabilities)
- **Developmental Disabilities Services** (day programs, residential support)
- **Assistive Technology Center** (devices, training)

#### 4. Senior Services
- **Area Agency on Aging** (meals on wheels, transportation, senior center)
- **AARP Local** (benefits counseling, community programs)

#### 5. Family & Children
- **Child & Family Services** (child protection, family support)
- **Foster Care & Adoption** (placement services)
- **Child Care Assistance** (subsidies for working families)

#### 6. Food & Nutrition
- **SNAP (Food Stamps)** (income-based food assistance)
- **WIC** (women, infants, children nutrition)
- **Food Pantries** (emergency food, local organizations)
- **Meals on Wheels** (hot meals for seniors/homebound)

#### 7. Housing & Homeless Services
- **Housing Assistance** (rental subsidies, emergency housing)
- **Homeless Services** (shelter, case management)
- **Housing Authority** (public housing, wait lists)

#### 8. Employment & Training
- **Job Center** (job search, resume help, training)
- **Unemployment Insurance** (claims, benefits)
- **Workforce Development** (skills training, apprenticeships)

#### 9. Utilities & Basic Services
- **LIHEAP** (heating/cooling assistance)
- **Water Assistance Programs** (bill reduction)
- **Phone Assistance** (Lifeline program)

---

## Sample Registry Entries (JSON format)

```json
{
  "services": [
    {
      "id": "waynesville_health_001",
      "name": "Wayne County Health Department",
      "category": "Health & Medical",
      "county": "Wayne",
      "city": "Waynesville",
      "address": "[Local address, not shared here]",
      "phone": "[Public number]",
      "website": "wayne.oh.gov/health",
      "hours": "Mon-Fri 8:00-17:00",
      "programs": [
        "Primary care coordination",
        "Immunizations",
        "Disease investigation",
        "Health inspections",
        "Birth/death certificates"
      ],
      "eligibility": {
        "income_based": false,
        "age_min": 0,
        "age_max": null,
        "residency_required": "Wayne County",
        "citizenship_required": false
      },
      "application_method": "Walk-in or phone",
      "documents_needed": []
    },
    {
      "id": "waynesville_snap_001",
      "name": "SNAP (Food Assistance)",
      "category": "Food & Nutrition",
      "county": "Wayne",
      "city": "Waynesville",
      "phone": "[County DSS]",
      "website": "benefits.oh.gov/snap",
      "programs": [
        "Monthly food assistance benefits",
        "Emergency expedited SNAP"
      ],
      "eligibility": {
        "income_based": true,
        "income_threshold": "130% of federal poverty line",
        "asset_limit": 2500,
        "age_min": 0,
        "residency_required": "Ohio resident",
        "citizenship_required": "Yes (or eligible non-citizen)"
      },
      "application_method": "Online (OhioMeansJobs) or in-person",
      "documents_needed": [
        "Proof of income (recent pay stubs, tax return)",
        "Proof of identity (driver license, passport)",
        "Proof of residency (utility bill, lease)"
      ],
      "processing_time_days": 30,
      "emergency_expedited_days": 7
    },
    {
      "id": "springvalley_aging_001",
      "name": "Greene County Area Agency on Aging",
      "category": "Senior Services",
      "county": "Greene",
      "city": "Spring Valley",
      "phone": "[Public number]",
      "website": "greene.oh.gov/aging",
      "programs": [
        "Meals on Wheels",
        "Transportation assistance",
        "Senior center activities",
        "Caregiver support",
        "Benefits counseling"
      ],
      "eligibility": {
        "age_min": 60,
        "income_based": true,
        "income_threshold": "Optional sliding scale",
        "residency_required": "Greene County"
      },
      "application_method": "Phone or in-person",
      "documents_needed": [
        "Proof of age",
        "Proof of residency"
      ]
    }
  ]
}
```

---

## Eligibility Matching Algorithm

BetterSafe queries this registry and matches user against criteria:

```python
def find_eligible_services(user_profile):
    """
    user_profile = {
        'age': 72,
        'income_annual': 18000,
        'residency': 'Waynesville, OH',
        'disability': True,
        'num_children': 0,
        'employment_status': 'retired'
    }
    """
    eligible = []
    
    for service in registry['services']:
        match_score = 0
        
        # Check age
        if service['eligibility']['age_min'] is not None:
            if user_profile['age'] >= service['eligibility']['age_min']:
                match_score += 1
        
        # Check income
        if service['eligibility']['income_based']:
            threshold = service['eligibility']['income_threshold']
            if user_profile['income_annual'] <= threshold:
                match_score += 1
        
        # Check residency
        if user_profile['residency'] in service['eligibility']['residency_required']:
            match_score += 1
        
        if match_score >= 2:  # At least 2 criteria match
            eligible.append({
                'service': service['name'],
                'match_score': match_score,
                'next_steps': f"Call {service['phone']} or visit {service['website']}"
            })
    
    return eligible
```

---

## Data Entry Checklist

For each service, collect:

- [ ] Service name
- [ ] Category (from list above)
- [ ] County, City
- [ ] Phone (public number)
- [ ] Website/portal
- [ ] Hours of operation
- [ ] Programs offered (list)
- [ ] Eligibility criteria (age, income, residency, citizenship)
- [ ] Income threshold (if applicable, as % of federal poverty line)
- [ ] Application method (online, in-person, phone)
- [ ] Documents required
- [ ] Processing time (days)
- [ ] Notes (e.g., "Expedited option available")

---

## Implementation (Phase 1)

**Week 1:** Seed registry with:
- Wayne County Health Department
- Wayne County DSS (SNAP, LIHEAP, Medicaid)
- Waynesville School District
- Greene County Area Agency on Aging
- Spring Valley public services

**Week 2:** Add:
- Disability services (VR, developmental disabilities)
- Housing assistance programs
- Food pantries (local nonprofit partners)

**Week 3:** Expand:
- Employment services
- Utility assistance programs
- Community nonprofits (crisis support, etc)

---

## Privacy & Usage

- Registry is **public information only** (government websites)
- BetterSafe stores no user input beyond current session (unless user saves a bookmark)
- Eligibility matching is **local only** (no data sent anywhere)
- User can print or export eligibility results as PDF

---

## Status

**Current:** Schema defined, ready for data entry  
**Next:** Populate initial services (Week 1)  
**Owner:** TBD

---

## References

- Ohio Department of Job & Family Services (ODJFS): benefits.oh.gov
- Wayne County: wayne.oh.gov
- Greene County: greene.oh.gov
- Waynesville City: waynesville.oh.gov
- Spring Valley: springvalleyohio.gov
