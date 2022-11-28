# @property doesn't work with static methods, but this simple decorator does
class staticproperty(property):
    def __get__(self, cls, owner):
        return self.fget()
