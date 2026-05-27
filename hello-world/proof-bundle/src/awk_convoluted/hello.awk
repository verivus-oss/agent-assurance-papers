# Indirect AWK implementation for the source-profile witness.
BEGIN {
    codes = "72 101 108 108 111 44 32 119 111 114 108 100 33"
    print render(codes)
}

function render(encoded, parts, count, i, out) {
    count = split(encoded, parts, " ")
    for (i = 1; i <= count; i++) {
        out = out sprintf("%c", parts[i])
    }
    return out
}
