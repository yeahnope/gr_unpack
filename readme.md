# gr_unpack

This repository contains information and code about the packing used for Ricoh GRIII firmware images.

## File Format
The file consists of a 0x80 byte header, followed by frames which can either contain only literals (not
compressed data) or are made up of blocks.

### Frames
The first two bytes of a frame determine the size and the type of the frame:
```
usssssss ssssssss
u =  1 bit bool:
        1 if data in frame is literal
        0 if data in frame is compressed
s = 15 bit unsigned integer size of frame
```
The rest of the frame consists of either s bytes of literals or of s bytes of compression blocks

### Block
If a frame contains compressed data, it is comprised of blocks.
The first two bytes of the block determine where in the block copy instructions are to be found.
A bit set to 0 represents a literal, a bit set to 1 represents a copy instruction. I.e. a block beginning
with 0x0003 beginns with 14 literals, and ends with 2 copy instructions.

Copy instructions are at least 2 bytes long, but can be longer:
```
ooooolll oooooooo
o = 13 bit unsigned integer offset value
l =  3 bit unsigned integer length value

o is determined by ((byte0 & 0xf8) << 5) + byte1

If all length bits are set, another byte is added to the copy instruction:
ooooo111 oooooooo llllllll
l is then determined by (byte0 & 0x07) + byte2, which is the same as 0x07 + byte2
```
If the offset is > 0, a total of (l + 3) bytes is copied from the already written file, starting at the
current write head minus o bytes. I.e. if the offset is 0x01 and the length is 0x01, and the current write
buffer is "Test" the output after the copy operation would be "Testtttt"

If the offset is 0, the frame ends and the following 2 bytes will determine size and type of the next frame.