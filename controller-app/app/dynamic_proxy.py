import asyncio
import struct
from .pool_manager import pool_manager

async def relay_data(reader, writer):
    try:
        while not reader.at_eof() and not writer.is_closing():
            data = await reader.read(4096)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        if not writer.is_closing():
            writer.close()
            await writer.wait_closed()

async def handle_client(client_reader, client_writer):
    try:
        # SOCKS5 handshake
        # 1. Client Greeting
        version, nmethods = await client_reader.readexactly(2)
        if version != 5:
            return
        methods = await client_reader.readexactly(nmethods)
        
        # 2. Server Choice (we support NO AUTHENTICATION REQUIRED)
        if 0 not in methods:
            return
        client_writer.write(b'\x05\x00')
        await client_writer.drain()

        # 3. Client Request
        version, cmd, rsv, atyp = await client_reader.readexactly(4)
        if version != 5 or cmd != 1: # CMD 1 is CONNECT
            # Send error reply
            client_writer.write(b'\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00')
            await client_writer.drain()
            return

        if atyp == 1: # IPv4
            addr = await client_reader.readexactly(4)
            dest_addr = ".".join(map(str, addr))
        elif atyp == 3: # Domain name
            domain_len = await client_reader.readexactly(1)
            dest_addr = (await client_reader.readexactly(domain_len[0])).decode()
        elif atyp == 4: # IPv6
            addr = await client_reader.readexactly(16)
            dest_addr = ":".join(f"{addr[i:i+2].hex()}" for i in range(0, 16, 2))
        else:
            return
        
        dest_port = struct.unpack('!H', await client_reader.readexactly(2))[0]

        # Get a healthy upstream proxy from PoolManager
        upstream_instance = pool_manager.get_healthy_instance()
        if not upstream_instance:
            print("SOCKS Proxy: No healthy upstream instance available.")
            # Send "Host unreachable"
            client_writer.write(b'\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00')
            await client_writer.drain()
            return

        upstream_status = upstream_instance.get_status()
        upstream_host = '127.0.0.1' # Assuming controller and warp run on same docker network
        upstream_port = upstream_status['socks5_port']
        
        print(f"SOCKS Proxy: Forwarding {dest_addr}:{dest_port} via {upstream_status['name']} ({upstream_host}:{upstream_port})")

        # Connect to the selected upstream WARP instance
        upstream_reader, upstream_writer = await asyncio.open_connection(upstream_host, upstream_port)
        
        # Send success reply to client
        client_writer.write(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
        await client_writer.drain()

        # Relay data
        await asyncio.gather(
            relay_data(client_reader, upstream_writer),
            relay_data(upstream_reader, client_writer)
        )

    except Exception as e:
        print(f"SOCKS Proxy Error: {e}")
    finally:
        if not client_writer.is_closing():
            client_writer.close()
            await client_writer.wait_closed()

async def start_proxy_server(host='0.0.0.0', port=10800):
    server = await asyncio.start_server(handle_client, host, port)
    addr = server.sockets[0].getsockname()
    print(f'Unified SOCKS5 Proxy listening on {addr}')
    async with server:
        await server.serve_forever()