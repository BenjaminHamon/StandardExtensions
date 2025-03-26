__product__ = None
__copyright__ = None
__version__ = None
__date__ = None


try:
    import benjaminhamon_standard_extensions.__metadata__ # type: ignore

    # pylint: disable = no-member
    __product__ = benjaminhamon_standard_extensions.__metadata__.__product__
    __copyright__ = benjaminhamon_standard_extensions.__metadata__.__copyright__
    __version__ = benjaminhamon_standard_extensions.__metadata__.__version__
    __date__ = benjaminhamon_standard_extensions.__metadata__.__date__
    # pylint: enable = no-member

except ImportError:
    pass
