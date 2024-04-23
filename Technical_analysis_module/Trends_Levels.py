def levels(self, ):
    """pivot point and support/resistance levels"""
    high = round(self.df["High"].iloc[-1], 2)
    low = round(self.df["Low"].iloc[-1], 2)
    close = round(self.df["Close"].iloc[-1], 2)
    pivot = round((high + low + close) / 3, 2)
    r1 = round((2 * pivot - low), 2)
    r2 = round((pivot + (high - low)), 2)
    r3 = round((high + 2 * (pivot - low)), 2)
    s1 = round((2 * pivot - high), 2)
    s2 = round((pivot - (high - low)), 2)
    s3 = round((low - 2 * (high - pivot)), 2)
    return (pivot, r1, r2, r3, s1, s2, s3)