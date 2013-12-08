from flexmock import flexmock


class DictPartialMatcher(object):
    """
    verifies the the passed dict is a subset of the matched one
    """

    def __init__(self, expected):
        self._expected = expected

    def __eq__(self, other):
        for key in self._expected.keys():
            if key not in other:
                return False

            if self._expected[key] != other[key]:
                return False

        return True

def mocked_response(content=None, status_code=200, headers=None):
    return flexmock(ok=status_code < 400, status_code=status_code, json=lambda: content, raw=content, text=content, headers=headers)
