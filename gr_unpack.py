#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser(description='Unpack GR III firmware images')
parser.add_argument('inputFile', type=str, help='')
parser.add_argument('-v', action='store_const', const=True, default=False, help='verbose (debug messages)')
parser.add_argument('-o', default="unpackedFW", type=str, help='Output File Name')
args = parser.parse_args()

debug = args.v

def debugPrint(arg, end="\n"):
    if debug:
        print(arg, end=end)

with open(args.inputFile, "rb") as f:

    f.seek(0x80)

    text = bytearray(b"")
    blockCount = 0
    lastMeta = f.tell()
    lastSize = 0
    firstRun = False

    framePrefix = int.from_bytes(f.read(2), "big")

    done = False
    instrLenInt = 0
    recover = False

    print ("Unpacking...")
    while framePrefix != 0x00:
        debugPrint ("Frame @ " + format(f.tell()-2, "08x") + " - " + "Frame @ " + format(f.tell()-2 + (framePrefix & 0x7ffff), "08x")+ ", uncompressed: " + str((framePrefix & 0x8000) == 0x8000) + ", len: " +  format(framePrefix & 0x7fff, "04x")  + ", ignoring: "+ format(instrLenInt, "02x") + "...")
        frameStart = f.tell()
        if (framePrefix & 0x8000) == 0x8000:
            text += f.read(framePrefix & 0x7FFF)
        else:
            while (framePrefix & 0x7FFF) > (f.tell() - frameStart):
                blockPrefix = int.from_bytes(f.read(2), "big")
                debugPrint ("\n" + format(f.tell(), "08x") + " " + format(blockPrefix, "04x"), end = "")
                for i in range(0, 16):
                    if (not firstRun) and (framePrefix & 0x7FFF) < (f.tell() - frameStart - 2):
                        print ("error 0x" + format((framePrefix & 0x7FFF) + frameStart - 2, "06x"))
                        print ("trying to recover...")
                        recover = True
                        break

                    if ((blockPrefix >> (15-i)) & 1) == 0:
                        text += f.read(1)
                        if debug:
                            literalInt = text[-1]
                            if (literalInt > 31) and (literalInt < 127):
                                debugPrint(" _" + bytes([literalInt]).decode("utf-8", "ignore"), end="")
                            else:
                                debugPrint(" " + format(literalInt, "02x"), end="")
                    else:

                        instrLen = f.read(1)
                        instrLenInt = int.from_bytes(instrLen, "big")
                        instrOff = f.read(1)
                        instrOffInt = int.from_bytes(instrOff, "big")
                        if (instrLen > b"\x07"):
                            instrLenInt = instrLen[0] & 0x7
                            instrOffInt += ((instrLen[0] & 0xf8) << (8 - 3))
                        if instrLenInt == 7:
                            instrLenInt += int.from_bytes(f.read(1), "big")
                        if (instrOffInt != 0):
                            start = len(text) - instrOffInt
                            buf = b""
                            if (instrLenInt == 0x7 + 0xFF):
                                nextByte = 0xff
                                while nextByte == 0xff:
                                    nextByte = int.from_bytes(f.read(1), "big")
                                    instrLenInt += nextByte


                            for k in range(start, start + 3 + instrLenInt):
                                if k >= 0:
                                    text += bytes([text[k]])
                                else:
                                    text += b"?"
                            for j in range(0,i):
                                debugPrint ("   ", end="")
                        else:
                            if firstRun:
                                frameStart = f.tell() - framePrefix
                            if f.tell() != frameStart + framePrefix:
                                print("need to recover...")
                                recover = True
                                break
                            else:
                                break
                if recover:
                    f.seek((framePrefix & 0x7FFF) + frameStart)
                    recover = False
                    break
        firstRun = False
        framePrefix = int.from_bytes(f.read(2), "big")
    print ("done.")
    outf = open(args.o, 'wb')
    outf.write(text)
    outf.close()