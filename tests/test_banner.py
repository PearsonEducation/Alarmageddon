from alarmageddon.banner import print_banner


def test_print_color_banner():
    print_banner(color=True)


def test_print_monochrome_banner():
    print_banner(color=False)
