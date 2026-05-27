# Smallest AWK program that satisfies contract_declaration.toml C01:
# writes the exact line "Hello, world!\n" to stdout and exits zero.
BEGIN {
    print "Hello, world!"
}
