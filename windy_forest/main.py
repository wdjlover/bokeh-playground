#!/usr/bin/env python3
import bokeh.io
import bokeh.plotting
import bokeh.models.callbacks

def main(bokeh_id):
    """Main program"""
    figure = bokeh.plotting.figure(sizing_mode="stretch_both", match_aspect=True)

    windy_forest(figure)

    if bokeh_id == '__main__':
        bokeh.plotting.show(figure)
    else:
        bokeh.io.curdoc().add_root(figure)


def windy_forest(figure):
    left_source = bokeh.models.ColumnDataSource({
        "x": [1, 2, 3],
        "y": [1, 2, 3],
        "width": [1, 1, 1],
        "alpha": [1, 1, 1]
    })
    left_renderer = figure.rect(x="x",
                                y="y",
                                width="width",
                                height=1,
                                color="blue",
                                alpha="alpha",
                                source=left_source)
    hover_tool = hover_tool_hide(left_source, side="right")
    figure.add_tools(hover_tool)
    right_source = bokeh.models.ColumnDataSource({
        "x": [1, 2, 3],
        "y": [3, 2, 1],
        "width": [0.5, 0.5, 0.5],
        "alpha": [1, 1, 1]
    })
    right_renderer = figure.rect(x="x",
                                 y="y",
                                 width="width",
                                 height=0.5,
                                 color="red",
                                 alpha="alpha",
                                 source=right_source)
    hover_tool = hover_tool_hide(right_source, side="left")
    figure.add_tools(hover_tool)
    vertical_line(figure)

def hover_tool_hide(source, side="left"):
    """Hide anything to the left/right of pointer

    At the moment this is achieved through the use of CustomJS and
    alpha values. A more complete solution would work on the canvas
    itself
    """
    code_template = """
        let x_left, x_right;
        let x = source.data["x"];
        let width = source.data["width"];
        let mouse_x = cb_data.geometry.x;
        let alpha = [];
        for (let i=0; i<x.length; i++) {
            x_left = x[i] - (width[i] / 2);
            x_right = x[i] + (width[i] / 2);
            if (%s) {
               alpha.push(0);
            } else {
               alpha.push(1);
            }
        }
        source.data.alpha = alpha;
        source.change.emit();
    """
    if side.lower() == "left":
        code = code_template % "mouse_x < x_right"
    else:
        code = code_template % "mouse_x > x_left"
    callback = bokeh.models.callbacks.CustomJS(args=dict(source=source),
                                               code=code)
    return bokeh.models.HoverTool(callback=callback)


def vertical_line(figure):
    """Add vertical Span that follows mouse pointer"""
    span = bokeh.models.Span(location=0, dimension='height', line_color='black', line_width=1)
    figure.renderers.append(span)
    callback = bokeh.models.callbacks.CustomJS(args=dict(span=span), code="""
        span.location = cb_data.geometry.x;
    """)
    hover_tool = bokeh.models.HoverTool(callback=callback)
    figure.add_tools(hover_tool)


main(__name__)
