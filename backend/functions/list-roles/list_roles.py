"""
GET /roles: the target roles in the KB for the role picker
"""

from kerjaready_shared.api_handler import api_handler
from kerjaready_shared.data_api import run_query

@api_handler
def handler(event, user):
    roles = run_query("SELECT role_id, title FROM roles ORDER BY title")
    return 200, {"roles": roles}
