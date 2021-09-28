#!/usr/bin/env python3
# unicode_converter/serialazer.py


from abc import ABC, abstractmethod


class Serializer(ABC):
    @abstractmethod
    def __init__(self, writer):
        pass


    @abstractmethod
    def serialize_char(self, char):
        pass


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
            
