import bokeh.plotting
import bokeh.models
import datetime as dt
from functools import partial


class Observer(object):
    def __init__(self, method):
        self.method = method

    def notify(self, value):
        return self.method(value)


class Stream(object):
    def __init__(self):
        self.subscribers = []

    def register(self, subscriber):
        self.subscribers.append(subscriber)

    def subscribe(self, method):
        self.subscribers.append(Observer(method))

    def emit(self, value):
        for subscriber in self.subscribers:
            subscriber.notify(value)

    def map(self, transform):
        return Map(self, transform)

    def scan(self, initial, combine):
        return Scan(self, initial, combine)

    def filter(self, criteria):
        return Filter(self, criteria)

    def unique(self):
        return Unique(self)

    def log(self):
        return Log(self)


class Log(Stream):
    def __init__(self, stream):
        stream.register(self)
        super().__init__()

    def notify(self, value):
        print(value)
        self.emit(value)


class Combine(Stream):
    def __init__(self, *streams):
        for stream in streams:
            stream.register(self)
        super().__init__()

    def notify(self, value):
        self.emit(value)


class CombineLatest(Stream):
    def __init__(self, *streams):
        self.state = []
        def indexed_calls(i):
            def wrapped(x):
                return (i, x)
            return wrapped
        for i, stream in enumerate(streams):
            stream.map(indexed_calls(i)).register(self)
            self.state.append(None)
        super().__init__()

    def notify(self, indexed_value):
        index, value = indexed_value
        state = list(self.state)
        state[index] = value
        self.state = tuple(state)
        self.emit(self.state)


class Map(Stream):
    def __init__(self, stream, transform):
        stream.register(self)
        self.transform = transform
        super().__init__()

    def notify(self, value):
        self.emit(self.transform(value))


class Scan(Stream):
    def __init__(self, stream, initial, combine):
        self.state = initial
        self.combine = combine
        stream.register(self)
        super().__init__()

    def notify(self, value):
        self.state = self.combine(self.state, value)
        self.emit(self.state)


class Filter(Stream):
    def __init__(self, stream, criteria):
        self.criteria = criteria
        stream.register(self)
        super().__init__()

    def notify(self, value):
        if not self.criteria(value):
            self.emit(value)


class Unique(Stream):
    def __init__(self, stream):
        stream.register(self)
        super().__init__()

    def notify(self, value):
        if not hasattr(self, 'current'):
            self.current = value
            self.emit(value)
        elif value != self.current:
            self.current = value
            self.emit(value)


def to_text(number):
    return "Index: {}".format(number)


def format_time(time):
    return "{:%Y%m%d %H:%M}".format(time)


def bounded_sum(minimum, maximum, total, value):
    if (total + value) >= maximum:
        return total
    if (total + value) < minimum:
        return total
    return total + value


def plus_button(stream):
    btn = bokeh.models.Button(label="+")
    btn.on_click(lambda: stream.emit(+1))
    return btn


def minus_button(stream):
    btn = bokeh.models.Button(label="-")
    btn.on_click(lambda: stream.emit(-1))
    return btn


def render(widget, value):
    widget.text = value


def combine(*streams):
    return Combine(*streams)


def combine_latest(*streams):
    return CombineLatest(*streams)


def forecast_label(time, hours):
    return "{:%Y-%m-%d %H:%M} T{:+}".format(time, hours)


def real_time(run_time, hours):
    return run_time + dt.timedelta(hours=hours)


def main():
    times = [dt.datetime(2018, 1, 1),
             dt.datetime(2018, 1, 2),
             dt.datetime(2018, 1, 3)]
    hours = [0, 3, 6, 9, 12, 15, 18, 21]

    time_index_p = bokeh.models.widgets.Paragraph(text="")
    time_p = bokeh.models.widgets.Paragraph(text="")
    hours_index_p = bokeh.models.widgets.Paragraph(text="")
    hours_p = bokeh.models.widgets.Paragraph(text="")
    label_p = bokeh.models.widgets.Paragraph(text="")
    real_time_p = bokeh.models.widgets.Paragraph(text="")
    buttons = []

    # Functional reactive programming style UI
    stream = Stream()
    time_clicks = stream
    index = stream.scan(0, partial(bounded_sum, 0, len(times))).unique()
    labels = index.map(to_text)
    labels.subscribe(partial(render, time_index_p))
    time_stream = index.map(partial(list.__getitem__, times))
    time_stream.map(format_time).subscribe(partial(render, time_p))
    buttons.append([plus_button(stream),
                    minus_button(stream)])

    stream = Stream()
    hour_clicks = stream
    index = stream.scan(0, partial(bounded_sum, 0, len(hours))).unique()
    index.map(to_text).subscribe(partial(render, hours_index_p))
    hour_stream = index.map(partial(list.__getitem__, hours))
    hour_stream.map(str).subscribe(partial(render, hours_p))
    buttons.append([plus_button(stream),
                    minus_button(stream)])

    stream = combine_latest(time_stream, hour_stream)
    stream = stream.filter(lambda args: any([a is None for a in args]))
    forecasts = stream.map(lambda args: forecast_label(*args))
    forecasts.subscribe(partial(render, label_p))

    real_times = stream.map(lambda args: real_time(*args))
    real_times.map(str).subscribe(partial(render, real_time_p))

    time_clicks.emit(0)
    hour_clicks.emit(0)

    document = bokeh.plotting.curdoc()
    document.add_root(bokeh.layouts.row(label_p))
    document.add_root(bokeh.layouts.row(real_time_p))
    document.add_root(bokeh.layouts.row(time_index_p, time_p))
    document.add_root(bokeh.layouts.row(hours_index_p, hours_p))
    for plus_btn, minus_btn in buttons:
        document.add_root(bokeh.layouts.row(plus_btn, minus_btn))


if __name__ == '__main__' or __name__.startswith("bk"):
    main()
