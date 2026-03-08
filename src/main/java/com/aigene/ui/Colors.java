package com.aigene.ui;

public final class Colors {
    public static final String RESET  = "\u001B[0m";
    public static final String BOLD   = "\u001B[1m";
    public static final String DIM    = "\u001B[2m";

    public static final String RED    = "\u001B[31m";
    public static final String GREEN  = "\u001B[32m";
    public static final String YELLOW = "\u001B[33m";
    public static final String BLUE   = "\u001B[34m";
    public static final String PURPLE = "\u001B[35m";
    public static final String CYAN   = "\u001B[36m";
    public static final String WHITE  = "\u001B[37m";

    public static final String BG_BLUE   = "\u001B[44m";
    public static final String BG_GREEN  = "\u001B[42m";
    public static final String BG_PURPLE = "\u001B[45m";

    private Colors() {}

    public static String bold(String s)   { return BOLD + s + RESET; }
    public static String green(String s)  { return GREEN + s + RESET; }
    public static String yellow(String s) { return YELLOW + s + RESET; }
    public static String cyan(String s)   { return CYAN + s + RESET; }
    public static String blue(String s)   { return BLUE + s + RESET; }
    public static String red(String s)    { return RED + s + RESET; }
    public static String purple(String s) { return PURPLE + s + RESET; }
    public static String dim(String s)    { return DIM + s + RESET; }
}
