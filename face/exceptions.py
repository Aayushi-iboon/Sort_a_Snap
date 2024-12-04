class CustomError(Exception):
    def __init__(self, message, code=None):
        print("---",message)
        self.message = message
        self.code = code
        super().__init__(self.message)