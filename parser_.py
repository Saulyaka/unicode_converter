#!/usr/bin/env python3
# unicode_converter/parser.py
import enum
from abc import ABC, abstractmethod


class ParseMode(enum.Enum):
    LATIN1 = 0
    IGNORE = 1
    RAISE = 2
    REPLACE = 3


class Parser(ABC):
    @abstractmethod
    def __init__(self, reader, mode):
        pass


    @abstractmethod
    def parse_char(self):
        pass


    @abstractmethod
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
        