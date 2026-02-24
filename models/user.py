class ClientAccount:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.status = "offline"
        self.friends = set()
        self.permissions = set()
        self.message_history = {}
    
    def add_friend(self, friend_username):
        self.friends.add(friend_username)
    
    def remove_friend(self, friend_username):
        self.friends.discard(friend_username)
    
    def add_permission(self, permission):
        self.permissions.add(permission)

    def remove_permission(self, permission):
        self.permissions.discard(permission)
    
    def set_status(self, status):
        self.status = status

    def show_info(self):
        return {
            "username": self.username,
            "status": self.status,
            "friends": list(self.friends),
            "permissions": list(self.permissions)
        }
    def add_message_to_history(self, friend_username, message):
        pass
