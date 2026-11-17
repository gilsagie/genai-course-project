class Job:
    def __init__(self, title, description=None):
        self.title = title
        self.description = description
    
    def set_title(self, title):
        self.title = title

    def set_description(self, description):
        self.description = description
