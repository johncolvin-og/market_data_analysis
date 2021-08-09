import copy
from src.view.color import Color


class CellView:
    def __init__(self, **kwargs):
        self.color = kwargs.get('color') or kwargs.get(
            'foreground') or kwargs.get('fg')
        self.background = kwargs.get('background_color') or kwargs.get(
            'background') or kwargs.get('bg')
        self.font_weight = kwargs.get('font_weight') or kwargs.get('fw')
        self.vertical_align = kwargs.get('vertical_align') or kwargs.get(
            'valign')

        self.border = kwargs.get('border') or kwargs.get(
            'border_style') or kwargs.get('bd') or kwargs.get('bds')
        self.border_left = kwargs.get('border_left') or kwargs.get(
            'border_left_style') or kwargs.get('bdl') or kwargs.get('bdls')
        self.border_top = kwargs.get('border_top') or kwargs.get(
            'border_top_style') or kwargs.get('bdt') or kwargs.get('bdts')
        self.border_right = kwargs.get('border_right') or kwargs.get(
            'border_right_style') or kwargs.get('bdr') or kwargs.get('bdrs')
        self.border_bottom = kwargs.get('border_bottom') or kwargs.get(
            'border_bottom_style') or kwargs.get('bdb') or kwargs.get('bdbs')

        self.border_color = kwargs.get('border_color') or kwargs.get('bdc')
        self.border_left_color = kwargs.get('border_left_color') or kwargs.get(
            'bdlc')
        self.border_top_color = kwargs.get('border_top_color') or kwargs.get(
            'bdtc')
        self.border_right_color = kwargs.get(
            'border_right_color') or kwargs.get('bdrc')
        self.border_bottom_color = kwargs.get(
            'border_bottom_color') or kwargs.get('bdbc')

        self.margin = kwargs.get('margin') or kwargs.get('mg')
        self.margin_left = kwargs.get('margin_left') or kwargs.get('mgl')
        self.margin_top = kwargs.get('margin_top') or kwargs.get('mgt')
        self.margin_right = kwargs.get('margin_right') or kwargs.get('mgr')
        self.margin_bottom = kwargs.get('margin_bottom') or kwargs.get('mgb')

        self.padding = kwargs.get('padding') or kwargs.get('pd')
        self.padding_left = kwargs.get('padding_left') or kwargs.get('pdl')
        self.padding_top = kwargs.get('padding_top') or kwargs.get('pdt')
        self.padding_right = kwargs.get('padding_right') or kwargs.get('pdr')
        self.padding_bottom = kwargs.get('padding_bottom') or kwargs.get('pdb')

    def merge(
            self,
            other,
            bg_blend_weight=0.5,
            fg_blend_weight=0.5,
            bc_blend_weight=0.5,
            inplace=False):
        tgt = self if inplace else copy.deepcopy(self)
        tgt.border = tgt.border or other.border

        def ensure_blendable(color):
            return Color(color) if not isinstance(color, Color) else color

        def merge_color(this_color, other_color, blend_weight):
            if other_color is None:
                return this_color
            if this_color is None:
                return other_color
            this_color = ensure_blendable(this_color)
            other_color = ensure_blendable(other_color)
            return this_color.blend(other_color, blend_weight)

        tgt.color = merge_color(tgt.color, other.color, fg_blend_weight)
        tgt.background = merge_color(
            tgt.background, other.background, bg_blend_weight)
        tgt.font_weight = tgt.font_weight or other.font_weight
        tgt.vertical_align = tgt.vertical_align or other.vertical_align

        tgt.border_color = merge_color(
            tgt.border_color, other.border_color, bc_blend_weight)
        tgt.border = tgt.border or other.border
        tgt.border_left = tgt.border_left or other.border_left
        tgt.border_top = tgt.border_top or other.border_top
        tgt.border_right = tgt.border_right or other.border_right
        tgt.border_bottom = tgt.border_bottom or other.border_bottom

        tgt.margin = tgt.margin or other.margin
        tgt.margin_left = tgt.margin_left or other.margin_left
        tgt.margin_top = tgt.margin_top or other.margin_top
        tgt.margin_right = tgt.margin_right or other.margin_right
        tgt.margin_bottom = tgt.margin_bottom or other.margin_bottom

        tgt.padding = tgt.padding or other.padding
        tgt.padding_left = tgt.padding_left or other.padding_left
        tgt.padding_top = tgt.padding_top or other.padding_top
        tgt.padding_right = tgt.padding_right or other.padding_right
        tgt.padding_bottom = tgt.padding_bottom or other.padding_bottom
        return tgt

    def to_tuples(self):
        rv = []

        def add_prop(name, value):
            if value is not None:
                rv.append((name, value))

        add_prop('color', self.color)
        add_prop('background', self.background)
        add_prop('font-weight', self.font_weight)
        add_prop('vertical-align', self.vertical_align)

        def add_bordert_prop(prefix, suffix, a, l, t, r, b):
            def fmt(*args):
                return '-'.join([x for x in args if x is not None])

            add_prop(fmt(prefix, suffix), a),
            add_prop(fmt(prefix, 'left', suffix), l)
            add_prop(fmt(prefix, 'top', suffix), t)
            add_prop(fmt(prefix, 'right', suffix), r)
            add_prop(fmt(prefix, 'bottom', suffix), b)

        add_bordert_prop(
            'margin', None, self.margin, self.margin_left, self.margin_top,
            self.margin_right, self.margin_bottom)
        add_bordert_prop(
            'padding', None, self.padding, self.padding_left, self.padding_top,
            self.padding_right, self.padding_bottom)
        add_bordert_prop(
            'border', 'style', self.border, self.border_left, self.border_top,
            self.border_right, self.border_bottom)
        add_bordert_prop(
            'border', 'color', self.border_color, self.border_left_color,
            self.border_top_color, self.border_right_color,
            self.border_bottom_color)

        return rv
