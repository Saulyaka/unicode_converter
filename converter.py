import abc
import enum


class BufferEmpty(Exception):
    pass


class Reader:
    def __init__(self, f):
        self.file = f
        self.bufsize = 4096
        self.buffer = bytes()
        self.index = 0


    def peek_byte(self, offt):
        if self.index + offt < len(self.buffer):
            return self.buffer[self.index + offt]
        else:
            raise BufferEmpty()


    def advance_bytes(self, n):
        self.index += n


    def peek_word_LE(self, offt):
        return self.peek_byte(offt * 2) | self.peek_byte(offt * 2 + 1) << 8


    def advance_words(self, n):
        self.advance_bytes(n * 2)


    def fill(self):
        new_data = self.file.read(self.bufsize)
        if len(new_data) == 0:
            raise EOFError()
        self.buffer = self.buffer[self.index:] + new_data


class Writer:
    def __init__(self, f):
        self.file = f
        self.buffer = bytearray()


    def write_byte(self, byte):
        self.buffer.append(byte)


    def write_word_LE(self, word):
        self.write_byte(word & 0xFF)
        self.write_byte(word >> 8)


    def write_word_BE(self, word):
        self.write_byte(word >> 8)
        self.write_byte(word & 0xFF)    


    def flush(self):
        self.file.write(self.buffer)
        self.buffer = bytearray()


class ParseMode(enum.Enum):
    LATIN1 = 0
    IGNORE = 1
    RAISE = 2
    REPLACE = 3


class Parser(abc.ABC):
    @abc.abstractmethod
    def __init__(self, reader, mode):
        pass


    @abc.abstractmethod
    def parse_char(self):
        pass


    @abc.abstractmethod
    def on_error(self):
        pass


    def parse_char(self):
        char = None
        while char is None:
            char = self.try_parse_char()
        return char

    def on_error(self):
            if self.mode == ParseMode.LATIN1:
                byte = self.reader.peek_byte(0)
                self.reader.advance_bytes(1)
                return byte
            elif self.mode == ParseMode.IGNORE:
                self.reader.advance_bytes(1)
                return None
            elif self.mode == ParseMode.RAISE:
                self.reader.advance_bytes(1)
                raise UnicodeDecodeError()
            elif self.mode == ParseMode.REPLACE:
                self.reader.advance_bytes(1)
                return 0xFFFD


class Serializer(abc.ABC):
    @abc.abstractmethod
    def __init__(self, writer):
        pass


    @abc.abstractmethod
    def serialize_char(self, char):
        pass


class UTF8Parser(Parser):
    def __init__(self, reader, mode):
        self.reader = reader
        self.mode = mode


    def try_parse_char(self):
        byte1 = self.reader.peek_byte(0)
        # 0xxxxxxx -> xxxxxxx
        if byte1 & 0x80 == 0:
            self.reader.advance_bytes(1)
            return byte1
        # 110xxxxx 10yyyyyy -> xxxxxyyyyyy
        elif byte1 & 0xE0 == 0xC0:
            byte2 = self.reader.peek_byte(1)
            if byte2 & 0xC0 != 0x80:
                return self.on_error()
            self.reader.advance_bytes(2)
            return (byte1 & 0x1F) << 6 | byte2 & 0x3F
        # 1110xxxx 10yyyyyy 10zzzzzz -> xxxxyyyyyyzzzzzz
        elif byte1 & 0xF0 == 0xE0:
            byte2 = self.reader.peek_byte(1)
            if byte2 & 0xC0 != 0x80:
                return self.on_error()
            byte3 = self.reader.peek_byte(2)
            if byte3 & 0xC0 != 0x80:
                return self.on_error()
            self.reader.advance_bytes(3)
            return (byte1 & 0x0F) << 12 | (byte2 & 0x3F) << 6 | byte3 & 0x3F
        # 11110xxx 10yyyyyy 10zzzzzz 10wwwwww -> xxxyyyyyyzzzzzzwwwwww
        elif byte1 & 0xF8 == 0xF0:
            byte2 = self.reader.peek_byte(1)
            if byte2 & 0xC0 != 0x80:
                return self.on_error()
            byte3 = self.reader.peek_byte(2)
            if byte3 & 0xC0 != 0x80:
                return self.on_error()
            byte4 = self.reader.peek_byte(3)
            if byte4 & 0xC0 != 0x80:
                return self.on_error()
            self.reader.advance_bytes(4)
            return (byte1 & 0x07) << 18 | (byte2 & 0x3F) << 12 | (byte3 & 0x3F) << 6 | (byte4 & 0x3F)
        # 11111xxx
        # 10xxxxxx
        else:
            return self.on_error()


class UTF16LEParser(Parser):
    def __init__(self, reader, mode):
        self.reader = reader
        self.mode = mode


    def try_parse_char(self):
        pair1 = self.reader.peek_word_LE(0)
        # surrogates
        if pair1 >> 10 == 0x36:
            pair2 = self.reader.peek_word_LE(1)
            if pair2 >> 10 != 0x37:
                return self.on_error()
            self.reader.advance_words(2)
            return (pair2 & 0x3FF) | ((pair1 & 0x3FF) << 10) + 0x10000
        # usual pair of bytes
        else:
            self.reader.advance_words(1)
            return pair1
        

class UTF16LESerializer(Serializer):
    def __init__(self, writer):
        self.writer = writer


    def serialize_char(self, char):
        if char <= 0xFFFF:
            self.writer.write_word_LE(char)
        else:
            self.writer.write_word_LE((char - 0x10000) >> 10 | 0xD800)
            self.writer.write_word_LE((char - 0x10000) & 0x3FF | 0xDC00)



class UTF8Serializer(Serializer):
    def __init__(self, writer):
        self.writer = writer


    def serialize_char(self, char):
        if char <= 0x7F:
            # xxxxxxx -> 0xxxxxxx
            self.writer.write_byte(char)
        elif char <= 0x7FF:
            # yyy yyxxxxxx -> 110yyyyy 10xxxxxx
            self.writer.write_byte(char >> 6 | 0xC0)
            self.writer.write_byte(char & 0x3F | 0x80)            
        elif char <= 0xFFFF:
            # zzzzyyyy yyxxxxxx -> 1110zzzz 10yyyyyy 10xxxxxx
            self.writer.write_byte(char >> 12 | 0xE0)
            self.writer.write_byte(char >> 6 & 0x3F| 0x80)
            self.writer.write_byte(char & 0x3F | 0x80)
        else:
            #  jjjzz zzzzyyyy yyxxxxxx-> 11110jjj 10zzzzzz 10yyyyyy 10xxxxxx 
            self.writer.write_byte(char >> 18 | 0xF0)
            self.writer.write_byte(char >> 12 & 0x3F | 0x80)
            self.writer.write_byte(char >> 6 & 0x3F | 0x80)
            self.writer.write_byte(char & 0x3F | 0x80)
            

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
    filename_in = "converter/output16LE.txt"
    filename_out = "converter/test16LE_Parser.txt"
    parser_class = UTF16LEParser
    serializer_class = UTF8Serializer
    mode = ParseMode.LATIN1

    with open(filename_in, "rb") as infile:
        with open(filename_out, "wb") as outfile:
            converter(infile, outfile, parser_class, serializer_class, mode)
