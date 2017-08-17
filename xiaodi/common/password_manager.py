# coding=utf-8
from passlib.hash import md5_crypt


class WrongOldPasswordError(Exception):
    pass


class PasswordManager(object):
    @staticmethod
    def encrypt(password):
        return md5_crypt.encrypt(password)

    @staticmethod
    def verify_password(password, password_hash):
        if md5_crypt.verify(password, password_hash):
            return True
        else:
            return False

    def change_password(self, user, old, new):
        if not self.verify_password(old, user.password):
            raise WrongOldPasswordError

        user.password = new
        return user

    def forget_password(self, user, password):
        user.password = self.encrypt(password)
        return user

password_manager = PasswordManager()