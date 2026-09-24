class BankError(Exception):
    """Base exception for banking operations."""


class InvalidAmountError(BankError):
    pass


class InsufficientFundsError(BankError):
    pass


class AccountNotFoundError(BankError):
    pass


class DuplicateEmailError(BankError):
    pass


class SameAccountTransferError(BankError):
    pass
