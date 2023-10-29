from typing import Any

from context import Context

import util


def format_table(context: Context, buffer: list[str], data: Any):
    strings = data['strings']
    columns = int(data['columns']) + 1
    legend = data['legend']

    # First, collapse 'strings' into a header and content row
    util.require(len(strings) % columns == 0, 'Data should divide columns, got %d len and %d columns' % (len(strings), columns))

    rows = len(strings) // columns

    util.require(rows > 1, 'Should have > 1 rows, got %d' % rows)

    headers = strings[:columns]
    body = [strings[i * columns:(i + 1) * columns] for i in range(1, rows)]

    # Title + text
    context.format_title(buffer, data)
    context.format_text(buffer, data)

    if legend:
        buffer.append('<div class="row"><div class="col-md-9">')

    # Build the HTML table
    buffer.append('<figure class="table-figure"><table><thead><tr>')
    for header in headers:
        buffer.append(get_component(header, key='th'))
    buffer.append('</tr></thead><tbody>')
    for row in body:
        buffer.append('<tr>')
        for td in row:
            buffer.append(get_component(td, key='td'))
        buffer.append('</tr>')
    buffer.append('</tbody></table></figure>')

    if legend:
        buffer.append('</div><div class="col-md-3"><h4>Legend</h4>')
        for entry in legend:
            # These are just a color square followed by a name
            buffer.append("""
            <div class="item-header">
                <span style="background-color:#%s"></span>
                <p>%s</p>
            </div>
            """ % (entry['color'][2:], entry['text']))
        buffer.append('</div></div>')


def get_component(th: Any, key: str):
    if 'fill' in th:  # Solid fill
        return '<%s style="background-color:#%s;"></%s>' % (key, th['fill'][2:], key)

    text = th['text']
    if text == '':  # Empty
        return '<%s></%s>' % (key, key)

    return '<%s><p>%s</p></%s>' % (key, text, key)
