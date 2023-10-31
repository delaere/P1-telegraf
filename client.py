import argparse
import asyncio, telnetlib3
import decoder
import logger as log

logger = None

# the telnet client loop
async def shell(reader, writer):
    global logger
    previous = None
    while True:
        # read stream
        try:
            outp = await asyncio.wait_for(reader.read(1024), timeout=10.0)
        except asyncio.exceptions.TimeoutError:
            logger.log(log.LOG_DEBUG,"Telnet connection timeout.")
            exit(1)
        if not outp:
            # End of File
            logger.log(log.LOG_DEBUG,"Telnet connection: EOF.")
            exit(1)
        # display only the records passing deadband filter.
        rec = decoder.record(raw=outp,measurement="ORES")
        if not rec.valid():
            continue
        if previous is None or previous != rec :
            logger.log(log.LOG_DEBUG,str(rec))
            print(rec, flush=True)
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

    # the logger
    global logger
    logger = log.logger(False,True,False,"/etc/telegraf/log.txt",log.LOG_DEBUG)

    # telnet client loop
    logger.log(log.LOG_INFO,f"Initiating telnet connection to {args.host}:{args.port}")
    loop = asyncio.get_event_loop()
    coro = telnetlib3.open_connection(args.host, args.port, shell=shell)
    logger.log(log.LOG_INFO,f"Connected!")
    reader, writer = loop.run_until_complete(coro)
    loop.run_until_complete(writer.protocol.waiter_closed)

if __name__ == "__main__":
    main()
    exit(1)
