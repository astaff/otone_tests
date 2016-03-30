#!/usr/bin/env python3

import asyncio

@asyncio.coroutine
def simulator(reader, writer):
  while True:
    data = yield from reader.read(100)
    print(data)
    ack_received = 'ok\r\n'.encode()
    ack_ready = '{"stat":0}\r\n'.encode()
    writer.write(ack_received)
    yield from writer.drain()
    writer.write(ack_ready)
    yield from writer.drain()

if __name__ == '__main__':
  the_loop = asyncio.get_event_loop()
  server = the_loop.run_until_complete(asyncio.start_server(simulator,'0.0.0.0',3333))
  the_loop.run_forever()