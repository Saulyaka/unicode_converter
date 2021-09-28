#!/usr/bin/env python3
# unicode_converter/converter.py


from parser_ import ParseMode, UTF16LEParser, UTF8Parser, UTF16BEParser, UTF32BEParser, UTF32LEParser
from io_buffer import Reader, Writer, BufferEmpty 
from  serialazer_ import UTF16LESerializer, UTF8Serializer, UTF16BESerializer, UTF32LESerializer, UTF32BESerializer


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
    filename_in = "testUTF32BE.txt"
    filename_out =  "test-test.txt"
    parser_class = UTF32BEParser
    serializer_class = UTF8Serializer
    mode = ParseMode.LATIN1

    with open(filename_in, "rb") as infile:
        with open(filename_out, "wb") as outfile:
            converter(infile, outfile, parser_class, serializer_class, mode)
