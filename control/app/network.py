# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#configuration | docs/PLATFORM.md
# The transport peer is authoritative unless its network was explicitly trusted.
import ipaddress
from fastapi import HTTPException


def address(value):
    if '%' in value:raise ValueError('Scoped addresses are not accepted')
    ip=ipaddress.ip_address(value)
    return ip.ipv4_mapped if isinstance(ip,ipaddress.IPv6Address) and ip.ipv4_mapped else ip


def forwarded_addresses(request):
    values=request.headers.getlist('x-forwarded-for')
    if not values:return []
    text=','.join(values)
    if len(text)>2048:return None
    parts=text.split(',')
    if len(parts)>16:return None
    try:return [address(part.strip()) for part in parts]
    except ValueError:return None


def client_address(request,trusted):
    try:peer=address(request.client.host if request.client else '')
    except ValueError:raise HTTPException(400,'Adresse du client indisponible.') from None
    def approved(ip):return any(ip in network for network in trusted)
    if not approved(peer):return str(peer)
    chain=forwarded_addresses(request)
    if not chain:raise HTTPException(400,'Chaîne de proxy absente ou invalide.')
    for hop in reversed(chain):
        if not approved(hop):return str(hop)
    return str(chain[0])
