import argparse
import asyncio, telnetlib3
import decoder

async def shell(reader, writer):
    previous = None
    while True:
        # read stream
        outp = await reader.read(1024)
        if not outp:
            # End of File
            break
        # display only the records passing deadband filter.
        rec = decoder.record(raw=outp,measurement="ORES")
        if previous is None or previous != rec :
            print(rec)
            previous = rec

def main():
    # load options
    argParser = argparse.ArgumentParser(
            prog="client.py",
            description="Telegraf external deamon input plugin to read P1 data.",
            epilog="Reduce your energy footprint!")
    argParser.add_argument("-t", "--host", help="telnet host", default="esp-easy.lan")
    argParser.add_argument("-p", "--port", help="telnet port", default="8088")
    args = argParser.parse_args()

    # telnet client loop
    loop = asyncio.get_event_loop()
    coro = telnetlib3.open_connection(args.host, args.port, shell=shell)
    reader, writer = loop.run_until_complete(coro)
    loop.run_until_complete(writer.protocol.waiter_closed)

if __name__ == "__main__":
    main()
