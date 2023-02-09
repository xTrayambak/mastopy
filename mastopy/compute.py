from multiprocessing.pool import ThreadPool


compute_pool = ThreadPool(4)


def compute(fn: callable):
    """
    Run a Python function on another CPU core.
    """
    def inner(*args, **kwargs):
        return compute_pool.apply_async(fn, args=(*args,)).get()

    return inner
