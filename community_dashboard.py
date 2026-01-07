"""
Dummy Community Dashboard for satisfying legacy tests.
"""
class CommunityDatabase:
    def __init__(self, db_path=None):
        pass

class CommunityDashboard:
    def __init__(self):
        self.db = CommunityDatabase()
