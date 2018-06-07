#!/usr/bin/env python3
import bokeh.io
import bokeh.plotting
import bokeh.models.callbacks

def main(bokeh_id):
    print("Hello, Bokeh!")
    figure = bokeh.plotting.figure(sizing_mode="stretch_both", match_aspect=True)
    vertical_line(figure)

    if bokeh_id == '__main__':
        bokeh.plotting.show(figure)
    else:
        bokeh.io.curdoc().add_root(figure)

def vertical_line(figure):
    """Make CustomJS callback to draw vertical line centered on mouse"""
    source = bokeh.models.ColumnDataSource({
        "x": [0, 1],
        "y": [0, 1]
    })
    renderer = figure.line(x="x", y="y", source=source)
    callback = bokeh.models.callbacks.CustomJS(args=dict(source=source, figure=figure), code="""
        // Get access to ColumnDataSource
        var data = source.data;

        // Get access to HoverTool data
        var geometry = cb_data['geometry'];

        console.log(figure);
        data['x'] = [geometry.x, geometry.x];
        data['y'] = [figure.attributes.y_range.attributes.start,
                     figure.attributes.y_range.attributes.end];

        // Update plot relative to updated ColumnDataSource
        source.change.emit();
    """)
    tool = bokeh.models.HoverTool(callback=callback)
    figure.add_tools(tool)

def moving_circle(figure):
    """Make CustomJS callback to move circle underneath mouse"""
    source = bokeh.models.ColumnDataSource({
        "x": [0],
        "y": [0]
    })
    renderer = figure.circle(x="x", y="y", source=source)
    callback = bokeh.models.callbacks.CustomJS(args=dict(source=source), code="""
        var data = source.data;
        var geometry = cb_data['geometry'];
        data['x'][0] = geometry.x;
        data['y'][0] = geometry.y;
        source.change.emit();
    """)
    tool = bokeh.models.HoverTool(callback=callback)
    figure.add_tools(tool)

def windy_forest(figure):
    left_renderer = figure.rect([1, 2, 3], [1, 2, 3], width=1, height=1,
                                color="blue")
    right_renderer = figure.rect([1, 2, 3], [3, 2, 1], width=0.5, height=0.5,
                                 color="red")
    callback = bokeh.models.callbacks.CustomJS(code="""
        console.log(cb_obj.value);
    """)
    hover_tool = bokeh.models.HoverTool(callback=callback)
    figure.add_tools(hover_tool)


main(__name__)
