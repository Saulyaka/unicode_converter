#!/usr/bin/env python3
# unicode_converter/io_buffer.py


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

    
    def peek_word_BE(self, offt):
        return self.peek_byte(offt * 2) << 8 | self.peek_byte(offt * 2 + 1)


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