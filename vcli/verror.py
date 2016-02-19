import re


RE_MESSAGE = re.compile(r'Message: (.+), Sqlstate:')
RE_SQLSTATE = re.compile(r'Sqlstate: (\d+)')
RE_POSITION = re.compile(r'Position: (\d+)')


def format_error(error):
    msg = str(error)
    if not hasattr(error, 'one_line_sql'):
        return msg

    result = ''

    match = RE_SQLSTATE.search(msg)
    if match:
        result += 'ERROR %s: ' % match.group(1)

    match = RE_MESSAGE.search(msg)
    if match:
        result += match.group(1)

    match = RE_POSITION.search(msg)
    if match:
        sql = error.one_line_sql()
        position = int(match.group(1))

        # Truncate the SQL query if its length > n (n must be odd)
        n = 75
        d = (n - 1) / 2
        length = len(sql)
        if length > n:
            left = position - d
            right = position + d
            position = d
            head = '...'
            tail = '...'

            if left < 0:
                right -= left
                position += left
                left = 0
                head = ''
            elif right >= length:
                offset = right - length + 1
                left -= offset
                position += offset
                right = length - 1
                tail = ''

            sql = head + sql[left:right + 1] + tail
            position += len(head)

        result += ('\n%s\n' % sql) + (' ' * (position - 1)) + '^'

    return result
