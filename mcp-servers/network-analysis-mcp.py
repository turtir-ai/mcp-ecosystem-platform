#!/usr/bin/env python3
"""
Network Analysis MCP Server
Real network analysis tools - ping, port scan, traceroute, DNS lookup
"""

import asyncio
import json
import sys
import socket
import subprocess
import platform
from typing import Any, Dict, List, Optional
import psutil

# MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types

# Create server instance
server = Server("network-analysis")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available network analysis tools."""
    return [
        Tool(
            name="get_network_interfaces",
            description="Get network interfaces information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_stats",
            description="Get network statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="ping_host",
            description="Ping a host and get latency information",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Host to ping (IP or domain)"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of ping packets",
                        "default": 4
                    }
                },
                "required": ["host"]
            }
        ),
        Tool(
            name="port_scan",
            description="Scan ports on a host",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Host to scan"
                    },
                    "ports": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of ports to scan"
                    }
                },
                "required": ["host", "ports"]
            }
        ),
        Tool(
            name="get_active_connections",
            description="Get active network connections",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="traceroute",
            description="Trace route to destination",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Destination host"
                    }
                },
                "required": ["host"]
            }
        ),
        Tool(
            name="dns_lookup",
            description="Perform DNS lookup",
            inputSchema={
                "type": "object",
                "properties": {
                    "hostname": {
                        "type": "string",
                        "description": "Hostname to resolve"
                    }
                },
                "required": ["hostname"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls."""
    
    if name == "get_network_interfaces":
        try:
            interfaces = []
            for interface_name, interface_addresses in psutil.net_if_addrs().items():
                interface_info = {
                    "name": interface_name,
                    "addresses": []
                }
                
                for address in interface_addresses:
                    addr_info = {
                        "family": str(address.family),
                        "address": address.address,
                        "netmask": address.netmask,
                        "broadcast": address.broadcast
                    }
                    interface_info["addresses"].append(addr_info)
                
                interfaces.append(interface_info)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(interfaces, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting network interfaces: {str(e)}"
            )]
    
    elif name == "get_network_stats":
        try:
            stats = psutil.net_io_counters()
            stats_dict = {
                "bytes_sent": stats.bytes_sent,
                "bytes_recv": stats.bytes_recv,
                "packets_sent": stats.packets_sent,
                "packets_recv": stats.packets_recv,
                "errin": stats.errin,
                "errout": stats.errout,
                "dropin": stats.dropin,
                "dropout": stats.dropout
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(stats_dict, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting network stats: {str(e)}"
            )]
    
    elif name == "ping_host":
        host = arguments.get("host")
        count = arguments.get("count", 4)
        
        try:
            # Platform-specific ping command
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", str(count), host]
            else:
                cmd = ["ping", "-c", str(count), host]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            return [types.TextContent(
                type="text",
                text=f"Ping results for {host}:\n{result.stdout}\n{result.stderr}"
            )]
        except subprocess.TimeoutExpired:
            return [types.TextContent(
                type="text",
                text=f"Ping to {host} timed out"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error pinging {host}: {str(e)}"
            )]
    
    elif name == "port_scan":
        host = arguments.get("host")
        ports = arguments.get("ports", [])
        
        results = []
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((host, port))
                sock.close()
                
                status = "open" if result == 0 else "closed"
                results.append(f"Port {port}: {status}")
            except Exception as e:
                results.append(f"Port {port}: error - {str(e)}")
        
        return [types.TextContent(
            type="text",
            text=f"Port scan results for {host}:\n" + "\n".join(results)
        )]
    
    elif name == "get_active_connections":
        try:
            connections = []
            for conn in psutil.net_connections():
                if conn.status == psutil.CONN_ESTABLISHED:
                    conn_info = {
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A",
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                        "status": conn.status,
                        "pid": conn.pid
                    }
                    connections.append(conn_info)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(connections, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting active connections: {str(e)}"
            )]
    
    elif name == "traceroute":
        host = arguments.get("host")
        
        try:
            # Platform-specific traceroute command
            if platform.system().lower() == "windows":
                cmd = ["tracert", host]
            else:
                cmd = ["traceroute", host]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return [types.TextContent(
                type="text",
                text=f"Traceroute to {host}:\n{result.stdout}\n{result.stderr}"
            )]
        except subprocess.TimeoutExpired:
            return [types.TextContent(
                type="text",
                text=f"Traceroute to {host} timed out"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error tracing route to {host}: {str(e)}"
            )]
    
    elif name == "dns_lookup":
        hostname = arguments.get("hostname")
        
        try:
            # Get IP address
            ip_address = socket.gethostbyname(hostname)
            
            # Try to get additional info
            try:
                host_info = socket.gethostbyaddr(ip_address)
                result = {
                    "hostname": hostname,
                    "ip_address": ip_address,
                    "canonical_name": host_info[0],
                    "aliases": host_info[1]
                }
            except:
                result = {
                    "hostname": hostname,
                    "ip_address": ip_address
                }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error resolving {hostname}: {str(e)}"
            )]
    
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    # Run the server using stdin/stdout streams
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="network-analysis",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())