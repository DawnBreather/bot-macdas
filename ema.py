def n_for_ema(period):
    return 2 / (period + 1)


def ema_update(element, period, prev):
    return round((n_for_ema(period) * float(element) + (1 - n_for_ema(period)) * float(prev)), 3)


def macd_update(fast, slow):
    return round((fast - slow), 3)


def macdas_update(element, prev_fast, prev_slow, prev_signal, signalas_prev, fast_period, slow_period, signal_period):
    fast_ma = ema_update(element, fast_period, prev_fast)
    slow_ma = ema_update(element, slow_period, prev_slow)
    macd_mas = macd_update(fast_ma, slow_ma)
    signal = ema_update(macd_mas, signal_period, prev_signal)
    histogram = macd_update(macd_mas, signal)

    signal_as = ema_update(histogram, signal_period, signalas_prev)
    result = {'histogram': histogram, "signal_as": signal_as, "fast": fast_ma,
              "slow": slow_ma, 'signal': signal}
    return result


def ema(massive, period):
    prev_element = 0
    res_massive = []
    for param in massive:
        if prev_element == 0:
            prev_element = param
            res_massive.append(param)
            continue
        else:
            new_param = round((n_for_ema(period) * param + (1 - n_for_ema(period)) * prev_element), 3)
            res_massive.append(new_param)
            prev_element = new_param
    return res_massive


def macd(fast, slow):
    pointer = 0
    macd_mas = []
    for item in fast:
        macd_mas.append(round((fast[pointer] - slow[pointer]), 3))
        pointer += 1
    return macd_mas


def macdas(mas, fast_period, slow_period, signal_period):
    fast_ma = ema(mas, fast_period)
    slow_ma = ema(mas, slow_period)
    macd_mas = macd(fast_ma, slow_ma)
    signal = ema(macd_mas, signal_period)
    histogram = macd(macd_mas, signal)

    signal_as = ema(histogram, signal_period)
    result = {'histogram': histogram[-2], "signal_as": signal_as[-2], "fast": fast_ma[-2],
              "slow": slow_ma[-2], 'signal': signal[-2]}
    return result

