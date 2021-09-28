#!/usr/bin/env python3
# unicode_converter/converter.py


from parser_ import ParseMode, UTF16LEParser, UTF8Parser, UTF16BEParser, UTF32BEParser, UTF32LEParser
from io_buffer import Reader, Writer, BufferEmpty 
from  serialazer_ import UTF16LESerializer, UTF8Serializer, UTF16BESerializer, UTF32LESerializer, UTF32BESerializer
import argparse


encoding = ["utf-32be", "utf-32le", "utf-16be", "utf-16le", "utf-8"]
mode = ["LATIN1", "IGNORE", "RAISE", "REPLACE"]


def parser_class(_encoding):
    if _encoding == encoding[0]:
        return UTF32BEParser
    if _encoding == encoding[1]:
        return UTF32LEParser
    if _encoding == encoding[2]:
        return UTF16BEParser
    if _encoding == encoding[3]:
        return UTF16LEParser
    if encoding == encoding[4]:
        return UTF8Parser


def serializer_class(decoding):
    if decoding == encoding[0]:
        return UTF32BESerializer
    if decoding == encoding[1]:
        return UTF32LESerializer
    if decoding == encoding[2]:
        return UTF16BESerializer
    if decoding == encoding[3]:
        return UTF16LESerializer
    if decoding == encoding[4]:
        return UTF8Serializer


def parse_mode(_mode):
    if _mode == mode[0]:
        return ParseMode.LATIN1
    if _mode == mode[1]:
        return ParseMode.IGNORE
    if _mode == mode[2]:
        return ParseMode.RAISE
    if _mode == mode[3]:
        return ParseMode.REPLACE


def converter(infile, outfile, parser_class, serializer_class, mode):
    reader = Reader(infile)
    parser = parser_class(reader, mode)
    writer = Writer(outfile)
    serializer = serializer_class(writer)
    while True:
        try:
            char = parser.parse_char()
            serializer.serialize_char(char)
        except BufferEmpty:
            writer.flush()
            try:
                reader.fill()
            except EOFError:
                writer.flush()
                break




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"UTF converter of encoding: {encoding}")
    parser.add_argument("in_file", type=str, help="Input file dir")
    parser.add_argument("encoding", type=str, help="Encoding of income file", choices=encoding)
    parser.add_argument("out_file", type=str, help="Output file dir")
    parser.add_argument("-d", type=str, default="utf-8", help="Decoding of output file. UTF-8 by default.", choices=encoding)
    parser.add_argument("-m", type=str, default="LATIN1", help="Handling encoding errors", choices=mode)    
    args = parser.parse_args()

    filename_in = args.in_file
    filename_out = args.out_file
    parser_class = parser_class(args.encoding)
    serializer_class = serializer_class(args.d)
    mode = parse_mode(args.m)

    with open(filename_in, "rb") as infile:
        with open(filename_out, "wb") as outfile:
            converter(infile, outfile, parser_class, serializer_class, mode)


