import os


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.1-8b-instant"
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

ISSUE_TYPES = [
    "Delivery",
    "Returns and Refunds",
    "Billing",
    "Account Access",
    "Technical Support",
    "General Inquiry",
]

SUPPORT_KNOWLEDGE_BASE = [
    {
        "title": "Shipping and Delivery Policy",
        "category": "Delivery",
        "content": (
            "Standard shipping usually arrives within 3 to 5 business days after dispatch. "
            "Express shipping usually arrives within 1 to 2 business days after dispatch. "
            "Customers can request an address correction only before an order is packed. "
            "If tracking has not updated for 5 business days after dispatch, the case should be reviewed by support. "
            "If an order is delayed by more than 10 business days, human support should investigate the carrier and next steps."
        ),
    },
    {
        "title": "Returns and Refunds",
        "category": "Returns and Refunds",
        "content": (
            "Most physical products can be returned within 30 calendar days of delivery when they are unused and in the original packaging. "
            "Damaged or incorrect items reported within 7 days of delivery are eligible for replacement or refund review. "
            "Refunds are issued to the original payment method after the returned item is inspected. "
            "Bank processing normally takes 5 to 7 business days after the refund is approved. "
            "Digital items and final sale items are not eligible for standard returns."
        ),
    },
    {
        "title": "Billing and Subscription Policy",
        "category": "Billing",
        "content": (
            "Monthly and annual plans renew automatically on the listed renewal date unless the customer cancels before renewal. "
            "A cancellation stops future renewal and does not refund the current billing period unless an approved exception is recorded by support. "
            "Plan upgrades can start immediately and may create a prorated charge. "
            "Invoice resend requests can be handled by support when the customer email is verified. "
            "Duplicate charges, chargebacks, or disputed payments should be escalated to a human billing specialist."
        ),
    },
    {
        "title": "Account Access and Security",
        "category": "Account Access",
        "content": (
            "Customers who forget their password should use the password reset link sent to the verified email address. "
            "Accounts are temporarily locked for 30 minutes after 5 failed login attempts. "
            "Changing the login email or phone number requires identity verification. "
            "Support should never ask the customer to share one-time passwords or verification codes. "
            "Suspicious access, fraud, or takeover concerns must be escalated to a human security specialist."
        ),
    },
    {
        "title": "Technical Support Troubleshooting",
        "category": "Technical Support",
        "content": (
            "For app sync issues, ask the customer to sign out and sign back in, confirm they are using the latest app version, and retry on a stable internet connection. "
            "If data still does not sync after reinstalling the app and waiting 24 hours, the case should be escalated to technical support. "
            "For checkout errors, confirm the billing address, payment method status, and whether the problem happens on both web and mobile."
        ),
    },
    {
        "title": "Escalation Guidelines",
        "category": "General Inquiry",
        "content": (
            "Human support should take over when the request involves fraud, chargebacks, legal threats, repeated failed deliveries, or missing account verification data. "
            "Escalation is also appropriate when the knowledge base does not clearly confirm the next action or when a case requires manual account changes."
        ),
    },
]

CUSTOMER_RECORDS = {
    "CUST-1001": {
        "name": "TANISHKA JADHAV",
        "email": "tanishka.jadhav@example.com",
        "plan": "Premium Monthly",
        "account_status": "Active",
        "region": "Bengaluru",
        "preferred_channel": "Email",
        "renewal_date": "2026-05-03",
        "last_ticket": "Password reset request resolved on 2026-04-10.",
        "notes": "Prefers evening callbacks after 6 PM IST.",
        "orders": [
            {
                "order_id": "ORD-5012",
                "item": "Noise Cancelling Headphones",
                "status": "In Transit",
                "placed_on": "2026-04-18",
                "delivery_date": "Expected by 2026-04-24",
                "amount": "$129.00",
            },
            {
                "order_id": "ORD-4988",
                "item": "USB-C Dock",
                "status": "Delivered",
                "placed_on": "2026-03-29",
                "delivery_date": "Delivered on 2026-04-02",
                "amount": "$79.00",
            },
        ],
    },
    "CUST-1002": {
        "name": "Nitisha Naigoankar",
        "email": "nitisha.naigoankar@example.com",
        "plan": "Standard Annual",
        "account_status": "Active",
        "region": "Pune",
        "preferred_channel": "Chat",
        "renewal_date": "2027-01-14",
        "last_ticket": "Refund status question answered on 2026-04-07.",
        "notes": "Asked for proactive shipping notifications on future orders.",
        "orders": [
            {
                "order_id": "ORD-4877",
                "item": "Smart Fitness Watch",
                "status": "Refund Under Review",
                "placed_on": "2026-03-11",
                "delivery_date": "Delivered on 2026-03-15",
                "amount": "$199.00",
            },
            {
                "order_id": "ORD-4820",
                "item": "Replacement Charging Cable",
                "status": "Delivered",
                "placed_on": "2026-02-25",
                "delivery_date": "Delivered on 2026-02-28",
                "amount": "$19.00",
            },
        ],
    },
    "CUST-1003": {
        "name": "Disha Patil",
        "email": "disha.patil@example.com",
        "plan": "Business Monthly",
        "account_status": "Login Locked",
        "region": "Hyderabad",
        "preferred_channel": "Phone",
        "renewal_date": "2026-04-30",
        "last_ticket": "Two-factor authentication setup completed on 2026-04-03.",
        "notes": "Needs invoice copies sent to finance@acme-example.com after verification.",
        "orders": [
            {
                "order_id": "ORD-5091",
                "item": "Team Collaboration License",
                "status": "Active Subscription",
                "placed_on": "2026-04-01",
                "delivery_date": "Digital access granted on 2026-04-01",
                "amount": "$349.00",
            }
        ],
    },
}
