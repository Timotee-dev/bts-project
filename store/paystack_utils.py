"""
BTS Project — Paystack Utilities
Handles subaccount creation and payment split
"""
import urllib.request
import urllib.parse
import json
from django.conf import settings


PAYSTACK_BASE = 'https://api.paystack.co'
BTS_COMMISSION = 200000  # ₦2,000 in kobo


def _paystack_request(method, endpoint, data=None):
    """Make a Paystack API request."""
    url = f"{PAYSTACK_BASE}{endpoint}"
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f'[Paystack] {method} {endpoint} failed: {e.code} — {error_body}')
        return None
    except Exception as e:
        print(f'[Paystack] Request error: {e}')
        return None


def create_vendor_subaccount(vendor):
    """
    Create a Paystack subaccount for a vendor.
    Called when vendor registers with bank details.
    Returns the subaccount_code or None if it fails.
    """
    if not vendor.bank_name or not vendor.account_number or not vendor.account_name:
        return None

    # Resolve bank code from bank name
    bank_code = get_bank_code(vendor.bank_name)
    if not bank_code:
        print(f'[Paystack] Could not find bank code for: {vendor.bank_name}')
        return None

    data = {
        'business_name': vendor.business_name,
        'settlement_bank': bank_code,
        'account_number': vendor.account_number,
        'percentage_charge': 0,  # We use flat fee, not percentage
        'description': f'BTS Vendor: {vendor.business_name}',
    }

    result = _paystack_request('POST', '/subaccount', data)
    if result and result.get('status'):
        subaccount_code = result['data']['subaccount_code']
        print(f'[Paystack] Subaccount created for {vendor.business_name}: {subaccount_code}')
        return subaccount_code

    return None


def get_bank_code(bank_name):
    """
    Get Paystack bank code from bank name.
    Common Nigerian banks mapped for quick lookup.
    Falls back to API call if not found.
    """
    # Common Nigerian banks - covers most vendors
    BANK_CODES = {
        'access': '044', 'access bank': '044',
        'citibank': '023',
        'diamond': '063', 'diamond bank': '063',
        'ecobank': '050',
        'fidelity': '070', 'fidelity bank': '070',
        'fcmb': '214', 'first city': '214',
        'first bank': '011', 'firstbank': '011', 'fbn': '011',
        'gtbank': '058', 'gtb': '058', 'guaranty trust': '058', 'gt bank': '058',
        'heritage': '030', 'heritage bank': '030',
        'keystone': '082', 'keystone bank': '082',
        'kuda': '090267', 'kuda bank': '090267',
        'opay': '100004',
        'palmpay': '100033',
        'polaris': '076', 'polaris bank': '076',
        'providus': '101', 'providus bank': '101',
        'stanbic': '221', 'stanbic ibtc': '221',
        'standard chartered': '068',
        'sterling': '232', 'sterling bank': '232',
        'suntrust': '100',
        'titan': '102', 'titan trust': '102',
        'union': '032', 'union bank': '032',
        'uba': '033', 'united bank': '033',
        'unity': '215', 'unity bank': '215',
        'wema': '035', 'wema bank': '035',
        'zenith': '057', 'zenith bank': '057',
    }

    name_lower = bank_name.lower().strip()
    for key, code in BANK_CODES.items():
        if key in name_lower:
            return code

    # Fallback: query Paystack API for bank list
    result = _paystack_request('GET', '/bank?country=nigeria&perPage=100')
    if result and result.get('status'):
        for bank in result.get('data', []):
            if bank_name.lower() in bank['name'].lower():
                return bank['code']

    return None


def build_payment_split(vendor_subaccount_code, order_total_kobo):
    """
    Build Paystack split config:
    - BTS keeps ₦2,000 (flat)
    - Vendor gets the rest
    Returns split config dict for payment initialization.
    """
    if not vendor_subaccount_code:
        return None

    vendor_amount = max(0, order_total_kobo - BTS_COMMISSION)

    return {
        'type': 'flat',
        'currency': 'NGN',
        'subaccounts': [
            {
                'subaccount': vendor_subaccount_code,
                'share': vendor_amount,
            }
        ],
        'bearer_type': 'account',  # BTS account bears transaction fees
        'main_account_share': BTS_COMMISSION,
    }