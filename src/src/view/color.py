import webcolors


def fill_bits(length, start=0):
    i = 0
    n = length
    while n > 0:
        i |= (1 << (start + n - 1))
        n -= 1
    return i


class Color:
    def __init__(self, *args, **kwargs):
        if len(args) == 3:
            self.r, self.g, self.b = args
            return

        def integer_impl(i):
            self.r = (i & fill_bits(8))
            self.g = (i & fill_bits(8, 8))
            self.b = (i & fill_bits(8, 16))

        def integer_rgb_impl(irgb):
            self.r = irgb.red
            self.g = irgb.green
            self.b = irgb.blue

        def text_impl(text):
            try:
                if text[0] == '#':
                    integer_impl(int(f'0x{text[1:]}', 0))
                elif len(text) > 1 and text[0:2] == '0x':
                    integer_impl(int(text, 0))
                else:
                    integer_impl(int(text))
            except:
                # Assume its a web color (named)
                wc = webcolors.name_to_rgb(text)
                integer_rgb_impl(wc)

        if len(args) == 1:
            if isinstance(args[0], int):
                integer_impl(args[0])
            elif isinstance(args[0], str):
                text_impl(args[0])
            elif isinstance(args[0], webcolors.IntegerRGB):
                self.r = args[0].red
                self.g = args[0].green
                self.b = args[0].blue

        if self.r is None:
            self.r = kwargs.get('r') or kwargs.get('red')
        if self.g is None:
            self.g = kwargs.get('g') or kwargs.get('green')
        if self.b is None:
            self.b = kwargs.get('b') or kwargs.get('blue')

        if self.r is None or self.g is None or self.b is None:
            i = kwargs.get('i') or kwargs.get('integer') or kwargs.get(
                'rgb') or kwargs.get('hex')
            if isinstance(i, int):
                integer_impl(i)
            elif isinstance(i, str):
                text_impl(i)
            else:
                text = kwargs.get('t') or kwargs.get('text') or kwargs.get(
                    'value')
                if isinstance(text, str) and len(text) > 0:
                    text_impl(text)

    def blend(self, other, weight=0.5):
        if weight >= 1:
            return other
        if weight <= 0:
            return self
        r = self.r + weight * (other.r - self.r)
        g = self.g + weight * (other.g - self.g)
        b = self.b + weight * (other.b - self.b)
        return Color(int(r), int(g), int(b))

    def __str__(self):
        return '#{:02x}{:02x}{:02x}'.format(self.r, self.g, self.b)


class Colors:
    @staticmethod
    def black():
        return Color(0, 0, 0)

    @staticmethod
    def white():
        return Color(255, 255, 255)

    @staticmethod
    def red():
        return Color(255, 0, 0)

    @staticmethod
    def darkred():
        return Color(130, 20, 20)

    @staticmethod
    def green():
        return Color(0, 255, 0)

    @staticmethod
    def yellow():
        return Color(255, 255, 0)

    @staticmethod
    def gold():
        return Color(208, 208, 0)

    @staticmethod
    def brown():
        return Color(150, 90, 0)

    @staticmethod
    def orange():
        return Color(255, 128, 0)

    @staticmethod
    def purple():
        return Color(128, 0, 255)

    @staticmethod
    def pink():
        return Color(234, 124, 175)

    @staticmethod
    def slateblue():
        return Color(120, 65, 255)

    @staticmethod
    def darkgreen():
        return Color(20, 130, 20)

    @staticmethod
    def darkgreen_pastel():
        return Color(17, 73, 17)

    @staticmethod
    def green_pastel():
        return Color(26, 168, 26)

    @staticmethod
    def semi_lightgreen_pastel():
        return Color(40, 186, 40)

    @staticmethod
    def lightgreen_pastel():
        return Color(55, 206, 55)

    @staticmethod
    def header_background():
        return Color(34, 56, 100)

    @staticmethod
    def blue():
        return Color(0, 0, 255)

    @staticmethod
    def darkblue():
        return Color(20, 20, 130)


class WebColors:

    # Pink colors

    @staticmethod
    def medium_violet_red():
        return webcolors.name_to_rgb('MediumVioletRed')

    @staticmethod
    def deep_pink():
        return webcolors.name_to_rgb('DeepPink')

    @staticmethod
    def pale_violet_red():
        return webcolors.name_to_rgb('PaleVioletRed')

    @staticmethod
    def hot_pink():
        return webcolors.name_to_rgb('HotPink')

    @staticmethod
    def light_pink():
        return webcolors.name_to_rgb('LightPink')

    @staticmethod
    def pink():
        return webcolors.name_to_rgb('Pink')

    # Red colors

    @staticmethod
    def dark_red():
        return webcolors.name_to_rgb('DarkRed')

    @staticmethod
    def red():
        return webcolors.name_to_rgb('Red')

    @staticmethod
    def firebrick():
        return webcolors.name_to_rgb('Firebrick')

    @staticmethod
    def crimson():
        return webcolors.name_to_rgb('Crimson')

    @staticmethod
    def indian_red():
        return webcolors.name_to_rgb('IndianRed')

    @staticmethod
    def light_coral():
        return webcolors.name_to_rgb('LightCoral')

    @staticmethod
    def salmon():
        return webcolors.name_to_rgb('Salmon')

    @staticmethod
    def dark_salmon():
        return webcolors.name_to_rgb('DarkSalmon')

    @staticmethod
    def light_salmon():
        return webcolors.name_to_rgb('LightSalmon')

    # Orange colors

    @staticmethod
    def orange_red():
        return webcolors.name_to_rgb('OrangeRed')

    @staticmethod
    def tomato():
        return webcolors.name_to_rgb('Tomato')

    @staticmethod
    def dark_orange():
        return webcolors.name_to_rgb('DarkOrange')

    @staticmethod
    def coral():
        return webcolors.name_to_rgb('Coral')

    @staticmethod
    def orange():
        return webcolors.name_to_rgb('Orange')

    # Yellow colors

    @staticmethod
    def dark_khaki():
        return webcolors.name_to_rgb('DarkKhaki')

    @staticmethod
    def gold():
        return webcolors.name_to_rgb('Gold')

    @staticmethod
    def khaki():
        return webcolors.name_to_rgb('Khaki')

    @staticmethod
    def peach_puff():
        return webcolors.name_to_rgb('PeachPuff')

    @staticmethod
    def yellow():
        return webcolors.name_to_rgb('Yellow')

    @staticmethod
    def pale_goldenrod():
        return webcolors.name_to_rgb('PaleGoldenrod')

    @staticmethod
    def moccasin():
        return webcolors.name_to_rgb('Moccasin')

    @staticmethod
    def papaya_whip():
        return webcolors.name_to_rgb('PapayaWhip')

    @staticmethod
    def light_goldenrod_yellow():
        return webcolors.name_to_rgb('LightGoldenrodYellow')

    @staticmethod
    def lemon_chiffon():
        return webcolors.name_to_rgb('LemonChiffon')

    @staticmethod
    def light_yellow():
        return webcolors.name_to_rgb('LightYellow')

    # Brown colors

    @staticmethod
    def maroon():
        return webcolors.name_to_rgb('Maroon')

    @staticmethod
    def brown():
        return webcolors.name_to_rgb('Brown')

    @staticmethod
    def saddle_brown():
        return webcolors.name_to_rgb('SaddleBrown')

    @staticmethod
    def sienna():
        return webcolors.name_to_rgb('Sienna')

    @staticmethod
    def chocolate():
        return webcolors.name_to_rgb('Chocolate')

    @staticmethod
    def dark_goldenrod():
        return webcolors.name_to_rgb('DarkGoldenrod')

    @staticmethod
    def peru():
        return webcolors.name_to_rgb('Peru')

    @staticmethod
    def rosy_brown():
        return webcolors.name_to_rgb('RosyBrown')

    @staticmethod
    def goldenrod():
        return webcolors.name_to_rgb('Goldenrod')

    @staticmethod
    def sandy_brown():
        return webcolors.name_to_rgb('SandyBrown')

    @staticmethod
    def tan():
        return webcolors.name_to_rgb('Tan')

    @staticmethod
    def burlywood():
        return webcolors.name_to_rgb('Burlywood')

    @staticmethod
    def wheat():
        return webcolors.name_to_rgb('Wheat')

    @staticmethod
    def navajo_white():
        return webcolors.name_to_rgb('NavajoWhite')

    @staticmethod
    def bisque():
        return webcolors.name_to_rgb('Bisque')

    @staticmethod
    def blanched_almond():
        return webcolors.name_to_rgb('BlanchedAlmond')

    @staticmethod
    def cornsilk():
        return webcolors.name_to_rgb('Cornsilk')

    # Purple, Violet, and Magenta colors

    @staticmethod
    def indigo():
        return webcolors.name_to_rgb('Indigo')

    @staticmethod
    def purple():
        return webcolors.name_to_rgb('Purple')

    @staticmethod
    def dark_magenta():
        return webcolors.name_to_rgb('DarkMagenta')

    @staticmethod
    def dark_violet():
        return webcolors.name_to_rgb('DarkViolet')

    @staticmethod
    def dark_slate_blue():
        return webcolors.name_to_rgb('DarkSlateBlue')

    @staticmethod
    def blue_violet():
        return webcolors.name_to_rgb('BlueViolet')

    @staticmethod
    def dark_orchid():
        return webcolors.name_to_rgb('DarkOrchid')

    @staticmethod
    def fuchsia():
        return webcolors.name_to_rgb('Fuchsia')

    @staticmethod
    def magenta():
        return webcolors.name_to_rgb('Magenta')

    @staticmethod
    def slate_blue():
        return webcolors.name_to_rgb('SlateBlue')

    @staticmethod
    def medium_slate_blue():
        return webcolors.name_to_rgb('MediumSlateBlue')

    @staticmethod
    def medium_orchid():
        return webcolors.name_to_rgb('MediumOrchid')

    @staticmethod
    def medium_purple():
        return webcolors.name_to_rgb('MediumPurple')

    @staticmethod
    def orchid():
        return webcolors.name_to_rgb('Orchid')

    @staticmethod
    def violet():
        return webcolors.name_to_rgb('Violet')

    @staticmethod
    def plum():
        return webcolors.name_to_rgb('Plum')

    @staticmethod
    def thistle():
        return webcolors.name_to_rgb('Thistle')

    @staticmethod
    def lavender():
        return webcolors.name_to_rgb('Lavender')

    # White colors

    @staticmethod
    def misty_rose():
        return webcolors.name_to_rgb('MistyRose')

    @staticmethod
    def antique_white():
        return webcolors.name_to_rgb('AntiqueWhite')

    @staticmethod
    def linen():
        return webcolors.name_to_rgb('Linen')

    @staticmethod
    def beige():
        return webcolors.name_to_rgb('Beige')

    @staticmethod
    def white_smoke():
        return webcolors.name_to_rgb('WhiteSmoke')

    @staticmethod
    def lavender_blush():
        return webcolors.name_to_rgb('LavenderBlush')

    @staticmethod
    def old_lace():
        return webcolors.name_to_rgb('OldLace')

    @staticmethod
    def alice_blue():
        return webcolors.name_to_rgb('AliceBlue')

    @staticmethod
    def seashell():
        return webcolors.name_to_rgb('Seashell')

    @staticmethod
    def ghost_white():
        return webcolors.name_to_rgb('GhostWhite')

    @staticmethod
    def honey_dew():
        return webcolors.name_to_rgb('HoneyDew')

    @staticmethod
    def floral_white():
        return webcolors.name_to_rgb('FloralWhite')

    @staticmethod
    def azure():
        return webcolors.name_to_rgb('Azure')

    @staticmethod
    def mint_cream():
        return webcolors.name_to_rgb('MintCream')

    @staticmethod
    def snow():
        return webcolors.name_to_rgb('Snow')

    @staticmethod
    def ivory():
        return webcolors.name_to_rgb('Ivory')

    @staticmethod
    def white():
        return webcolors.name_to_rgb('White')

    # Gray and Black colors

    @staticmethod
    def black():
        return webcolors.name_to_rgb('Black')

    @staticmethod
    def dark_slate_gray():
        return webcolors.name_to_rgb('DarkSlateGray')

    @staticmethod
    def dim_gray():
        return webcolors.name_to_rgb('DimGray')

    @staticmethod
    def slate_gray():
        return webcolors.name_to_rgb('SlateGray')

    @staticmethod
    def gray():
        return webcolors.name_to_rgb('Gray')

    @staticmethod
    def light_slate_gray():
        return webcolors.name_to_rgb('LightSlateGray')

    @staticmethod
    def dark_gray():
        return webcolors.name_to_rgb('DarkGray')

    @staticmethod
    def silver():
        return webcolors.name_to_rgb('Silver')

    @staticmethod
    def light_gray():
        return webcolors.name_to_rgb('LightGray')

    @staticmethod
    def gainsboro():
        return webcolors.name_to_rgb('Gainsboro')

    #Green colors

    @staticmethod
    def dark_green():
        return webcolors.name_to_rgb('DarkGreen')

    @staticmethod
    def dark_olive_green():
        return webcolors.name_to_rgb('DarkOliveGreen')

    @staticmethod
    def forest_green():
        return webcolors.name_to_rgb('ForestGreen')

    @staticmethod
    def sea_green():
        return webcolors.name_to_rgb('SeaGreen')

    @staticmethod
    def olive():
        return webcolors.name_to_rgb('Olive')

    @staticmethod
    def medium_sea_green():
        return webcolors.name_to_rgb('MediumSeaGreen')

    @staticmethod
    def lime_green():
        return webcolors.name_to_rgb('LimeGreen')

    @staticmethod
    def lime():
        return webcolors.name_to_rgb('Lime')

    @staticmethod
    def spring_green():
        return webcolors.name_to_rgb('SpringGreen')

    @staticmethod
    def medium_spring_green():
        return webcolors.name_to_rgb('MediumSpringGreen')

    @staticmethod
    def dark_sea_green():
        return webcolors.name_to_rgb('DarkSeaGreen')

    @staticmethod
    def medium_aquamarine_green():
        return webcolors.name_to_rgb('MediumAquamaringGreen')

    @staticmethod
    def yellow_green():
        return webcolors.name_to_rgb('YellowGreen')

    @staticmethod
    def lawn_green():
        return webcolors.name_to_rgb('LawnGreen')

    @staticmethod
    def chartreuse():
        return webcolors.name_to_rgb('Chartreuse')

    @staticmethod
    def light_green():
        return webcolors.name_to_rgb('LightGreen')

    @staticmethod
    def green_yellow():
        return webcolors.name_to_rgb('GreenYellow')

    @staticmethod
    def pale_green():
        return webcolors.name_to_rgb('PaleGreen')

    # Cyan colors

    @staticmethod
    def teal():
        return webcolors.name_to_rgb('Teal')

    @staticmethod
    def dark_cyan():
        return webcolors.name_to_rgb('DarkCyan')

    @staticmethod
    def light_sea_green():
        return webcolors.name_to_rgb('LightSeaGreen')

    @staticmethod
    def cadet_blue():
        return webcolors.name_to_rgb('CadetBlue')

    @staticmethod
    def dark_turquoise():
        return webcolors.name_to_rgb('DarkTurqoise')

    @staticmethod
    def medium_turquoise():
        return webcolors.name_to_rgb('MediumTurquoise')

    @staticmethod
    def turquoise():
        return webcolors.name_to_rgb('Turquoise')

    @staticmethod
    def aqua():
        return webcolors.name_to_rgb('Aqua')

    @staticmethod
    def cyan():
        return webcolors.name_to_rgb('Cyan')

    @staticmethod
    def aquamarine():
        return webcolors.name_to_rgb('Aquamarine')

    @staticmethod
    def pale_turquoise():
        return webcolors.name_to_rgb('PaleTurquoise')

    @staticmethod
    def light_cyan():
        return webcolors.name_to_rgb('LightCyan')

    # Blue colors

    @staticmethod
    def navy():
        return webcolors.name_to_rgb('Navy')

    @staticmethod
    def dark_blue():
        return webcolors.name_to_rgb('DarkBlue')

    @staticmethod
    def medium_blue():
        return webcolors.name_to_rgb('MediumBlue')

    @staticmethod
    def blue():
        return webcolors.name_to_rgb('Blue')

    @staticmethod
    def midnight_blue():
        return webcolors.name_to_rgb('MidnightBlue')

    @staticmethod
    def royal_blue():
        return webcolors.name_to_rgb('RoyalBlue')

    @staticmethod
    def steel_blue():
        return webcolors.name_to_rgb('SteelBlue')

    @staticmethod
    def dodger_blue():
        return webcolors.name_to_rgb('DodgerBlue')

    @staticmethod
    def deep_sky_blue():
        return webcolors.name_to_rgb('DeepSkyBlue')

    @staticmethod
    def cornflower_blue():
        return webcolors.name_to_rgb('CornflowerBlue')

    @staticmethod
    def sky_blue():
        return webcolors.name_to_rgb('SkyBlue')

    @staticmethod
    def light_sky_blue():
        return webcolors.name_to_rgb('LightSkyBlue')

    @staticmethod
    def light_steel_blue():
        return webcolors.name_to_rgb('LightSteelBlue')

    @staticmethod
    def light_blue():
        return webcolors.name_to_rgb('LightBlue')

    @staticmethod
    def powder_blue():
        return webcolors.name_to_rgb('PowderBlue')
