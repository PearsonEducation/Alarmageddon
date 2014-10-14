# This Python file uses the following encoding: utf-8

import os, sys

from colorama import Fore, Back, Style, init, deinit

def print_banner(color=True):
    """Prints an Alarmageddon banner in color if the caller requests it
    and stdout is a terminal.  PEP8 is temporarily suspended...

    """
    if color and sys.stdout.isatty():
        # Print a color version of the banner
        init()
        print("")
        print(Fore.WHITE + "     " + Style.DIM + "( " + Style.NORMAL + "." + Style.DIM +  "  (    ) :" + Style.NORMAL + "." + Style.DIM +  " )      " + 
              Style.NORMAL + Fore.YELLOW + ".  , // .  ,      " + Fore.GREEN + "/\\")
        print(Fore.WHITE + "      " + Style.DIM + "( (    )     )        " + Style.NORMAL  + Fore.YELLOW + ".  //   .     " + Fore.GREEN + "/\\/  \\/\\")
        print(Fore.WHITE + "       " + Style.DIM + "(  : " + Style.NORMAL + "*" + Style.DIM +  "  (  )  " + Style.NORMAL + "   *   "  + Fore.YELLOW + 
              ". //  .      " + Fore.GREEN + "( " + Fore.RED + ">" + Fore.GREEN + "\\  /" + Fore.RED + "<" + Fore.GREEN + " )")
        print(Fore.WHITE + "  * " + Style.DIM + "    (    :   )         "  + Style.NORMAL + Fore.YELLOW + ". // . .      " + Fore.GREEN + "/  `__`  \\")
        print(Fore.WHITE + "         " + Style.DIM + "( :  : )   " + Style.NORMAL + " *      "  + Fore.RED + Style.BRIGHT + " O" + Fore.YELLOW + Style.NORMAL + 
              " .         " + Fore.GREEN + "\\ /" + Fore.WHITE + "VVVV" + Fore.GREEN + "\ /")
        print(Fore.WHITE + "     * " + Style.DIM + "   ( :  )                        " + Style.NORMAL + Fore.RED + "/" + Fore.WHITE + "IIIIIII" + Fore.RED + 
              "/[]\\        ")
        print(Fore.WHITE + "    .      " + Fore.RED + "||||" + Fore.WHITE + "    .                   " + Fore.WHITE + Style.DIM + "d" + Style.NORMAL + Fore.RED + "_" + Fore.WHITE + "O" + Fore.RED +
              "______" + Fore.WHITE + "O" + Fore.RED + "___" + Style.DIM + Fore.WHITE + "b" + Style.NORMAL)
        print(Fore.WHITE + "         . " + Fore.RED + "||||" + Fore.WHITE + "  .     \\o/  \\o/      " + Fore.GREEN + " __   \\" + Fore.WHITE + "^^^^" + 
              Fore.GREEN + "/ \     ")
        print(Fore.WHITE + "         " + Fore.MAGENTA + "_/ " + Fore.YELLOW + "@ @@" + Fore.MAGENTA + "_" + Fore.WHITE + "       |    |       " + 
              Fore.GREEN + "/  /\\  \__/   \ ")
        print(Fore.WHITE + "        " + Fore.MAGENTA + "/  " + Fore.YELLOW + "@   @" + Fore.MAGENTA + " \  " + Fore.WHITE + "   //    \\\\    " + 
              Fore.GREEN + " " + Fore.WHITE + " VVV" + Fore.GREEN + "\\ \  \      \ ")
        print("")
        print("Alarmageddon: Monitoring Your Stuff...")
        print("    Until You Don't Care About Your Stuff.")
        print("")
        deinit()
    else:
        # Print a monochrome version of the banner.
        print("")
        print("     ( .  (    ) :. )      .  , // .  ,      /\ ")
        print("      ( (    )     )        .  //   .     /\/  \/\ ")
        print("       (  : *  (  )     *   . //  .      ( >\  /< ) ")
        print("  *     (    :   )         . // . .      /  `__`  \ ")
        print("         ( :  : )    *       O .         \ /VVVV\ / ")
        print("     *    ( :  )                        /IIIIIII/[]\         ")
        print("    .      ||||    .                   d_O______O___b ")
        print("         . ||||  .     \o/  \o/       __   \^^^^/ \      ")
        print("         _/ @ @@_       |    |       /  /\  \__/   \  ")
        print("        /  @   @ \     //    \\\\     VVV\  \  \      \  ")
        print("")
        print("Alarmageddon: Monitoring Your Stuff... ")
        print("    Until You Don't Care About Your Stuff. ")
        print("")
