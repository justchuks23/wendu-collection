"""Authentication serializers are configured in the user API views.

Keep explicit field allowlists for any user-facing serializers. Never expose
permission, role, or staff fields as writable customer data.
"""
