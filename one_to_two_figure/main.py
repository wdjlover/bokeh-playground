import bokeh.plotting
import bokeh.models
import bokeh.layouts
import cartopy
import numpy as np
import datetime as dt
from functools import partial


def main():
    document = bokeh.plotting.curdoc()
    tile = bokeh.models.WMTSTileSource(
        url='http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png',
        attribution="Attribution text goes here"
    )

    x_range, y_range = google_mercator([-20, 20], [-5, 15])
    first = bokeh.plotting.figure(
        x_range=x_range,
        y_range=y_range,
        x_axis_type="mercator",
        y_axis_type="mercator",
        active_scroll="wheel_zoom")
    second = bokeh.plotting.figure(
        active_scroll="wheel_zoom",
        x_axis_type="mercator",
        y_axis_type="mercator",
        x_range=first.x_range,
        y_range=first.y_range)
    second.yaxis.visible = False
    figures = [
     first,
     second
    ]
    for f in figures:
        f.toolbar.logo = None
        f.toolbar_location = None
        f.add_tile(tile)

    zs = []
    nx, ny = 10, 10
    lons, lats = np.meshgrid(
            np.linspace(0, 10, nx),
            np.linspace(0, 10, ny))
    x, y = google_mercator(lons, lats)

    z = np.ma.arange(nx * ny, dtype=np.float).reshape(nx, ny).T
    z[:, ::2] = np.ma.masked
    source_1 = image_source(x, y, z)
    zs.append(z)

    z = np.ma.arange(nx * ny, dtype=np.float).reshape(nx, ny).T
    z[:, 1::2] = np.ma.masked
    source_2 = image_source(x, y, z)
    zs.append(z)

    low = min([z.min() for z in zs])
    high = max([z.max() for z in zs])
    color_mapper = bokeh.models.LinearColorMapper(
        palette=bokeh.palettes.Plasma[256],
        low=low,
        low_color="white",
        high=high,
        high_color="white",
        nan_color=bokeh.colors.RGB(0, 0, 0, a=0),
    )
    for f in figures:
        colorbar(f, color_mapper)

    first_glyph = plot_image(first, source_1, color_mapper)
    second_glyph = plot_image(first, source_2, color_mapper)
    third_glyph = plot_image(second, source_2, color_mapper)

    layout = bokeh.layouts.row(*figures, sizing_mode="stretch_both")
    layout.children = [figures[0]]  # Trick to keep correct sizing modes

    button = bokeh.models.Button()
    button.on_click(toggle(figures, layout, [second_glyph]))

    name_drop = bokeh.models.Dropdown(menu=[
        (k, k) for k in bokeh.palettes.mpl.keys()])
    size_drop = bokeh.models.Dropdown(menu=[])

    def label(drop):
        def on_change(attr, old, new):
            drop.label = new
        return on_change

    picker = Picker(color_mapper)
    name_drop.on_change('value', picker.change_name)
    name_drop.on_change('value', label(name_drop))
    size_drop.on_change('value', picker.change_size)
    size_drop.on_change('value', label(size_drop))

    def change_menu(drop):
        def on_change(attr, old, new):
            if hasattr(bokeh.palettes, new):
                drop.menu = [(str(k), str(k))
                        for k in getattr(bokeh.palettes, new).keys()]
        return on_change
    name_drop.on_change('value', change_menu(size_drop))

    min_input = bokeh.models.TextInput(value=str(low), title="Min:")
    min_input.on_change('value', change(color_mapper, "low"))
    color_mapper.on_change('low', change(min_input, "value", str))

    max_input = bokeh.models.TextInput(value=str(high), title="Max:")
    max_input.on_change('value', change(color_mapper, "high"))
    color_mapper.on_change('high', change(max_input, "value", str))

    def zoom(figure, color_mapper, lons, lats, zs):
        @debounce
        def on_change(attr, old, new):
            lon_range, lat_range = plate_carree(
                    [figure.x_range.start,
                     figure.x_range.end],
                    [figure.y_range.start,
                     figure.y_range.end])
            lon_start, lon_end = lon_range
            lat_start, lat_end = lat_range
            dlon = lons[0, 1] - lons[0, 0]
            dlat = lats[1, 0] - lats[0, 0]
            pts = np.where(
                    ((lons + dlon) >= lon_start) &
                    ((lons - dlon) <= lon_end) &
                    ((lats + dlat) >= lat_start) &
                    ((lats - dlat) <= lat_end))
            if len(pts[0]) > 0:
                low = min(z[pts].min() for z in zs)
                high = max(z[pts].max() for z in zs)
                print(low, high)
                color_mapper.low = low
                color_mapper.high = high
        return on_change
    figure = figures[0]
    on_change = zoom(figure, color_mapper, lons, lats, zs)
    figure.x_range.on_change('start', on_change)
    figure.x_range.on_change('end', on_change)
    figure.y_range.on_change('start', on_change)
    figure.y_range.on_change('end', on_change)

    document.add_root(layout)
    document.add_root(
            bokeh.layouts.column(
                bokeh.layouts.row(name_drop, size_drop, button),
                bokeh.layouts.row(min_input, max_input)))


def debounce(f, miliseconds=200):
    document = bokeh.plotting.curdoc()
    timeout_callback = None
    def wrapper(attr, old, new):
        nonlocal document
        nonlocal timeout_callback
        callback = partial(f, attr, old, new)
        if timeout_callback is not None:
            try:
                document.remove_timeout_callback(timeout_callback)
            except ValueError:
                pass
        timeout_callback = document.add_timeout_callback(
                callback,
                miliseconds)
    return wrapper


def throttle(f, seconds=1):
    miliseconds = 1000 * seconds
    last_time = None
    document = bokeh.plotting.curdoc()
    timeout_callback = None
    def wrapper(attr, old, new):
        nonlocal document
        nonlocal timeout_callback
        nonlocal last_time
        now = dt.datetime.now()
        callback = partial(f, attr, old, new)
        if (last_time is None) or ((now - last_time).total_seconds() > seconds):
            last_time = now
            if timeout_callback is not None:
                try:
                    document.remove_timeout_callback(timeout_callback)
                except ValueError:
                    pass
            timeout_callback = document.add_timeout_callback(
                    callback,
                    miliseconds)
    return wrapper


def change(widget, prop, dtype=float):
    def on_change(attr, old, new):
        setattr(widget, prop, dtype(new))
    return on_change


class Picker(object):
    def __init__(self, color_mapper):
        self.color_mapper = color_mapper
        self.name = "Viridis"
        self.size = 256

    def change_name(self, attr, old, new):
        self.name = new
        self.render()

    def change_size(self, attr, old, new):
        self.size = int(new)
        self.render()

    def render(self):
        if hasattr(bokeh.palettes, self.name):
            palettes = getattr(bokeh.palettes, self.name)
            if self.size in palettes:
                self.color_mapper.palette = palettes[self.size]


def google_mercator(lons, lats):
    gl = cartopy.crs.Mercator.GOOGLE
    pc = cartopy.crs.PlateCarree()
    x, y, _ = gl.transform_points(pc, flatten(lons), flatten(lats)).T
    return x, y


def plate_carree(x, y):
    gl = cartopy.crs.Mercator.GOOGLE
    pc = cartopy.crs.PlateCarree()
    lons, lats, _ = pc.transform_points(gl, flatten(x), flatten(y)).T
    return lons, lats


def flatten(a):
    if isinstance(a, list):
        a = np.array(a, dtype=np.float)
    return a.flatten()


def image_source(x, y, z):
    return bokeh.models.ColumnDataSource({
        "x": [x.min()],
        "y": [y.min()],
        "dw": [x.max() - x.min()],
        "dh": [y.max() - y.min()],
        "image": [z]
        })


def plot_image(figure, source, color_mapper):
    return figure.image(
        x="x",
        y="y",
        dw="dw",
        dh="dh",
        image="image",
        source=source,
        color_mapper=color_mapper
    )


def colorbar(figure, color_mapper):
    color_bar = bokeh.models.ColorBar(
        color_mapper=color_mapper,
        orientation='horizontal',
        background_fill_alpha=0,
        location='bottom_center',
        major_tick_line_color='black',
        bar_line_color='black',
        title='Title')
    figure.add_layout(color_bar, 'center')
    return color_bar


def toggle(figures, layout, glyphs):
    def render():
        if len(layout.children) == 1:
            layout.children = figures
            for glyph in glyphs:
                glyph.visible = False
        else:
            layout.children = [figures[0]]
            for glyph in glyphs:
                glyph.visible = True
    return render


if __name__.startswith('bk'):
    main()
