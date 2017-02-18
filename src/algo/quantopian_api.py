class QuantopianAPI:
    """
    Quantopian has some globals that we can use to place orders, get
    fundamentals, etc, etc.  The problem is that when we have unit or local
    tests, we don't have those things.  So we access those global things via
    this API object.  In a test, we can simulate (mock) this object, and when
    running quantopian, we use this class to access the globals.
    """
    def __init__():
        self.fundamentals = fundamentals

    def order(*args, **kwargs):
        return order(*args, **kwargs):

    def order_target(*args, **kwargs):
        return order_target(*args, **kwargs):

    def get_fundamentals(*args, **kwargs):
        return get_fundamentals(*args, **kwargs):

    def query(*args, **kwargs):
        return query(*args, **kwargs):

    def get_datetime(*args, **kwargs):
        return get_datetime(*args, **kwargs):

    def record(*args, **kwargs):
        return record(*args, **kwargs):
