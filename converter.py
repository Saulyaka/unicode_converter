#!/usr/bin/env python3
# unicode_converter/converter.py


from parser_ import ParseMode, UTF16LEParser, UTF8Parser, UTF16BEParser, UTF32BEParser, UTF32LEParser
from io_buffer import Reader, Writer, BufferEmpty 
from  serialazer_ import UTF16LESerializer, UTF8Serializer, UTF16BESerializer, UTF32LESerializer, UTF32BESerializer
import argparse


parser_dict = {
    "utf-32be": UTF32BEParser,
    "utf-32le": UTF32LEParser,
    "utf-16be": UTF16BEParser,
    "utf-16le": UTF16LEParser,
    "utf-8": UTF8Parser
    }
serializer_dict ={
    "utf-32be": UTF32BESerializer,
    "utf-32le": UTF32LESerializer,
    "utf-16be": UTF16BESerializer,
    "utf-16le": UTF16LESerializer,
    "utf-8": UTF8Serializer}

mode_dict = {
    "LATIN1": ParseMode.LATIN1,
    "IGNORE": ParseMode.IGNORE,
    "RAISE": ParseMode.RAISE,
    "REPLACE": ParseMode.REPLACE}


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
    parser.add_argument("encoding", type=str, help="Encoding of income file", choices=parser_dict)
    parser.add_argument("out_file", type=str, help="Output file dir")
    parser.add_argument("-d", type=str, default="utf-8", help="Decoding of output file. UTF-8 by default.", choices=serializer_dict)
    parser.add_argument("-m", type=str, default="LATIN1", help="Handling encoding errors", choices=mode_dict)    
    args = parser.parse_args()

    filename_in = args.in_file
    filename_out = args.out_file
    parser_class = parser_dict[args.encoding]
    serializer_class = serializer_dict[args.d]
    mode = mode_dict[args.m]

    with open(filename_in, "rb") as infile:
        with open(filename_out, "wb") as outfile:
            converter(infile, outfile, parser_class, serializer_class, mode)