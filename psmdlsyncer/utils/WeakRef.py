import weakref as wr
def weak_reference(obj):
    """
    MAKES A WEAK REFERENCE
    """
    return wr.ref(obj)
