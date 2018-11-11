import matplotlib.pyplot as plt
import matplotlib.quiver
import numpy as np
import bokeh.plotting
import custom
import time


def timed(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        duration = end - start
        print('function {} ran for {} seconds'.format(
            str(func), duration))
        return result
    return wrapper

figure = bokeh.plotting.figure(
        match_aspect=True,
        sizing_mode="stretch_both")

ax = plt.gca()
angle = 30

X = np.arange(-10, 10, 1, dtype="d")
Y = np.arange(-10, 10, 1, dtype="d")
U, V = np.meshgrid(X**2, Y**2)

mpl_barbs = matplotlib.quiver.Barbs(ax, X, Y, U, V)

@timed
def bokeh_barbs(mpl_barb):
    """Convert matplotlib.quiver.Barbs to bokeh multiline/patches data"""
    xo, yo = mpl_barb.get_offsets().T
    paths = mpl_barb.get_paths()
    xs, ys = [], []
    for path in paths:
        x, y = path.vertices.T
        xs.append(x)
        ys.append(y)
    return xo, yo, xs, ys

x, y, a, b = bokeh_barbs(mpl_barbs)
glyph = custom.Barbs(
        x="x",
        y="y",
        a="a",
        b="b",
        size=10)
source = bokeh.models.ColumnDataSource(dict(
        x=x,
        y=y,
        a=a,
        b=b,
    ))
figure.add_glyph(source, glyph)

# Demonstrate click/change barbs
def on_click():
    X = np.arange(-10, 10, 1)
    Y = np.arange(-10, 10, 1)
    U, V = np.meshgrid(-X**2, Y)
    mpl_barbs = matplotlib.quiver.Barbs(ax, X, Y, U, V)
    x, y, a, b = bokeh_barbs(mpl_barbs)
    source.data = {
        "x": x,
        "y": y,
        "a": a,
        "b": b,
    }


@timed
def rotate():
    global X, Y, U, V, source
    angle = np.rad2deg(np.arctan2(V, U))
    angle += 5
    C = np.sqrt(U**2 + V**2)
    U = C * np.cos(np.deg2rad(angle))
    V = C * np.sin(np.deg2rad(angle))
    ax = plt.gca()
    n, m = 10, 10
    mpl_barbs = matplotlib.quiver.Barbs(ax,
            X[:m],
            Y[:n],
            U[:n, :m],
            V[:n, :m])
    x, y, a, b = bokeh_barbs(mpl_barbs)
    source.data = {
        "x": x,
        "y": y,
        "a": a,
        "b": b,
    }

button = bokeh.models.Button(label="Change barbs")
button.on_click(on_click)

document = bokeh.plotting.curdoc()
document.add_root(button)
document.add_root(figure)
document.add_periodic_callback(rotate, 50)
