from bisect import bisect_left


class Heatmap:
    def __init__(self, steps={}, interpolate=True):
        self.steps = steps
        self.interpolate = interpolate

    @staticmethod
    def stepwise_lambda(steps={}, map_value=None):
        if len(steps) == 0:
            raise ValueError('\'steps\' is empty')
        keys = list(steps.keys())
        keys.sort()

        def get_key(x):
            i = bisect_left(keys, x)
            if i == len(keys):
                return keys[len(steps) - 1]
            if x < keys[i]:
                i -= 1
            return keys[i]

        if map_value == None:
            map_value = lambda x: x
        return lambda x: f'background-color: {steps[get_key(map_value(x))]}'

    @staticmethod
    def interpolation_lambda(steps={}, map_value=None):
        if len(steps) == 0:
            raise ValueError('\steps\' is empty')

        def fmt_attr(color):
            return f'background-color: {color}'

        if len(steps) == 1:
            val = next(iter(steps.items()))[1]
            attr_str = fmt_attr(val)
            return lambda x: attr_str
        keys = list(steps.keys())
        keys.sort()

        def binary_interpolate(value, max_idx):
            min_value = keys[max_idx - 1]
            max_value = keys[max_idx]
            min_color = steps[min_value]
            max_color = steps[max_value]
            spread = max_value - min_value
            return fmt_attr(
                min_color.blend(max_color, (value - min_value) / spread))

        if map_value == None:
            map_value = lambda x: x

        def interpolate(value):
            mvalue = map_value(value)
            i = bisect_left(keys, mvalue)
            if i == len(keys):
                return fmt_attr(steps[keys[-1]])
            if i == 0:
                return fmt_attr(steps[keys[0]])
            return binary_interpolate(mvalue, i)

        return interpolate

    def to_lambda(self, map_value=None):
        if self.interpolate:
            return Heatmap.interpolation_lambda(self.steps, map_value)
        return Heatmap.stepwise_lambda(self.steps, map_value)
