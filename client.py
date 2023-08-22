import asyncio, telnetlib3
import decoder

async def shell(reader, writer):
    previous = None
    while True:
        # read stream until '?' mark is found
        outp = await reader.read(1024)
        if not outp:
            # End of File
            break
        # display all server output
        # print(decoder.processRecord(outp))
        # display only the records passing deadband filter.
        rec = decoder.record(raw=outp,measurement="ORES")
        if previous is None or previous != rec :
            print(rec)
            previous = rec

def main():
    loop = asyncio.get_event_loop()
    coro = telnetlib3.open_connection('esp-easy.lan', 8088, shell=shell)
    reader, writer = loop.run_until_complete(coro)
    loop.run_until_complete(writer.protocol.waiter_closed)

if __name__ == "__main__":
    main()
